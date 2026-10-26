import { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import {
    ArrowDownUp, ArrowRight, ArrowUpRight, Search, SlidersHorizontal, ChevronDown,
    ChevronLeft, ChevronRight, ShoppingBag, Truck, ShieldCheck, Leaf, Package, Zap, Star
} from 'lucide-react';
import { errorMessage } from '../config/api';
import { productsApi } from '../services/market';
import { money } from '../shared';
import ProductCard from '../components/ProductCard';

export function Catalog({ add, liked, onLike }) {
    const [items, setItems] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [searchParams, setSearchParams] = useSearchParams();

    const [query, setQuery] = useState(searchParams.get('text_query') || '');
    const [min, setMin] = useState(searchParams.get('min_price') || '');
    const [max, setMax] = useState(searchParams.get('max_price') || '');
    const [sort, setSort] = useState(searchParams.get('order_by') || '');
    const [offset, setOffset] = useState(0);
    const [totalPage, setTotalPage] = useState(false);

    useEffect(() => {
        let alive = true;
        setLoading(true);
        const params = {
            limit: 12,
            offset,
            text_query: query || undefined,
            min_price: min || undefined,
            max_price: max || undefined,
            order_by: sort || undefined,
            order: sort === 'price' ? 'asc' : 'desc'
        };
        productsApi
            .list(params)
            .then(data => {
                if (alive) {
                    setItems(data.filter(p => p.is_active !== false));
                    setTotalPage(data.length === 12);
                    setError('');
                }
            })
            .catch(e => {
                if (alive) {
                    setError(errorMessage(e));
                    setItems([]);
                }
            })
            .finally(() => alive && setLoading(false));
        return () => {
            alive = false;
        };
    }, [query, min, max, sort, offset]);

    const submit = e => {
        e.preventDefault();
        setOffset(0);
        setSearchParams(query ? { text_query: query } : {});
    };

    return (
        <main>
            <section className="hero">
                <div className="hero-content">
                    <div className="eyebrow">
                        <span className="eyebrow-dot" /> КУРАТОРСКИЙ МАРКЕТПЛЕЙС
                    </div>
                    <h1>
                        Хорошие вещи.
                        <br />
                        <em>Хороший выбор.</em>
                    </h1>
                    <p>
                        Находите вещи, которые подходят вашему ритму жизни. Дизайн, качество и осознанный выбор — в
                        одном месте.
                    </p>
                    <a href="#catalog" className="button button-lime">
                        Исследовать каталог <ArrowRight size={18} />
                    </a>
                    <div className="hero-proof">
                        <div className="proof-avatars">
                            <span>А</span>
                            <span>М</span>
                            <span>Е</span>
                            <span>+</span>
                        </div>
                        <div>
                            <strong>Покупки с удовольствием</strong>
                            <small>Выбирайте то, что важно именно вам</small>
                        </div>
                    </div>
                </div>
                <div className="hero-art">
                    <div className="hero-orbit orbit-one"></div>
                    <div className="hero-orbit orbit-two"></div>
                    <div className="hero-blob">
                        <img
                            src="https://images.unsplash.com/photo-1490312278390-ab64016e0aa9?auto=format&fit=crop&w=1100&q=90"
                            alt="Подборка стильных вещей"
                        />
                    </div>
                    <div className="floating-card floating-top">
                        <span className="floating-icon"><Zap size={18} /></span>
                        <div>
                            <b>Выбор дня</b>
                            <small>Вещи с характером</small>
                        </div>
                    </div>
                    <div className="floating-card floating-bottom">
                        <span className="rating-star"><Star size={16} fill="currentColor" /></span>
                        <div>
                            <b>Любимые находки</b>
                            <small>Откройте что-то новое</small>
                        </div>
                    </div>
                    <div className="hero-spark">✳</div>
                </div>
                <div className="hero-bottom-label">
                    LESS, BUT BETTER <span>—</span> 01 / 04
                </div>
            </section>

            <section className="trust-strip">
                <div>
                    <Truck />
                    <span>
                        <b>Доставка без забот</b>
                        <small>Отслеживайте свои заказы</small>
                    </span>
                </div>
                <div>
                    <ShieldCheck />
                    <span>
                        <b>Безопасные покупки</b>
                        <small>Ваши данные под защитой</small>
                    </span>
                </div>
                <div>
                    <Leaf />
                    <span>
                        <b>Осознанный выбор</b>
                        <small>Покупайте то, что любите</small>
                    </span>
                </div>
                <div>
                    <Package />
                    <span>
                        <b>Только нужное</b>
                        <small>Меньше шума, больше смысла</small>
                    </span>
                </div>
            </section>

            <section className="catalog-section section-shell" id="catalog">
                <div className="section-heading">
                    <div>
                        <div className="eyebrow">НАШ КАТАЛОГ</div>
                        <h2>
                            Вещи, которые <em>вдохновляют.</em>
                        </h2>
                        <p>Подборка на каждый день — от полезных мелочей до особенных находок.</p>
                    </div>
                    <span className="catalog-counter">
                        {items.length ? `${items.length} товаров` : ''} <ArrowDownUp size={15} />
                    </span>
                </div>

                <form className="catalog-tools" onSubmit={submit}>
                    <label className="search-box">
                        <Search size={19} />
                        <input
                            value={query}
                            onChange={e => {
                                setQuery(e.target.value);
                                setOffset(0);
                            }}
                            placeholder="Что ищем сегодня?"
                        />
                        <button type="submit" className="search-submit">
                            Найти
                        </button>
                    </label>
                    <div className="filter-group">
                        <label className="price-field">
                            <span>От ₽</span>
                            <input
                                type="number"
                                min="0"
                                value={min}
                                onChange={e => {
                                    setMin(e.target.value);
                                    setOffset(0);
                                }}
                                placeholder="0"
                            />
                        </label>
                        <label className="price-field">
                            <span>До ₽</span>
                            <input
                                type="number"
                                min="0"
                                value={max}
                                onChange={e => {
                                    setMax(e.target.value);
                                    setOffset(0);
                                }}
                                placeholder="∞"
                            />
                        </label>
                        <label className="sort-select">
                            <SlidersHorizontal size={16} />
                            <select value={sort} onChange={e => setSort(e.target.value)}>
                                <option value="">По умолчанию</option>
                                <option value="price">По цене</option>
                                <option value="name">По названию</option>
                            </select>
                            <ChevronDown size={15} />
                        </label>
                    </div>
                </form>

                {error && (
                    <div className="error-panel">
                        <p>Не удалось загрузить каталог. Проверьте, что API доступен.</p>
                        <small>{error}</small>
                        <button className="button button-outline" onClick={() => setOffset(v => v)}>
                            Повторить
                        </button>
                    </div>
                )}

                {loading ? (
                    <div className="product-grid">
                        {[1, 2, 3, 4, 5, 6, 7, 8].map(i => (
                            <div className="skeleton-card" key={i}>
                                <div />
                                <span />
                                <span />
                            </div>
                        ))}
                    </div>
                ) : !items.length && !error ? (
                    <div className="empty-state">
                        <div className="empty-icon"><ShoppingBag /></div>
                        <h3>Пока ничего не найдено</h3>
                        <p>Попробуйте изменить запрос или сбросить фильтры.</p>
                        <button
                            className="button button-dark"
                            onClick={() => {
                                setQuery('');
                                setMin('');
                                setMax('');
                                setSort('');
                                setOffset(0);
                            }}
                        >
                            Сбросить фильтры
                        </button>
                    </div>
                ) : (
                    <>
                        <div className="product-grid">
                            {items.map((p, i) => (
                                <ProductCard
                                    key={p.id}
                                    product={p}
                                    index={i + offset}
                                    onAdd={add}
                                    liked={liked.includes(p.id)}
                                    onLike={onLike}
                                />
                            ))}
                        </div>
                        <div className="pagination">
                            <button
                                className="button button-outline"
                                disabled={offset === 0}
                                onClick={() => setOffset(Math.max(0, offset - 12))}
                            >
                                <ChevronLeft size={17} /> Назад
                            </button>
                            <span>Страница {Math.floor(offset / 12) + 1}</span>
                            <button
                                className="button button-outline"
                                disabled={!totalPage}
                                onClick={() => setOffset(offset + 12)}
                            >
                                Дальше <ChevronRight size={17} />
                            </button>
                        </div>
                    </>
                )}
            </section>

            <section className="feature-banner section-shell">
                <div className="feature-copy">
                    <div className="eyebrow">МЕНЬШЕ, НО ЛУЧШЕ</div>
                    <h2>
                        Покупайте с умом.
                        <br />
                        <em>Живите с удовольствием.</em>
                    </h2>
                    <p>
                        Мы верим, что хорошие вещи не нуждаются в лишнем шуме. Только полезные товары, понятные цены и
                        приятный опыт.
                    </p>
                    <a href="#catalog" className="button button-dark">
                        Найти свою вещь <ArrowUpRight size={18} />
                    </a>
                </div>
                <div className="feature-visual">
                    <img
                        src="https://images.unsplash.com/photo-1494438639946-1ebd1d20bf85?auto=format&fit=crop&w=1000&q=85"
                        alt="Минималистичный интерьер"
                    />
                    <div className="feature-note">
                        <Leaf size={17} />
                        <span>
                            Выбор с заботой
                            <br />
                            <b>о вашем времени</b>
                        </span>
                    </div>
                </div>
            </section>
        </main>
    );
}

export default Catalog;