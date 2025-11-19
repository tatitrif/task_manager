// main.js — bootstrap and event wiring
import { showNotification, showView } from './ui.js';
import { ensureAccessToken, login, logout, register } from './auth.js';
import { completeTask, loadInitialTasks } from './tasks.js';
import { initWebSocket } from './ws.js';
import { ACCESS_KEY } from './config.js';

// DOM refs
const loginBtn = document.getElementById('loginBtn');
const toRegisterBtn = document.getElementById('toRegisterBtn');
const toLoginBtn = document.getElementById('toLoginBtn');
const registerBtn = document.getElementById('registerBtn');
const logoutBtn = document.getElementById('logoutBtn');
const tasksBody = document.getElementById('tasksTableBody');

async function boot() {
    // initial view selection
    const token = localStorage.getItem(ACCESS_KEY);
    if (token) {
        try {
            await ensureAccessToken();
            await loadInitialTasks();
            showView('appView');
            await initWebSocket();
        } catch (e) {
            console.warn('boot failed, show login', e);
            showView('loginView');
        }
    } else {
        showView('loginView');
    }
}

loginBtn?.addEventListener('click', async () => {
    const u = document.getElementById('loginUsername').value.trim();
    const p = document.getElementById('loginPassword').value;
    try {
        await login(u, p);
        // load tasks & connect ws
        await loadInitialTasks();
        await initWebSocket();
        showView('appView');
    } catch (e) {
        console.error(e);
        showNotification('Неверные данные', 'error');
    }
});

toRegisterBtn?.addEventListener('click', () => showView('registerView'));
toLoginBtn?.addEventListener('click', () => showView('loginView'));

registerBtn?.addEventListener('click', async () => {
    const u = document.getElementById('regUsername').value.trim();
    const e = document.getElementById('regEmail').value.trim();
    const p = document.getElementById('regPassword').value;
    const c = document.getElementById('regPasswordConfirm').value;
    if (p !== c) {
        showNotification('Пароли не совпадают', 'error');
        return;
    }
    try {
        await register(u, e, p, c);
        showNotification('Регистрация прошла успешно', 'success');
        showView('loginView');
    } catch (err) {
        console.error(err);
        showNotification(err.message || 'Ошибка регистрации', 'error');
    }
});
// Делегирование событий для кнопок задач

logoutBtn?.addEventListener('click', () => {
    logout();
    showView('loginView');
});

tasksBody?.addEventListener('click', e => {
    if (e.target.classList.contains('success')) {
        const taskId = e.target.closest('tr')?.dataset.taskId;
        if (taskId) completeTask(taskId);
    }
});

// boot app
boot();
