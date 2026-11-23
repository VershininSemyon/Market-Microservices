
import { useState, useEffect } from 'react';
import { TrendingUp, TrendingDown, CalendarRange } from 'lucide-react';
import { errorMessage } from '../config/api';
import { analyticsApi } from '../services/market';

const PERIODS = [
    ['daily', 'Сегодня'],
    ['weekly', 'Неделя'],
    ['monthly', 'Месяц'],
    ['yearly', 'Год'],
    ['all', 'Всё время']
];

const ENTITIES = [
    ['user', 'Пользователи', 'tone-user'],
    ['product', 'Товары', 'tone-product'],
    ['review', 'Отзывы', 'tone-review'],
    ['order', 'Заказы', 'tone-order']
];

const fmt = n => new Intl.NumberFormat('ru-RU').format(Number(n) || 0);

export function Admin() {
    const [period, setPeriod] = useState('monthly');
    const [stats, setStats] = useState(null);
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(true);
    const [reloadKey, setReloadKey] = useState(0);

    useEffect(() => {
        let alive = true;
        setLoading(true);
        setError('');
        analyticsApi
            .stats(period)
            .then(data => alive && setStats(data))
            .catch(e => alive && setError(errorMessage(e)))
            .finally(() => alive && setLoading(false));
        return () => {
            alive = false;
        };
    }, [period, reloadKey]);

    const periodLabel = PERIODS.find(([value]) => value === period)?.[1] || period;
    const distribution = stats?.distribution || {};
    const maxValue = Math.max(
        1,
        ...ENTITIES.flatMap(([key]) => [
            distribution[key]?.created || 0,
            distribution[key]?.deleted || 0
        ])
    );

    return (
        <main className="page-shell">
            <div className="eyebrow">Панель управления</div>
            <h1 className="page-heading">
                Аналитика <em>магазина.</em>
            </h1>

            <div className="admin-toolbar">
                <span>Период отчёта</span>
                <select value={period} onChange={e => setPeriod(e.target.value)} aria-label="Период отчёта">
                    {PERIODS.map(([value, label]) => (
                        <option key={value} value={value}>
                            {label}
                        </option>
                    ))}
                </select>
            </div>

            {loading ? (
                <div className="stats-grid">
                    {[1, 2, 3].map(i => (
                        <div className="skeleton-card" key={i}>
                            <span className="sk-top" />
                            <span className="sk-line" />
                            <span className="sk-line short" />
                        </div>
                    ))}
                </div>
            ) : error ? (
                <div className="error-panel">
                    <p>Не удалось загрузить аналитику.</p>
                    <small>{error}</small>
                    <button className="button button-outline" onClick={() => setReloadKey(v => v + 1)}>
                        Повторить
                    </button>
                </div>
            ) : stats ? (
                <>
                    <div className="stats-grid">
                        <div className="stat-card stat-created">
                            <span>Создано за период</span>
                            <strong>{fmt(stats.total_created)}</strong>
                            <small>событий</small>
                            <TrendingUp />
                        </div>
                        <div className="stat-card stat-deleted">
                            <span>Удалено за период</span>
                            <strong>{fmt(stats.total_deleted)}</strong>
                            <small>событий</small>
                            <TrendingDown />
                        </div>
                        <div className="stat-card stat-period">
                            <span>Период отчёта</span>
                            <strong>{periodLabel}</strong>
                            <small>по событиям из очереди</small>
                            <CalendarRange />
                        </div>
                    </div>

                    <div className="analytics-head">
                        <h3>По сущностям</h3>
                        <div className="legend">
                            <span className="legend-created"><i /> Создано</span>
                            <span className="legend-deleted"><i /> Удалено</span>
                        </div>
                    </div>

                    <div className="analytics-grid">
                        {ENTITIES.map(([key, label, tone]) => {
                            const created = distribution[key]?.created || 0;
                            const deleted = distribution[key]?.deleted || 0;
                            return (
                                <div className={`entity-card ${tone}`} key={key}>
                                    <div className="entity-head">
                                        <b>
                                            <span className="entity-dot" aria-hidden="true" />
                                            {label}
                                        </b>
                                        <small>всего: {fmt(created + deleted)}</small>
                                    </div>
                                    <div className="bar-row">
                                        <span className="bar-label">Создано</span>
                                        <div className="bar-track">
                                            <div
                                                className="bar-fill"
                                                style={{ width: `${(created / maxValue) * 100}%` }}
                                            />
                                        </div>
                                        <span className="bar-value">{fmt(created)}</span>
                                    </div>
                                    <div className="bar-row">
                                        <span className="bar-label">Удалено</span>
                                        <div className="bar-track">
                                            <div
                                                className="bar-fill is-deleted"
                                                style={{ width: `${(deleted / maxValue) * 100}%` }}
                                            />
                                        </div>
                                        <span className="bar-value">{fmt(deleted)}</span>
                                    </div>
                                </div>
                            );
                        })}
                    </div>

                    <p className="admin-note">
                        Данные собираются асинхронно из событий RabbitMQ — свежие действия могут появиться с задержкой.
                    </p>
                </>
            ) : null}
        </main>
    );
}

export default Admin;
