// ui.js

export const VIEWS = ['loadingView', 'loginView', 'registerView', 'appView'];

// Показ уведомления
export function showNotification(message, type = 'success') {
    const container = document.getElementById('notificationContainer');

    const notification = document.createElement('div');
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

export function showView(name) {
    VIEWS.forEach(v => {
        const el = document.getElementById(v);
        if (el) {
            el.classList.toggle('hidden', v !== name);
        }
    });
}
