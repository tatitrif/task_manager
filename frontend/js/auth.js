// auth.js
// Управление токенами, логин/регистрация, обновление токенов, обёртка apiFetch

import {
    ACCESS_EXP_KEY,
    ACCESS_KEY,
    API_BASE_URL,
    DEFAULT_TIMEOUT,
    REFRESH_KEY,
} from './config.js';
import { showNotification } from './ui.js';

// --- Вспомогательные функции ---

/**
 * Выполняет fetch с таймаутом
 * @param {string} url - URL запроса
 * @param {object} options - параметры fetch
 * @returns {Promise<Response>} - ответ от сервера
 */
async function fetchWithTimeout(url, options = {}) {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), DEFAULT_TIMEOUT);

    try {
        const res = await fetch(url, {
            ...options,
            signal: controller.signal,
        });
        clearTimeout(timeoutId);
        return res;
    } catch (e) {
        clearTimeout(timeoutId);
        if (e.name === 'AbortError') {
            throw new Error('Request timeout');
        }
        throw e;
    }
}

/**
 * Форматирует ошибки из API в строку
 * @param {object|string} data - объект ошибки от сервера
 * @returns {string} - строка с ошибками
 */
function formatError(data) {
    if (typeof data === 'string') return data;
    if (data.detail) return data.detail;
    if (data.message) return data.message;

    // Обработка ошибок вида: { field: ["error1", "error2"] }
    const errors = Object.values(data).flat();
    return errors.join(', ') || 'Request failed';
}

// --- Работа с токенами ---

/**
 * Получить access токен из localStorage
 * @returns {string|null} - токен или null
 */
export function getAccessToken() {
    return localStorage.getItem(ACCESS_KEY);
}

/**
 * Получить refresh токен из localStorage
 * @returns {string|null} - токен или null
 */
export function getRefreshToken() {
    return localStorage.getItem(REFRESH_KEY);
}

/**
 * Очистить все токены из localStorage
 */
export function clearTokens() {
    localStorage.removeItem(ACCESS_KEY);
    localStorage.removeItem(REFRESH_KEY);
    localStorage.removeItem(ACCESS_EXP_KEY);
}

/**
 * Сохранить токены и время их жизни
 * @param {string} access - access токен
 * @param {string} refresh - refresh токен
 * @param {number} access_expires_in - время жизни access токена в секундах
 */
export function saveTokens(access, refresh, access_expires_in) {
    localStorage.setItem(ACCESS_KEY, access);
    localStorage.setItem(REFRESH_KEY, refresh);
    if (access_expires_in) {
        localStorage.setItem(ACCESS_EXP_KEY, String(Date.now() + access_expires_in * 1000));
    } else {
        localStorage.removeItem(ACCESS_EXP_KEY);
    }
}

/**
 * Проверить, действителен ли access токен (с запасом 10 секунд)
 * @returns {boolean} - true, если токен действителен
 */
export function isAccessTokenValid() {
    const exp = localStorage.getItem(ACCESS_EXP_KEY);
    if (!exp) return !!getAccessToken();
    return Date.now() < Number(exp) - 10000;
}

// Предотвращает параллельные попытки обновления токена
let refreshPromise = null;

/**
 * Обновить access токен с помощью refresh токена
 * @returns {Promise<string|null>} - новый access токен или null
 */
export async function refreshAccessToken() {
    if (refreshPromise) return refreshPromise;
    const refresh = getRefreshToken();
    if (!refresh) return null;

    refreshPromise = (async () => {
        try {
            const res = await fetchWithTimeout(`${API_BASE_URL}/auth/token/refresh/`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ refresh }),
            });

            if (!res.ok) {
                clearTokens();
                return null;
            }
            const data = await res.json();
            saveTokens(data.access, refresh, data.access_expires_in);
            return data.access;
        } catch (e) {
            console.error('refresh error', e);
            clearTokens();
            return null;
        } finally {
            refreshPromise = null;
        }
    })();

    return refreshPromise;
}

/**
 * Убедиться, что токен действителен, и вернуть его
 * @returns {Promise<string|null>} - действительный токен или null
 */
export async function ensureAccessToken() {
    if (isAccessTokenValid()) return getAccessToken();
    const refreshed = await refreshAccessToken();
    if (refreshed) return refreshed;
    clearTokens();
    return null;
}

/**
 * Обёртка для fetch, которая:
 * - добавляет токен в заголовки
 * - автоматически обновляет токен при 401/403
 * - добавляет Content-Type, если не FormData
 * @param {string} url - URL запроса
 * @param {object} options - параметры fetch
 * @param {boolean} retry - нужно ли повторить запрос при 401
 * @returns {Promise<Response>} - ответ от сервера
 */
export async function apiFetch(url, options = {}, retry = true) {
    const access = await ensureAccessToken();
    if (!options.headers) options.headers = {};

    if (access) {
        options.headers['Authorization'] = `Bearer ${access}`;
    }

    // Не добавлять Content-Type, если FormData
    if (!options.headers['Content-Type'] && !(options.body instanceof FormData)) {
        options.headers['Content-Type'] = 'application/json';
    }

    const res = await fetchWithTimeout(url, options);

    if ((res.status === 401 || res.status === 403) && retry) {
        const refreshed = await refreshAccessToken();
        if (refreshed) return apiFetch(url, options, false);
        clearTokens();
        showNotification('Сессия истекла. Войдите снова.', 'error');
        throw new Error('Unauthorized');
    }

    return res;
}

// ---- Функции аутентификации ----

/**
 * Вход пользователя
 * @param {string} username - имя пользователя
 * @param {string} password - пароль
 * @returns {Promise<object>} - токены и время жизни
 */
export async function login(username, password) {
    if (!username || !password) {
        throw new Error('Username and password are required');
    }

    const res = await fetchWithTimeout(`${API_BASE_URL}/auth/token/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password }),
    });

    if (!res.ok) {
        const errorData = await res.json().catch(() => ({ detail: 'Login failed' }));
        throw new Error(formatError(errorData));
    }

    const data = await res.json();
    saveTokens(data.access, data.refresh, data.access_expires_in);
    return data;
}

/**
 * Регистрация пользователя
 * @param {string} username - имя пользователя
 * @param {string} email - email
 * @param {string} password - пароль
 * @param {string} confirm_password - подтверждение пароля
 * @returns {Promise<object>} - данные пользователя
 */
export async function register(username, email, password, confirm_password) {
    if (!username || !password || !confirm_password) {
        throw new Error('Username, password and confirmation are required');
    }

    const res = await fetchWithTimeout(`${API_BASE_URL}/auth/register/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, email, password, confirm_password }),
    });

    if (!res.ok) {
        const errorData = await res.json().catch(() => ({ detail: 'Registration failed' }));
        throw new Error(formatError(errorData));
    }

    return await res.json();
}

/**
 * Выход пользователя (опционально отзывает refresh токен на сервере)
 */
export async function logout() {
    const refresh = getRefreshToken();
    if (refresh) {
        try {
            await fetchWithTimeout(`${API_BASE_URL}/auth/token/blacklist/`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ refresh }),
            });
        } catch (e) {
            console.warn('Failed to blacklist refresh token:', e);
        }
    }
    clearTokens();
}
