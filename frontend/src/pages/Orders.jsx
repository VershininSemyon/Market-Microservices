import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Check, Package } from 'lucide-react';
import { errorMessage } from '../config/api';
import { ordersApi } from '../services/market';
import { money } from '../shared';

export function Orders() {
    const [orders, setOrders] = useState([]);
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        ordersApi
            .list()
            .then(setOrders)
            .catch(e => setError(errorMessage(e)))
            .finally(() => setLoading(false));
    }, []);

    return (
        <main className="page-shell">
            <div className="eyebrow">ВАША ИСТОРИЯ</div>
            <h1 className="page-heading">
                Мои <em>заказы.</em>
            </h1>
            <p className="page-lead">Все покупки в одном месте.</p>
            {loading ? (
                <p>Загружаем заказы…</p>
            ) : error ? (
                <div className="error-panel">{error}</div>
            ) : !orders.length ? (
                <div className="empty-state">
                    <div className="empty-icon"><Package /></div>
                    <h2>Пока нет заказов</h2>
                    <p>Когда вы что-то закажете, история появится здесь.</p>
                    <Link to="/" className="button button-dark">
                        Перейти в каталог
                    </Link>
                </div>
            ) : (
                <div className="orders-list">
                    {orders.map(o => (
                        <article className="order-card" key={o.id}>
                            <div className="order-card-head">
                                <div>
                                    <small>ЗАКАЗ ОТ {new Date(o.created_at).toLocaleDateString('ru-RU')}</small>
                                    <b>№ {String(o.id).slice(0, 8).toUpperCase()}</b>
                                </div>
                                <span className="order-status">
                                    <Check size={14} /> Принят
                                </span>
                            </div>
                            <div className="order-product-lines">
                                {Object.entries(o.products || {}).map(([id, p]) => (
                                    <div key={id}>
                                        <span>
                                            {p.name} × {p.quantity}
                                        </span>
                                        <b>{money(p.price * p.quantity)}</b>
                                    </div>
                                ))}
                            </div>
                            <div className="order-total">
                                <span>{o.total_amount} товара</span>
                                <strong>{money(o.total_price)}</strong>
                            </div>
                        </article>
                    ))}
                </div>
            )}
        </main>
    );
}

export default Orders;