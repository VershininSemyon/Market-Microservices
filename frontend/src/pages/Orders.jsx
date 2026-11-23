
import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Check, Package } from 'lucide-react';
import { errorMessage } from '../config/api';
import { ordersApi } from '../services/market';
import { money, formatDate, shortId, plural } from '../shared';

export function Orders() {
    const [orders, setOrders] = useState([]);
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        let alive = true;
        ordersApi
            .list()
            .then(data => alive && setOrders(data))
            .catch(e => alive && setError(errorMessage(e)))
            .finally(() => alive && setLoading(false));
        return () => {
            alive = false;
        };
    }, []);

    const sorted = [...orders].sort(
        (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
    );

    return (
        <main className="page-shell">
            <div className="eyebrow">Ваша история</div>
            <h1 className="page-heading">
                Мои <em>заказы.</em>
            </h1>
            <p className="page-lead">Все покупки в одном месте — от новых к старым.</p>

            {loading ? (
                <p className="loading-line">Загружаем заказы…</p>
            ) : error ? (
                <div className="error-panel">{error}</div>
            ) : !sorted.length ? (
                <div className="empty-state">
                    <div className="empty-icon">
                        <Package />
                    </div>
                    <h2>Пока нет заказов</h2>
                    <p>Когда вы что-то закажете, история появится здесь.</p>
                    <Link to="/" className="button button-dark">
                        Перейти в каталог
                    </Link>
                </div>
            ) : (
                <div className="orders-list">
                    {sorted.map(o => (
                        <article className="order-card" key={o.id}>
                            <div className="order-card-head">
                                <div>
                                    <small>Заказ от {formatDate(o.created_at)}</small>
                                    <b>№ {shortId(o.id)}</b>
                                </div>
                                <span className="order-status">
                                    <Check size={13} /> Оформлен
                                </span>
                            </div>
                            <div className="order-product-lines">
                                {Object.entries(o.products || {}).map(([id, p], index) => (
                                    <div key={id}>
                                        <span className="order-line-index">{String(index + 1).padStart(2, '0')}</span>
                                        <span className="order-line-name">
                                            <Link to={`/product/${id}`}>{p.name}</Link> <i>× {p.quantity}</i>
                                        </span>
                                        <b>{money(p.price * p.quantity)}</b>
                                    </div>
                                ))}
                            </div>
                            <div className="order-total">
                                <span>
                                    {o.total_amount} {plural(o.total_amount, 'товар', 'товара', 'товаров')}
                                </span>
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
