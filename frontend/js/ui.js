// ui.js

// Показ уведомления
function showNotification(message, type = "success") {
  const container = document.getElementById("notificationContainer");

  const notification = document.createElement("div");
  notification.className = `notification ${type}`;
  notification.textContent = message;

  // Добавляем уведомление в контейнер
  container.appendChild(notification);

  // Автоматически удаляем уведомление через 5 секунды
  setTimeout(() => {
    if (notification.parentNode) {
      notification.parentNode.removeChild(notification);
    }
  }, 5000);
}

// Экспортируем функции для использования в других модулях
if (typeof module !== "undefined" && module.exports) {
  module.exports = {
    showNotification,
  };
}
