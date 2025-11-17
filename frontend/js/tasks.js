//tasks.js
// Загрузка, отображение и обновление задач

// Загрузка списков задач и задач
let currentTasks = [];

// --- Получение и отображение начального списка
async function fetchAndRenderTasks() {
  try {
    const response = await apiRequest(`${API_BASE_URL}/tasks/`);
    if (!response.ok) {
      console.error("Ошибка при загрузке списков задач:", response.status);
      showNotification("Ошибка при загрузке данных", "error");
    }
    const data = await response.json();
    currentTasks = data.results;
    renderTasks(currentTasks);
    console.info("fetchAndRenderTasks:", currentTasks);
  } catch (error) {
    console.error("Ошибка при загрузке списков задач:", error);
    showNotification("Ошибка при загрузке данных", "error");
  }
}

// --- Отрисовка списка задач ---
function renderTasks(tasks) {
  const container = document.getElementById("tasksTableBody");
  if (!container) {
    console.error("Контейнер задач не найден");
    return;
  }

  container.innerHTML = ""; // Очистить текущий список

  tasks.forEach((task, index) => {
    const taskElement = createTaskElement(task);
    container.appendChild(taskElement);
  });
}

// --- Создание DOM-элемента задачи ---
function createTaskElement(task) {
  const row = document.createElement("tr");
  row.className = "task-item";
  row.dataset.taskId = task.id;
  row.dataset.index = -1;

  // Форматируем дату
  let formattedDate = "Не указан";
  if (task.complete_before) {
    const date = new Date(task.complete_before);
    formattedDate = date.toLocaleString("ru-RU", {
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
    });
  }

  // Создаём поле Выполнить
  let completeField;
  if (task.status === "In Progress") {
    const completeButton = document.createElement("button");
    completeButton.textContent = "Выполнить";
    completeButton.className = "complete-btn";
    completeButton.onclick = () => completeTask(task.id);
    completeField = completeButton;
  } else {
    const span = document.createElement("span");
    span.textContent = "—";
    completeField = span;
  }

  // Создаём ячейки таблицы
  const idCell = document.createElement("td");
  idCell.textContent = task.id;

  const nameCell = document.createElement("td");
  nameCell.textContent = task.name;

  const descriptionCell = document.createElement("td");
  descriptionCell.textContent = task.description || "";

  const listNameCell = document.createElement("td");
  listNameCell.textContent = task.list_name;

  const assigneeNameCell = document.createElement("td");
  assigneeNameCell.textContent = task.assignee_name || "Не назначен";

  const dateCell = document.createElement("td");
  dateCell.textContent = formattedDate;

  const statusCell = document.createElement("td");
  statusCell.textContent = task.status;

  const actionCell = document.createElement("td");
  actionCell.appendChild(completeField);

  // Добавляем ячейки в строку
  row.appendChild(idCell);
  row.appendChild(nameCell);
  row.appendChild(descriptionCell);
  row.appendChild(listNameCell);
  row.appendChild(assigneeNameCell);
  row.appendChild(dateCell);
  row.appendChild(statusCell);
  row.appendChild(actionCell);

  return row;
}

// --- Обновление задачи в DOM ---
function updateTaskInDOM(action, taskData) {
  const container = document.getElementById("tasksTableBody");
  const existingElement = document.querySelector(
    `[data-task-id="${taskData.id}"]`,
  );

  if (action === "deleted") {
    if (existingElement) {
      existingElement.remove();
      currentTasks = currentTasks.filter((t) => t.id !== taskData.id);
    }
    return;
  }

  if (action === "created") {
    if (!existingElement) {
      const newElement = createTaskElement(taskData);
      container.appendChild(newElement);
      currentTasks.push(taskData);
    }
  } else if (action === "updated") {
    if (existingElement) {
      // Заменяем старый элемент на новый (с обновлёнными данными)
      const newElement = createTaskElement(taskData);
      existingElement.replaceWith(newElement);
      // Обновляем в локальном массиве
      const index = currentTasks.findIndex((t) => t.id === taskData.id);
      if (index !== -1) {
        currentTasks[index] = taskData;
      }
    } else {
      // Если элемента не было, но пришло "updated" — добавляем
      const newElement = createTaskElement(taskData);
      container.appendChild(newElement);
      currentTasks.push(taskData);
    }
  }

  // Пересчитываем индексы (если нужно для других целей)
  recalculateIndices();
}

// --- Пересчёт индексов задач в DOM ---
function recalculateIndices() {
  const container = document.getElementById("tasksTableBody");
  const taskElements = container.querySelectorAll(".task-item");
  taskElements.forEach((el, index) => {
    el.dataset.index = index;
  });
}

// --- completeTask задачи   ---
async function completeTask(taskId) {
  try {
    const response = await apiRequest(
      `${API_BASE_URL}/tasks/${taskId}/complete/`,
      {
        method: "POST",
      },
    );
    if (!response.ok) {
      showNotification("Ошибка при выполнении задачи", "error");
    }
    if (response.ok) {
      showNotification("Задача выполнена!", "success");
      // Ожидаем, что сервер отправит через WebSocket: {"type": "task_updated", "action": "complete", "task": {"id": taskId, ...}}
    }
  } catch (error) {
    console.error("Ошибка при complete задачи:", error);
  }
}

// Экспортируем функции для использования в других модулях
if (typeof module !== "undefined" && module.exports) {
  module.exports = {
    fetchAndRenderTasks,
    renderTasks,
    createTaskElement,
    updateTaskInDOM,
    recalculateIndices,
    completeTask,
  };
}
