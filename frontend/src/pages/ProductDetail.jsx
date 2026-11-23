
import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { ArrowLeft, Star, Truck, ShieldCheck, ShoppingBag, Pencil, Trash2 } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { errorMessage } from '../config/api';
import { productsApi, reviewsApi } from '../services/market';
import { money, formatDate, productInitial, shortId, plural, toneClass } from '../shared';

export function ProductDetail({ add }) {
    const { id } = useParams();
    const { user } = useAuth();
    const [product, setProduct] = useState(null);
    const [reviews, setReviews] = useState({ reviews: [], avg_rating: 0 });
    const [busy, setBusy] = useState(true);
    const [error, setError] = useState('');
    const [rating, setRating] = useState(9);
    const [comment, setComment] = useState('');
    const [pending, setPending] = useState(false);
    const [notice, setNotice] = useState('');
    const [noticeKind, setNoticeKind] = useState('success');
    const [editingId, setEditingId] = useState(null);
    const [editForm, setEditForm] = useState({ rating: 10, comment: '' });

    useEffect(() => {
        let ok = true;
        setBusy(true);
        setError('');
        setNotice('');
        setEditingId(null);
        setComment('');
        setRating(9);
        setProduct(null);
        setReviews({ reviews: [], avg_rating: 0 });

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
            .catch(e => ok && setError(errorMessage(e)))
            .finally(() => ok && setBusy(false));

        return () => {
            ok = false;
        };
    }, [id]);

    const showNotice = (text, kind = 'success') => {
        setNotice(text);
        setNoticeKind(kind);
    };

    const refreshReviews = async () => {
        try {
            setReviews(await reviewsApi.list(id));
        } catch (e) {
            showNotice(errorMessage(e), 'error');
        }
    };

    const submit = async e => {
        e.preventDefault();
        setPending(true);
        try {
            await reviewsApi.create({ product_id: id, rating, comment });
            setComment('');
            setRating(9);
            showNotice('Спасибо за отзыв!');
            await refreshReviews();
        } catch (e) {
            showNotice(errorMessage(e), 'error');
        } finally {
            setPending(false);
        }
    };

    const startEdit = review => {
        setEditingId(review.id);
        setEditForm({ rating: review.rating, comment: review.comment });
        setNotice('');
    };

    const saveEdit = async e => {
        e.preventDefault();
        setPending(true);
        try {
            await reviewsApi.update(editingId, editForm);
            setEditingId(null);
            showNotice('Отзыв обновлён');
            await refreshReviews();
        } catch (e) {
            showNotice(errorMessage(e), 'error');
        } finally {
            setPending(false);
        }
    };

    const removeReview = async reviewId => {
        if (!window.confirm('Удалить отзыв?')) return;
        try {
            await reviewsApi.remove(reviewId);
            if (editingId === reviewId) setEditingId(null);
            showNotice('Отзыв удалён');
            await refreshReviews();
        } catch (e) {
            showNotice(errorMessage(e), 'error');
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
                    <p>{error || 'Возможно, товар был удалён из каталога.'}</p>
                    <Link to="/" className="button button-dark">
                        В каталог
                    </Link>
                </div>
            </main>
        );
    }

    const inStock = product.quantity > 0;
    const reviewList = reviews.reviews || [];
    const myReview = user ? reviewList.find(r => r.user_id === user.id) : null;
    const commentLength = comment.length;

    return (
        <main className="page-shell">
            <Link to="/" className="back-link">
                <ArrowLeft size={16} /> Вернуться в каталог
            </Link>

            <div className="detail-layout">
                <aside className={`detail-specimen ${toneClass(product)}`} aria-label="Карточка товара">
                    <div className="specimen-top">
                        <span>Product / Specimen</span>
                        <span>№ {shortId(product.id)}</span>
                    </div>
                    <div className="specimen-mark" aria-hidden="true">
                        <span>{productInitial(product)}</span>
                    </div>
                    <dl className="specimen-meta">
                        <div>
                            <dt>Цена</dt>
                            <dd>{money(product.price)}</dd>
                        </div>
                        <div>
                            <dt>Наличие</dt>
                            <dd className={inStock ? '' : 'is-muted'}>
                                {inStock ? `${product.quantity} шт.` : 'Нет в наличии'}
                            </dd>
                        </div>
                        <div>
                            <dt>В каталоге с</dt>
                            <dd>{formatDate(product.created_at)}</dd>
                        </div>
                    </dl>
                </aside>

                <div className="detail-info">
                    <div className="eyebrow">Товар / {shortId(product.id)}</div>
                    <h1>{product.name}</h1>
                    <div className="detail-rating">
                        <Star size={16} fill="currentColor" />
                        {reviews.avg_rating ? Number(reviews.avg_rating).toFixed(1) : 'Новый товар'}
                        <span>
                            · {reviewList.length} {plural(reviewList.length, 'отзыв', 'отзыва', 'отзывов')}
                        </span>
                    </div>
                    <div className="detail-price">{money(product.price)}</div>
                    <p className="detail-description">
                        {product.description ||
                            'Продуманный товар для повседневной жизни. Хороший дизайн, практичность и качество в каждой детали.'}
                    </p>
                    <div className="detail-meta">
                        <span>
                            <Truck /> Статус заказа — в кабинете
                        </span>
                        <span>
                            <ShieldCheck /> Данные под защитой
                        </span>
                    </div>
                    <div className="detail-actions">
                        <button
                            className="button button-dark"
                            disabled={!inStock}
                            onClick={() => add(product)}
                        >
                            <ShoppingBag size={18} /> Добавить в корзину
                        </button>
                        <span className="stock-note">
                            {inStock ? `В наличии: ${product.quantity}` : 'Нет в наличии'}
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
                        <div className="eyebrow">Опыт покупателей</div>
                        <h2>
                            Отзывы <em>о товаре</em>
                        </h2>
                    </div>
                    <div className="review-average">
                        <Star size={15} fill="currentColor" /> {Number(reviews.avg_rating || 0).toFixed(1)} / 10
                    </div>
                </div>

                {notice && (
                    <p className={noticeKind === 'error' ? 'notice-text is-error' : 'notice-text'}>{notice}</p>
                )}

                {user && myReview && editingId !== myReview.id && (
                    <div className="review-own">
                        <p>Вы уже оставили отзыв на этот товар.</p>
                        <button className="button button-outline button-small" onClick={() => startEdit(myReview)}>
                            <Pencil size={13} /> Изменить отзыв
                        </button>
                    </div>
                )}

                {user && !myReview && (
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
                            <span>Ваш отзыв</span>
                            <textarea
                                required
                                minLength={20}
                                maxLength={1000}
                                rows="3"
                                value={comment}
                                onChange={e => setComment(e.target.value)}
                                placeholder="Что понравилось в товаре?"
                            />
                            <small className={commentLength < 20 ? 'char-hint is-warn' : 'char-hint'}>
                                {commentLength < 20
                                    ? `Ещё ${20 - commentLength} символов до минимума (20)`
                                    : `${commentLength} / 1000`}
                            </small>
                        </label>
                        <button className="button button-dark" disabled={pending}>
                            {pending ? 'Публикуем…' : 'Опубликовать отзыв'}
                        </button>
                    </form>
                )}

                {reviewList.length ? (
                    <div className="reviews-list">
                        {reviewList.map(r => {
                            const isOwn = user?.id === r.user_id;
                            return (
                                <article className="review-card" key={r.id}>
                                    <div className="review-card-head">
                                        <span className={`review-avatar ${toneClass({ id: r.user_id })}`} aria-hidden="true">
                                            {String(r.user_id).slice(0, 1).toUpperCase()}
                                        </span>
                                        <div>
                                            <b>{isOwn ? 'Ваш отзыв' : 'Покупатель'}</b>
                                            <small>{formatDate(r.created_at)}</small>
                                        </div>
                                        <span className="review-score">
                                            <Star size={13} fill="currentColor" /> {r.rating}/10
                                        </span>
                                    </div>

                                    {editingId === r.id ? (
                                        <form className="review-inline-form" onSubmit={saveEdit}>
                                            <label className="form-field">
                                                <span>Оценка: {editForm.rating} / 10</span>
                                                <input
                                                    type="range"
                                                    min="1"
                                                    max="10"
                                                    value={editForm.rating}
                                                    onChange={e => setEditForm({ ...editForm, rating: +e.target.value })}
                                                />
                                            </label>
                                            <label className="form-field">
                                                <span>Комментарий</span>
                                                <textarea
                                                    required
                                                    minLength={20}
                                                    maxLength={1000}
                                                    rows="3"
                                                    value={editForm.comment}
                                                    onChange={e => setEditForm({ ...editForm, comment: e.target.value })}
                                                />
                                                <small
                                                    className={
                                                        editForm.comment.length < 20 ? 'char-hint is-warn' : 'char-hint'
                                                    }
                                                >
                                                    {editForm.comment.length < 20
                                                        ? `Ещё ${20 - editForm.comment.length} символов до минимума (20)`
                                                        : `${editForm.comment.length} / 1000`}
                                                </small>
                                            </label>
                                            <div className="review-form-actions">
                                                <button className="button button-dark button-small" disabled={pending}>
                                                    {pending ? 'Сохраняем…' : 'Сохранить'}
                                                </button>
                                                <button
                                                    type="button"
                                                    className="button button-outline button-small"
                                                    onClick={() => setEditingId(null)}
                                                >
                                                    Отмена
                                                </button>
                                            </div>
                                        </form>
                                    ) : (
                                        <>
                                            <p>{r.comment}</p>
                                            {isOwn && (
                                                <div className="review-actions">
                                                    <button className="text-button" onClick={() => startEdit(r)}>
                                                        <Pencil size={13} /> Изменить
                                                    </button>
                                                    <button
                                                        className="text-button text-danger"
                                                        onClick={() => removeReview(r.id)}
                                                    >
                                                        <Trash2 size={13} /> Удалить
                                                    </button>
                                                </div>
                                            )}
                                        </>
                                    )}
                                </article>
                            );
                        })}
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
