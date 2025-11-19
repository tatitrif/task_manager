// tasks.js
// Управление задачами

import { API_BASE_URL, PAGE_LIMIT } from './config.js';
import { showNotification } from './ui.js';
import { apiFetch } from './auth.js';

// --- Глобальное состояние ---
const TaskState = {
    currentLimit: PAGE_LIMIT,
    currentOffset: 0,
    nextPage: null,
    prevPage: null,
    currentTasks: [],
    isLoading: false,
};

// --- DOM-элементы ---
const tasksBody = document.getElementById('tasksTableBody');

/**
 * Создаёт строку задачи для таблицы
 * @param {object} task - объект задачи
 * @returns {HTMLTableRowElement} - элемент строки таблицы
 */
function createTaskRow(task) {
    const row = document.createElement('tr');
    row.className = 'task-item';
    row.dataset.taskId = task.id;

    const formatDate = task.complete_before
        ? new Date(task.complete_before).toLocaleString('ru-RU')
        : '—';

    row.innerHTML = `
        <td>${task.id}</td>
        <td>${task.name || 'Без названия'}</td>
        <td>${task.description || ''}</td>
        <td>${task.list_name || 'Без списка'}</td>
        <td>${task.assignee_name || 'Не назначен'}</td>
        <td>${formatDate}</td>
        <td>${task.status || 'Unknown'}</td>
        <td>${task.status === 'In Progress' ? '<button class="success">Выполнить</button>' : '—'}</td>
    `;

    return row;
}

/**
 * Добавляет задачу в DOM (в начало или конец)
 * @param {object} task - объект задачи
 * @param {'prepend'|'append'} position - куда добавлять
 */
function addTaskToDOM(task, position = 'append') {
    if (!tasksBody || tasksBody.querySelector(`[data-task-id="${task.id}"]`)) return;

    const row = createTaskRow(task);

    if (position === 'prepend') {
        tasksBody.prepend(row);
    } else {
        tasksBody.appendChild(row);
    }
}

/**
 * Добавляет несколько задач в конец таблицы
 * @param {object[]} tasks - массив задач
 */
export function appendTasks(tasks) {
    if (!Array.isArray(tasks)) return;

    const fragment = document.createDocumentFragment();

    tasks.forEach(task => {
        if (!tasksBody.querySelector(`[data-task-id="${task.id}"]`)) {
            fragment.appendChild(createTaskRow(task));
        }
    });

    if (fragment.children.length > 0) {
        tasksBody.appendChild(fragment);
    }
}

/**
 * Добавляет задачу в начало списка (например, при создании)
 * @param {object} task - объект задачи
 */
function prependTask(task) {
    addTaskToDOM(task, 'prepend');
}

/**
 * Обновляет задачу в DOM (заменяет строку)
 * @param {object} task - объект задачи
 */
export function updateTaskInDOM(task) {
    const existing = tasksBody?.querySelector(`[data-task-id="${task.id}"]`);
    const row = createTaskRow(task);

    if (existing) {
        existing.replaceWith(row);
    } else {
        tasksBody?.appendChild(row);
    }
}

/**
 * Удаляет задачу из DOM
 * @param {object} task - объект задачи
 */
export function removeTaskFromDOM(task) {
    const existing = tasksBody?.querySelector(`[data-task-id="${task.id}"]`);
    if (existing) existing.remove();
}

/**
 * Отмечает задачу как выполненную
 * @param {number} taskId - ID задачи
 */
export async function completeTask(taskId) {
    try {
        await apiFetch(`${API_BASE_URL}/tasks/${taskId}/complete/`, { method: 'POST' });
        showNotification('Задача выполнена!', 'success');
    } catch (e) {
        console.error('Complete task error:', e);
        showNotification('Ошибка при выполнении задачи', 'error');
    }
}

/**
 * Загружает страницу задач с сервера
 * @param {number} offset - смещение для пагинации
 */
export async function fetchTasksPage(offset = TaskState.currentOffset) {
    if (TaskState.isLoading) return;

    TaskState.isLoading = true;

    try {
        const url = `${API_BASE_URL}/tasks/?limit=${TaskState.currentLimit}&offset=${offset}`;
        const res = await apiFetch(url);
        const data = await res.json();

        if (!Array.isArray(data.results)) {
            console.warn('Invalid response structure', data);
            return;
        }

        TaskState.nextPage = data.next;
        TaskState.prevPage = data.previous;
        TaskState.currentTasks = TaskState.currentTasks.concat(data.results);

        appendTasks(data.results);
    } catch (e) {
        console.error('Ошибка загрузки', e);
        showNotification('Ошибка загрузки задач', 'error');
    } finally {
        TaskState.isLoading = false;
    }
}

/**
 * Загружает начальные задачи (очищает таблицу и загружает первую страницу)
 */
export async function loadInitialTasks() {
    if (tasksBody) tasksBody.innerHTML = '';
    return await fetchTasksPage(TaskState.currentOffset);
}

/**
 * Обрабатывает сообщение WebSocket
 * @param {object} data - сообщение от WebSocket
 */
export function handleWSMessage(data) {
    if (!data || !data.action) return;

    switch (data.action) {
        case 'created':
            prependTask(data.task);
            break;
        case 'updated':
            updateTaskInDOM(data.task);
            break;
        case 'deleted':
            removeTaskFromDOM(data.task);
            break;
        default:
            break;
    }
}

// --- Бесконечная прокрутка ---
let scrollHandler = null;

function debouncedScroll() {
    if (scrollHandler) clearTimeout(scrollHandler);
    scrollHandler = setTimeout(() => {
        if (TaskState.isLoading || !TaskState.nextPage) return;

        const url = new URL(TaskState.nextPage);
        const offset = parseInt(url.searchParams.get('offset') || 0);
        if (isNaN(offset)) return;

        TaskState.currentOffset = offset;
        fetchTasksPage(TaskState.currentOffset);
    }, 100);
}

window.addEventListener('scroll', debouncedScroll);
