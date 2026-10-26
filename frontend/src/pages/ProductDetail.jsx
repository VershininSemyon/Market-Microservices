import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { ArrowLeft, Star, Truck, ShieldCheck, ShoppingBag } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { errorMessage } from '../config/api';
import { productsApi, reviewsApi } from '../services/market';
import { money, imageFor } from '../shared';

export function ProductDetail({ add }) {
    const { id } = useParams();
    const { user } = useAuth();
    const [product, setProduct] = useState(null);
    const [reviews, setReviews] = useState({ reviews: [], avg_rating: 0 });
    const [busy, setBusy] = useState(true);
    const [error, setError] = useState('');
    const [rating, setRating] = useState(9);
    const [comment, setComment] = useState('');
    const [notice, setNotice] = useState('');

    useEffect(() => {
        let ok = true;
        Promise.all([
            productsApi.get(id),
            reviewsApi.list(id).catch(() => ({ reviews: [], avg_rating: 0 }))
        ])
            .then(([p, r]) => {
                if (ok) {
                    setProduct(p);
                    setReviews(r);
                }
            })
            .catch(e => setError(errorMessage(e)))
            .finally(() => setBusy(false));
        return () => {
            ok = false;
        };
    }, [id]);

    const submit = async e => {
        e.preventDefault();
        try {
            await reviewsApi.create({ product_id: id, rating, comment });
            setComment('');
            setNotice('Спасибо за отзыв!');
            setReviews(await reviewsApi.list(id));
        } catch (e) {
            setNotice(errorMessage(e));
        }
    };

    if (busy) {
        return (
            <main className="page-shell">
                <div className="loading-line">Загружаем товар…</div>
            </main>
        );
    }

    if (!product) {
        return (
            <main className="page-shell">
                <div className="empty-state">
                    <h2>Товар не найден</h2>
                    <p>{error}</p>
                    <Link to="/" className="button button-dark">
                        В каталог
                    </Link>
                </div>
            </main>
        );
    }

    return (
        <main className="page-shell">
            <Link to="/" className="back-link">
                <ArrowLeft size={16} /> Вернуться в каталог
            </Link>
            <div className="detail-layout">
                <div className="detail-image">
                    <img src={imageFor(product, 2)} alt={product.name} />
                    <span className="image-chip">{product.quantity > 0 ? 'В наличии' : 'Нет в наличии'}</span>
                </div>
                <div className="detail-info">
                    <div className="eyebrow">ВЫБОР MARKET</div>
                    <h1>{product.name}</h1>
                    <div className="detail-rating">
                        <Star size={17} fill="currentColor" />{' '}
                        {reviews.avg_rating ? Number(reviews.avg_rating).toFixed(1) : 'Новый товар'}{' '}
                        <span>· {reviews.reviews?.length || 0} отзывов</span>
                    </div>
                    <div className="detail-price">{money(product.price)}</div>
                    <p className="detail-description">
                        {product.description ||
                            'Продуманный товар для повседневной жизни. Хороший дизайн, практичность и качество в каждой детали.'}
                    </p>
                    <div className="detail-meta">
                        <span>
                            <Truck /> Удобная доставка
                        </span>
                        <span>
                            <ShieldCheck /> Защищённая оплата
                        </span>
                    </div>
                    <div className="detail-actions">
                        <button
                            className="button button-dark"
                            disabled={product.quantity < 1}
                            onClick={() => add(product)}
                        >
                            <ShoppingBag size={18} /> Добавить в корзину
                        </button>
                        <span className="stock-note">
                            {product.quantity > 0 ? `В наличии: ${product.quantity}` : 'Нет в наличии'}
                        </span>
                    </div>
                    <div className="detail-divider" />
                    <div className="detail-guarantee">
                        <ShieldCheck />
                        <div>
                            <b>Покупка без лишних забот</b>
                            <p>Прозрачная информация и поддержка на каждом шаге.</p>
                        </div>
                    </div>
                </div>
            </div>

            <section className="reviews-section">
                <div className="section-heading">
                    <div>
                        <div className="eyebrow">ОПЫТ ПОКУПАТЕЛЕЙ</div>
                        <h2>
                            Отзывы <em>о товаре</em>
                        </h2>
                    </div>
                    <div className="review-average">
                        <Star fill="currentColor" /> {Number(reviews.avg_rating || 0).toFixed(1)} / 10
                    </div>
                </div>

                {user && (
                    <form className="review-form" onSubmit={submit}>
                        <h3>Поделитесь впечатлением</h3>
                        <label className="form-field">
                            <span>Оценка: {rating} / 10</span>
                            <input
                                type="range"
                                min="1"
                                max="10"
                                value={rating}
                                onChange={e => setRating(+e.target.value)}
                            />
                        </label>
                        <label className="form-field">
                            <span>Ваш отзыв (от 20 символов)</span>
                            <textarea
                                required
                                minLength={20}
                                maxLength={1000}
                                rows="3"
                                value={comment}
                                onChange={e => setComment(e.target.value)}
                                placeholder="Что понравилось в товаре?"
                            />
                        </label>
                        {notice && <p className="notice-text">{notice}</p>}
                        <button className="button button-dark">Опубликовать отзыв</button>
                    </form>
                )}

                {reviews.reviews?.length ? (
                    <div className="reviews-list">
                        {reviews.reviews.map(r => (
                            <article className="review-card" key={r.id}>
                                <div className="review-card-head">
                                    <span className="review-avatar">
                                        {String(r.user_id).slice(0, 1).toUpperCase()}
                                    </span>
                                    <div>
                                        <b>Покупатель</b>
                                        <small>{new Date(r.created_at).toLocaleDateString('ru-RU')}</small>
                                    </div>
                                    <span className="review-score">
                                        <Star size={14} fill="currentColor" /> {r.rating}/10
                                    </span>
                                </div>
                                <p>{r.comment}</p>
                                {user?.id === r.user_id && (
                                    <button
                                        className="text-danger"
                                        onClick={async () => {
                                            await reviewsApi.remove(r.id);
                                            setReviews(await reviewsApi.list(id));
                                        }}
                                    >
                                        Удалить отзыв
                                    </button>
                                )}
                            </article>
                        ))}
                    </div>
                ) : (
                    <div className="empty-review">
                        Пока нет отзывов.{' '}
                        {user
                            ? 'Станьте первым, кто поделится впечатлением!'
                            : 'Войдите, чтобы оставить первый отзыв.'}
                    </div>
                )}
            </section>
        </main>
    );
}

export default ProductDetail;