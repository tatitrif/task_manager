// ws.js
// Инициализация и управление WebSocket соединением

let taskWebSocket = null;

// Инициализация WebSocket соединений
async function initWebSocket() {
  const { accessToken, refreshToken } = getTokens();

  if (!accessToken && refreshToken) {
    console.log("Access токен отсутствует, пробуем обновить...");
    const tokenRefreshed = await refreshAccessToken();
    if (!tokenRefreshed) {
      console.error("Не удалось обновить токен");
      return;
    }
  } else if (!accessToken && !refreshToken) {
    console.error("Токены отсутствуют, невозможно подключиться к WebSocket");
    return;
  }

  const { accessToken: finalAccessToken } = getTokens();

  // Закрываем старое соединение, если оно есть
  if (taskWebSocket) {
    taskWebSocket.close();
  }

  const taskWsUrl = `${WS_BASE_URL}/ws/tasks/?token=${encodeURIComponent(
    finalAccessToken,
  )}`;
  taskWebSocket = new WebSocket(taskWsUrl);

  taskWebSocket.onopen = () => {
    console.log("WebSocket открыт.");
  };

  taskWebSocket.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      console.log("Получено сообщение от WebSocket задач:", data);

      if (data.type === "task_updated") {
        updateTaskInDOM(data.action, data.task);
      }
      if (data.type === "task_notify") {
        showNotification(data.message);
      }
    } catch (error) {
      console.error("Ошибка при обработке уведомления WebSocket:", error);
    }
  };

  taskWebSocket.onclose = async function (event) {
    console.log("WebSocket закрыт:", event.code, event.reason);
    if (event.code === 4001) {
      console.log("Токен истёк, пробуем обновить и переподключиться...");
      const tokenRefreshed = await refreshAccessToken();
      if (tokenRefreshed) {
        console.log("Токен обновлён, пробуем переподключиться...");
        setTimeout(initWebSocket, 1000);
      } else {
        console.error(
          "Не удалось обновить токен после закрытия WebSocket с кодом 4001",
        );
        showNotification("Сессия истекла, пожалуйста, авторизуйтесь снова.");
        window.location.href = "../html/login.html";
      }
    } else {
      console.log("WebSocket задач закрыт, пробуем переподключиться...");
      setTimeout(initWebSocket, 5000);
    }
    taskWebSocket = null; // Сбрасываем переменную при закрытии
  };

  taskWebSocket.onerror = function (error) {
    console.error("Ошибка WebSocket задач:", error);
  };
}

// Отправка сообщения через WebSocket задач
function sendTaskMessage(message) {
  if (taskWebSocket && taskWebSocket.readyState === WebSocket.OPEN) {
    taskWebSocket.send(JSON.stringify(message));
  } else {
    console.warn("WebSocket задач недоступен для отправки сообщения");
  }
}

// Закрытие WebSocket соединений
function closeWebSocketConnections() {
  if (taskWebSocket) {
    taskWebSocket.close();
  }
}

// Экспортируем функции для использования в других модулях
if (typeof module !== "undefined" && module.exports) {
  module.exports = {
    initWebSocket,
    sendTaskMessage,
    closeWebSocketConnections,
  };
}
