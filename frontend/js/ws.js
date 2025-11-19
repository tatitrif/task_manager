// ws.js
import { WS_BASE_URL } from './config.js';
import { ensureAccessToken } from './auth.js';
import { handleWSMessage } from './tasks.js';
import { showNotification } from './ui.js';

let taskWebSocket = null;
let isConnecting = false; // Защищаем от параллельных подключений

/**
 * Инициализирует WebSocket-соединение для задач
 * Автоматически обновляет токен при истечении и переподключается
 */
export async function initWebSocket() {
    if (isConnecting) return; // Не запускать, если уже идёт подключение
    isConnecting = true;

    try {
        // Получаем актуальный токен (автоматически обновит, если нужно)
        const token = await ensureAccessToken();
        if (!token) {
            showNotification('Сессия истекла. Войдите снова.', 'error');
            isConnecting = false;
            return;
        }

        const url = `${WS_BASE_URL}/ws/tasks/?token=${token}`;

        // Закрываем старое соединение, если есть
        if (taskWebSocket) {
            taskWebSocket.close();
        }

        taskWebSocket = new WebSocket(url);

        taskWebSocket.onopen = () => {
            showNotification('WS подключен');
            console.info('WS подключен');
            isConnecting = false; // Подключение завершено
        };

        taskWebSocket.onmessage = event => {
            try {
                const data = JSON.parse(event.data);
                console.log('Получено сообщение от WebSocket задач:', data);

                if (data.type === 'task_updated') {
                    handleWSMessage(data);
                }
                if (data.type === 'task_notify') {
                    showNotification(data.message);
                }
            } catch (error) {
                console.error('Ошибка при обработке уведомления WebSocket:', error);
            }
        };

        taskWebSocket.onclose = e => {
            console.warn('WebSocket закрыт, код:', e.code);

            if (e.code === 1006 || e.code === 4001) {
                showNotification('Сессия истекла, войдите снова', 'error');
            }

            // Переподключаемся через 3 секунды — даже если токен обновился
            setTimeout(initWebSocket, 3000);
        };

        taskWebSocket.onerror = e => {
            console.error('WS Error', e);
            // Переподключаемся на ошибке
            setTimeout(initWebSocket, 3000);
        };
    } catch (e) {
        console.error('Ошибка при инициализации WebSocket:', e);
        showNotification('Ошибка подключения к WebSocket', 'error');
        isConnecting = false;
    }
}
