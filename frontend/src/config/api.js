
import axios from 'axios';

export const api = axios.create({
    baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
    headers: { 'Content-Type': 'application/json' }
});

api.interceptors.request.use(config => {
    const token = localStorage.getItem('market_access');
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
});

// Бэкенд ожидает refresh-токен как JSON-строку в теле (Body(str)),
// поэтому отправляем JSON.stringify(token), а не объект.
let refreshRequest = null;

async function refreshTokens() {
    const refresh = localStorage.getItem('market_refresh');
    if (!refresh) throw new Error('Нет refresh токена');

    const { data } = await axios.post(
        `${api.defaults.baseURL}/auth/token/refresh`,
        JSON.stringify(refresh),
        { headers: { 'Content-Type': 'application/json' } }
    );

    const access = data.access || data.access_token;
    const nextRefresh = data.refresh || data.refresh_token;
    if (!access) throw new Error('Сервер не вернул access токен');

    localStorage.setItem('market_access', access);
    if (nextRefresh) localStorage.setItem('market_refresh', nextRefresh);
    return access;
}

api.interceptors.response.use(
    r => r,
    async error => {
        const original = error.config;
        const canRetry =
            error.response?.status === 401 &&
            original &&
            !original._retry &&
            !original.url?.includes('/auth/token') &&
            localStorage.getItem('market_refresh');

        if (canRetry) {
            original._retry = true;
            try {
                // Single-flight: параллельные 401 используют один запрос refresh,
                // иначе ротация refresh-токена разлогинит пользователя.
                refreshRequest = refreshRequest || refreshTokens().finally(() => { refreshRequest = null; });
                const access = await refreshRequest;
                original.headers = original.headers || {};
                original.headers.Authorization = `Bearer ${access}`;
                return api(original);
            } catch {
                localStorage.removeItem('market_access');
                localStorage.removeItem('market_refresh');
                window.dispatchEvent(new Event('market:session-expired'));
            }
        }
        return Promise.reject(error);
    }
);

export function errorMessage(error) {
    const detail = error?.response?.data?.detail;
    if (typeof detail === 'string' && detail) return detail;
    if (Array.isArray(detail)) {
        const messages = detail.map(item => item?.msg || item?.message).filter(Boolean);
        if (messages.length) return messages.join('; ');
    }
    if (detail && typeof detail === 'object') {
        return detail.msg || detail.message || 'Некорректные данные запроса';
    }
    const message = error?.response?.data?.message;
    if (typeof message === 'string' && message) return message;
    if (error?.code === 'ERR_NETWORK') return 'Сервер недоступен. Проверьте подключение к сети.';
    return error?.message || 'Что-то пошло не так';
}
