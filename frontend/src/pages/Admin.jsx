import { useState, useEffect } from 'react';
import { ChartNoAxesColumnIncreasing } from 'lucide-react';
import { errorMessage } from '../config/api';
import { analyticsApi } from '../services/market';

export function Admin() {
    const [period, setPeriod] = useState('monthly');
    const [stats, setStats] = useState(null);
    const [error, setError] = useState('');
    const [busy, setBusy] = useState(false);

    const load = () => {
        setBusy(true);
        analyticsApi
            .stats(period)
            .then(setStats)
            .catch(e => setError(errorMessage(e)))
            .finally(() => setBusy(false));
    };

    useEffect(() => {
        load();
    }, [period]);

    return (
        <main className="page-shell">
            <div className="eyebrow">ПАНЕЛЬ УПРАВЛЕНИЯ</div>
            <h1 className="page-heading">Аналитика <em>магазина.</em></h1>
            <div className="admin-toolbar">
                <span>Период отчёта</span>
                <select value={period} onChange={e => setPeriod(e.target.value)}>
                    <option value="daily">Сегодня</option>
                    <option value="weekly">Неделя</option>
                    <option value="monthly">Месяц</option>
                    <option value="yearly">Год</option>
                    <option value="all">Всё время</option>
                </select>
            </div>
            {busy ? (
                <p>Загружаем аналитику…</p>
            ) : error ? (
                <div className="error-panel">
                    <p>Аналитика доступна только пользователям с правами администратора.</p>
                    <small>{error}</small>
                </div>
            ) : stats ? (
                <div className="stats-grid">
                    {Object.entries(stats).map(([key, value]) => (
                        <div className="stat-card" key={key}>
                            <span>{key.replaceAll('_', ' ')}</span>
                            <strong>
                                {typeof value === 'number'
                                    ? new Intl.NumberFormat('ru-RU').format(value)
                                    : String(value)}
                            </strong>
                            <ChartNoAxesColumnIncreasing />
                        </div>
                    ))}
                </div>
            ) : null}
        </main>
    );
}

export default Admin;