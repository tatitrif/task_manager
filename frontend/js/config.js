// config.js
// Определяем конфигурацию API и WebSocket

const HOST = "127.0.0.1:8000";
const API_BASE_URL = `http://${HOST}/api`;
const WS_BASE_URL =
  window.location.protocol === "https:" ? `wss://${HOST}` : `ws://${HOST}`;

// Экспортируем функции для использования в других модулях
if (typeof module !== "undefined" && module.exports) {
  module.exports = {
    API_BASE_URL,
    WS_BASE_URL,
  };
}
