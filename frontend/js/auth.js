// auth.js
// Функции аутентификации, регистрации, обновления токенов и т.д.

// Получение токенов из localStorage
function getTokens() {
  const accessToken = localStorage.getItem("access_token");
  const refreshToken = localStorage.getItem("refresh_token");
  return { accessToken, refreshToken };
}

// Сохранение токенов в localStorage
function saveTokens(accessToken, refreshToken) {
  localStorage.setItem("access_token", accessToken);
  localStorage.setItem("refresh_token", refreshToken);
}

// Удаление токенов из localStorage
function removeTokens() {
  localStorage.removeItem("access_token");
  localStorage.removeItem("refresh_token");
}

// Обновление access токена
async function refreshAccessToken() {
  const { refreshToken } = getTokens();
  if (!refreshToken) {
    return false;
  }

  try {
    const response = await fetch(`${API_BASE_URL}/auth/token/refresh/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh: refreshToken }),
    });

    if (response.ok) {
      const data = await response.json();
      saveTokens(data.access, refreshToken);
      return true;
    } else {
      // Если не удалось обновить токен, удаляем старые токены
      removeTokens();
      return false;
    }
  } catch (error) {
    console.error("Ошибка при обновлении токена:", error);
    removeTokens();
    return false;
  }
}

// Выполнение запроса с автоматическим обновлением токена
async function apiRequest(url, options = {}) {
  let { accessToken } = getTokens();

  const makeRequest = (token) => {
    const headers = {
      "Content-Type": "application/json",
      ...options.headers,
    };

    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }

    return fetch(url, { ...options, headers });
  };

  let response = await makeRequest(accessToken);

  if (response.status === 401 || response.status === 403) {
    const tokenRefreshed = await refreshAccessToken();
    if (tokenRefreshed) {
      const { accessToken: newAccessToken } = getTokens();
      response = await makeRequest(newAccessToken); // Повторяем с новым токеном
    }
  }

  return response;
}

// Аутентификация пользователя
async function authenticateUser(username, password) {
  try {
    const response = await fetch(`${API_BASE_URL}/auth/token/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password }),
    });

    if (response.ok) {
      const data = await response.json();
      saveTokens(data.access, data.refresh);
      return true;
    } else {
      return false;
    }
  } catch (error) {
    console.error("Ошибка при аутентификации:", error);
    throw error;
  }
}

// Регистрация пользователя
async function registerUser(username, email, password, confirm_password) {
  try {
    const response = await fetch(`${API_BASE_URL}/auth/register/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        username,
        email: email || "", // email может быть пустым
        password,
        confirm_password,
      }),
    });

    const data = await response.json();

    if (response.ok) {
      return { success: true, message: data.message };
    } else {
      return {
        success: false,
        message:
          data.message ||
          data.detail ||
          data.error ||
          Object.values(data).flat().join(", ") ||
          "Ошибка регистрации",
      };
    }
  } catch (error) {
    console.error("Ошибка при регистрации:", error);
    return {
      success: false,
      message: "Ошибка регистрации: не удалось подключиться к серверу",
    };
  }
}

// Выход из системы
async function logout() {
  const { refreshToken } = getTokens();

  if (refreshToken) {
    try {
      const response = await apiRequest(`${API_BASE_URL}/auth/logout/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ refresh_token: refreshToken }),
      });
      if (!response.ok) {
        console.warn("Logout request failed, but clearing tokens anyway");
      }
    } catch (error) {
      console.error("Ошибка при выходе:", error);
    }
  }
  removeTokens();
}

// Проверка аутентификации
async function checkAuth() {
  const { accessToken, refreshToken } = getTokens();
  return !!(refreshToken || accessToken);
}

// Проверка наличия токенов и редирект
async function checkTokensAndRedirect() {
  const isAuthenticated = await checkAuth();
  if (!isAuthenticated) {
    window.location.href = "../html/login.html";
  }
}

// Экспортируем функции для использования в других модулях
if (typeof module !== "undefined" && module.exports) {
  module.exports = {
    getTokens,
    saveTokens,
    removeTokens,
    refreshAccessToken,
    apiRequest,
    authenticateUser,
    registerUser,
    logout,
    checkAuth,
    checkTokensAndRedirect,
  };
}
