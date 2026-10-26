import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { ArrowLeft, ArrowRight, Minus, Plus, ShoppingBag, Trash2, ShieldCheck } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { errorMessage } from '../config/api';
import { ordersApi } from '../services/market';
import { money, imageFor } from '../shared';

export function Cart({ cart, setCart, add, toast }) {
    const navigate = useNavigate();
    const { user } = useAuth();
    const entries = Object.entries(cart);
    const [busy, setBusy] = useState(false);
    const total = entries.reduce((sum, [id, item]) => sum + item.product.price * item.quantity, 0);

    const update = (id, q) => setCart(prev => ({ ...prev, [id]: { ...prev[id], quantity: q } }));

    const checkout = async () => {
        if (!user) {
            navigate('/login');
            return;
        }
        setBusy(true);
        try {
            const products = Object.fromEntries(entries.map(([id, x]) => [id, x.quantity]));
            await ordersApi.create(products);
            setCart({});
            toast('Заказ успешно оформлен!');
            navigate('/orders');
        } catch (e) {
            toast(errorMessage(e));
        } finally {
            setBusy(false);
        }
    };

    return (
        <main className="page-shell">
            <div className="page-title-row">
                <div>
                    <div className="eyebrow">ВАШ ВЫБОР</div>
                    <h1>
                        Корзина <em>покупок.</em>
                    </h1>
                </div>
                <span className="subtle">{entries.length} позиций</span>
            </div>
            {!entries.length ? (
                <div className="empty-state cart-empty">
                    <div className="empty-icon"><ShoppingBag /></div>
                    <h2>Корзина пока пуста</h2>
                    <p>Самое время найти что-нибудь хорошее.</p>
                    <Link to="/" className="button button-dark">
                        Перейти в каталог <ArrowRight size={17} />
                    </Link>
                </div>
            ) : (
                <div className="cart-layout">
                    <div className="cart-items">
                        {entries.map(([id, { product, quantity }], i) => (
                            <article className="cart-item" key={id}>
                                <img src={imageFor(product, i)} alt={product.name} />
                                <div className="cart-item-info">
                                    <Link to={`/product/${id}`}>{product.name}</Link>
                                    <small>{money(product.price)} за шт.</small>
                                    <div className="quantity-control">
                                        <button
                                            onClick={() =>
                                                quantity <= 1
                                                    ? setCart(prev => {
                                                          const n = { ...prev };
                                                          delete n[id];
                                                          return n;
                                                      })
                                                    : update(id, quantity - 1)
                                            }
                                        >
                                            <Minus size={14} />
                                        </button>
                                        <span>{quantity}</span>
                                        <button
                                            disabled={quantity >= product.quantity}
                                            onClick={() => update(id, quantity + 1)}
                                        >
                                            <Plus size={14} />
                                        </button>
                                    </div>
                                </div>
                                <div className="cart-item-total">
                                    <b>{money(product.price * quantity)}</b>
                                    <button
                                        className="remove-button"
                                        onClick={() =>
                                            setCart(prev => {
                                                const n = { ...prev };
                                                delete n[id];
                                                return n;
                                            })
                                        }
                                        aria-label="Удалить"
                                    >
                                        <Trash2 size={17} />
                                    </button>
                                </div>
                            </article>
                        ))}
                        <Link to="/" className="back-link">
                            <ArrowLeft size={16} /> Продолжить покупки
                        </Link>
                    </div>
                    <aside className="order-summary">
                        <h3>Ваш заказ</h3>
                        <div className="summary-line">
                            <span>Товары</span>
                            <span>{money(total)}</span>
                        </div>
                        <div className="summary-line">
                            <span>Доставка</span>
                            <span className="free-label">Бесплатно</span>
                        </div>
                        <div className="summary-total">
                            <span>Итого</span>
                            <strong>{money(total)}</strong>
                        </div>
                        <button
                            className="button button-dark button-wide"
                            disabled={busy}
                            onClick={checkout}
                        >
                            {busy ? 'Оформляем…' : 'Оформить заказ'} <ArrowRight size={18} />
                        </button>
                        <div className="secure-note">
                            <ShieldCheck size={16} /> Безопасное оформление заказа
                        </div>
                    </aside>
                </div>
            )}
        </main>
    );
}

export default Cart;