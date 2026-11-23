
import { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import {
    ArrowDownUp,
    ArrowRight,
    ArrowUpRight,
    ChevronDown,
    ChevronLeft,
    ChevronRight,
    Search,
    ShoppingBag,
    SlidersHorizontal
} from 'lucide-react';
import { errorMessage } from '../config/api';
import { productsApi } from '../services/market';
import { plural, useReveal } from '../shared';
import ProductCard from '../components/ProductCard';

const PAGE_SIZE = 12;

const SORT_OPTIONS = [
    { value: '', label: 'По умолчанию' },
    { value: 'price-asc', label: 'Цена: по возрастанию' },
    { value: 'price-desc', label: 'Цена: по убыванию' },
    { value: 'name-asc', label: 'Название: А — Я' },
    { value: 'name-desc', label: 'Название: Я — А' }
];

const PRINCIPLES = [
    ['01', 'Отбираем вручную', 'Небольшая подборка вместо бесконечной витрины.'],
    ['02', 'Показываем цену', 'Итоговая стоимость видна до оформления заказа.'],
    ['03', 'Оставляем главное', 'Понятные описания без маркетингового шума.'],
    ['04', 'Помогаем после', 'Заказ можно отследить в личном кабинете.']
];

const TRUST = [
    ['01', 'Доставка без забот', 'Следите за статусом заказа в личном кабинете.'],
    ['02', 'Безопасные покупки', 'Данные аккаунта и заказов защищены.'],
    ['03', 'Осознанный выбор', 'Только товары, которые прошли отбор.'],
    ['04', 'Только нужное', 'Меньше шума — больше смысла.']
];

export function Catalog({ add, liked, onLike }) {
    const [items, setItems] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [hasNext, setHasNext] = useState(false);
    const [reloadKey, setReloadKey] = useState(0);
    const [searchParams, setSearchParams] = useSearchParams();
    const [query, setQuery] = useState(searchParams.get('text_query') || '');
    const [min, setMin] = useState(searchParams.get('min_price') || '');
    const [max, setMax] = useState(searchParams.get('max_price') || '');
    const [sort, setSort] = useState(searchParams.get('sort') || '');
    const [offset, setOffset] = useState(0);

    const trustRef = useReveal();
    const approachRef = useReveal();

    const invalidRange = min !== '' && max !== '' && Number(min) > Number(max);
    const orderBy = sort.startsWith('price') ? 'price' : sort.startsWith('name') ? 'name' : undefined;
    const order = sort.endsWith('desc') ? 'desc' : 'asc';

    // Фильтры живут в URL — ссылку на подборку можно скопировать.
    useEffect(() => {
        const params = {};
        if (query) params.text_query = query;
        if (min) params.min_price = min;
        if (max) params.max_price = max;
        if (sort) params.sort = sort;
        setSearchParams(params, { replace: true });
    }, [query, min, max, sort, setSearchParams]);

    useEffect(() => {
        if (invalidRange) {
            setLoading(false);
            setError('');
            return;
        }
        let alive = true;
        setLoading(true);

        const timer = setTimeout(() => {
            // При поиске бэкенд ограничивает выдачу Elasticsearch значением limit,
            // а offset применяет уже к SQL. Чтобы страницы поиска не пустели,
            // запрашиваем окно offset + PAGE_SIZE + 1 (не больше 100 — лимит API).
            const requestLimit = query ? Math.min(offset + PAGE_SIZE + 1, 100) : PAGE_SIZE + 1;

            productsApi
                .list({
                    limit: requestLimit,
                    offset,
                    text_query: query || undefined,
                    min_price: min || undefined,
                    max_price: max || undefined,
                    order_by: orderBy,
                    order
                })
                .then(data => {
                    if (!alive) return;
                    setItems(data.slice(0, PAGE_SIZE));
                    setHasNext(data.length > PAGE_SIZE);
                    setError('');
                })
                .catch(e => {
                    if (!alive) return;
                    setError(errorMessage(e));
                    setItems([]);
                    setHasNext(false);
                })
                .finally(() => alive && setLoading(false));
        }, 280);

        return () => {
            alive = false;
            clearTimeout(timer);
        };
    }, [query, min, max, sort, offset, reloadKey, orderBy, order, invalidRange]);

    const submit = e => {
        e.preventDefault();
        setOffset(0);
    };

    const reset = () => {
        setQuery('');
        setMin('');
        setMax('');
        setSort('');
        setOffset(0);
    };

    return (
        <main>
            <section className="hero">
                <div className="hero-content">
                    <div className="eyebrow">
                        <span className="eyebrow-rule" /> Кураторский маркетплейс
                    </div>
                    <h1>
                        Хорошие вещи.
                        <br />
                        <em>Без лишнего шума.</em>
                    </h1>
                    <p>
                        Небольшая подборка товаров для повседневной жизни: понятные описания, честные цены и
                        аккуратный выбор без бесконечной прокрутки.
                    </p>
                    <div className="hero-actions">
                        <a href="#catalog" className="button button-dark">
                            Смотреть каталог <ArrowRight size={17} />
                        </a>
                        <a href="#approach" className="text-link">
                            Как мы выбираем <ArrowUpRight size={15} />
                        </a>
                    </div>
                    <div className="hero-meta">
                        <span>Сезон 2026</span>
                        <span>Ручной отбор</span>
                        <span>Честные цены</span>
                    </div>
                </div>

                <aside className="hero-ledger" aria-label="Принципы маркетплейса">
                    <div className="ledger-head">
                        <span>Market / Index</span>
                        <span>01—04</span>
                    </div>
                    <ol>
                        {PRINCIPLES.map(([n, title, text]) => (
                            <li key={n}>
                                <span>{n}</span>
                                <div>
                                    <b>{title}</b>
                                    <small>{text}</small>
                                </div>
                            </li>
                        ))}
                    </ol>
                    <div className="ledger-foot">
                        <span>Меньше, но лучше</span>
                        <ArrowUpRight size={16} />
                    </div>
                </aside>

                <div className="hero-bottom-label">
                    LESS, BUT BETTER <span>—</span> 01 / 04
                </div>
            </section>

            <section className="trust-strip reveal" aria-label="Преимущества" ref={trustRef}>
                {TRUST.map(([n, title, text]) => (
                    <div key={n}>
                        <span className="trust-index">{n}</span>
                        <span>
                            <b>{title}</b>
                            <small>{text}</small>
                        </span>
                    </div>
                ))}
            </section>

            <section className="catalog-section section-shell" id="catalog">
                <div className="section-heading">
                    <div>
                        <div className="eyebrow">Каталог</div>
                        <h2>
                            Вещи, которые <em>пригождаются.</em>
                        </h2>
                        <p>Подборка на каждый день — от полезных мелочей до особенных находок.</p>
                    </div>
                    <span className="catalog-counter">
                        {loading
                            ? 'Обновляем…'
                            : items.length
                              ? `${items.length} ${plural(items.length, 'товар', 'товара', 'товаров')}`
                              : 'Пусто'}
                        <ArrowDownUp size={14} />
                    </span>
                </div>

                <form className="catalog-tools" onSubmit={submit}>
                    <label className="search-box">
                        <Search size={18} />
                        <input
                            value={query}
                            onChange={e => {
                                setQuery(e.target.value);
                                setOffset(0);
                            }}
                            placeholder="Что ищем сегодня?"
                            aria-label="Поиск по каталогу"
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
                                aria-label="Минимальная цена"
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
                                aria-label="Максимальная цена"
                            />
                        </label>
                        <label className="sort-select">
                            <SlidersHorizontal size={15} />
                            <select
                                value={sort}
                                onChange={e => {
                                    setSort(e.target.value);
                                    setOffset(0);
                                }}
                                aria-label="Сортировка"
                            >
                                {SORT_OPTIONS.map(option => (
                                    <option key={option.value} value={option.value}>
                                        {option.label}
                                    </option>
                                ))}
                            </select>
                            <ChevronDown size={14} />
                        </label>
                    </div>
                </form>

                {invalidRange && (
                    <p className="range-hint">Минимальная цена не может быть больше максимальной — уточните диапазон.</p>
                )}

                {error && (
                    <div className="error-panel">
                        <p>Не удалось загрузить каталог. Проверьте, что API доступен.</p>
                        <small>{error}</small>
                        <button className="button button-outline" onClick={() => setReloadKey(v => v + 1)}>
                            Повторить
                        </button>
                    </div>
                )}

                {loading ? (
                    <div className="product-grid">
                        {[1, 2, 3, 4, 5, 6].map(i => (
                            <div className="skeleton-card" key={i}>
                                <span className="sk-top" />
                                <span className="sk-mark" />
                                <span className="sk-line" />
                                <span className="sk-line short" />
                            </div>
                        ))}
                    </div>
                ) : !items.length && !error && !invalidRange ? (
                    <div className="empty-state">
                        <div className="empty-icon">
                            <ShoppingBag />
                        </div>
                        <h3>Пока ничего не найдено</h3>
                        <p>Попробуйте изменить запрос или сбросить фильтры.</p>
                        <button className="button button-dark" onClick={reset}>
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
                                disabled={loading || offset === 0}
                                onClick={() => setOffset(Math.max(0, offset - PAGE_SIZE))}
                            >
                                <ChevronLeft size={16} /> Назад
                            </button>
                            <span>Страница {Math.floor(offset / PAGE_SIZE) + 1}</span>
                            <button
                                className="button button-outline"
                                disabled={loading || !hasNext}
                                onClick={() => setOffset(offset + PAGE_SIZE)}
                            >
                                Дальше <ChevronRight size={16} />
                            </button>
                        </div>
                    </>
                )}
            </section>

            <section className="feature-banner section-shell reveal" id="approach" ref={approachRef}>
                <div className="feature-copy">
                    <div className="eyebrow">Наш подход</div>
                    <h2>
                        Меньше выбора.
                        <br />
                        <em>Больше смысла.</em>
                    </h2>
                    <p>
                        Мы не стремимся показать всё сразу. Вместо этого — небольшой каталог, в котором каждая
                        позиция объяснима: зачем она нужна, сколько стоит и когда приедет.
                    </p>
                    <a href="#catalog" className="button button-outline">
                        Вернуться к каталогу <ArrowUpRight size={16} />
                    </a>
                </div>
                <ol className="feature-index">
                    <li>
                        <span>01</span>
                        <div>
                            <b>Понятные цены</b>
                            <small>Стоимость и наличие видны до оформления заказа.</small>
                        </div>
                    </li>
                    <li>
                        <span>02</span>
                        <div>
                            <b>Спокойный выбор</b>
                            <small>Описания без давления и обещаний, которые нельзя проверить.</small>
                        </div>
                    </li>
                    <li>
                        <span>03</span>
                        <div>
                            <b>Прозрачный заказ</b>
                            <small>История покупок и состав заказа всегда под рукой.</small>
                        </div>
                    </li>
                </ol>
            </section>
        </main>
    );
}

export default Catalog;
