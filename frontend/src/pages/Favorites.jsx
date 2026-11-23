import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Heart, ArrowRight } from 'lucide-react';
import { productsApi } from '../services/market';
import { plural } from '../shared';
import ProductCard from '../components/ProductCard';

export function Favorites({ liked, onLike, onAdd, onClear, onRemoveMissing }) {
    const [items, setItems] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [reloadKey, setReloadKey] = useState(0);

    useEffect(() => {
        let alive = true;
        if (!liked.length) {
            setItems([]);
            setLoading(false);
            setError('');
            return;
        }
        setLoading(true);
        Promise.allSettled(liked.map(id => productsApi.get(id))).then(results => {
            if (!alive) return;
            const found = [];
            const missing = [];
            let failed = 0;
            results.forEach((result, i) => {
                if (result.status === 'fulfilled') {
                    found.push(result.value);
                } else if (result.reason?.response?.status === 404) {
                    missing.push(liked[i]);
                } else {
                    failed += 1;
                }
            });
            setItems(found);
            setError(failed ? 'Не удалось загрузить часть товаров. Проверьте подключение и повторите.' : '');
            setLoading(false);
            if (missing.length) onRemoveMissing(missing);
        });
        return () => {
            alive = false;
        };
    }, [liked, reloadKey, onRemoveMissing]);

    const clearAll = () => {
        if (window.confirm('Очистить список избранного?')) onClear();
    };

    // Мгновенно скрываем снятые с лайка карточки, не дожидаясь перезапроса.
    const visible = items.filter(p => liked.includes(p.id));

    return (
        <main className="page-shell">
            <div className="page-title-row">
                <div>
                    <div className="eyebrow">Ваш список</div>
                    <h1>
                        Избранное.<em> Сохранённое.</em>
                    </h1>
                </div>
                <span className="subtle">
                    {liked.length} {plural(liked.length, 'товар', 'товара', 'товаров')}
                </span>
            </div>

            {error && (
                <div className="error-panel">
                    <p>{error}</p>
                    <button className="button button-outline" onClick={() => setReloadKey(v => v + 1)}>
                        Повторить
                    </button>
                </div>
            )}

            {!liked.length ? (
                <div className="empty-state">
                    <div className="empty-icon">
                        <Heart />
                    </div>
                    <h2>В избранном пока пусто</h2>
                    <p>Нажимайте на сердечко в каталоге, чтобы сохранять вещи, к которым хотите вернуться.</p>
                    <Link to="/" className="button button-dark">
                        Перейти в каталог <ArrowRight size={17} />
                    </Link>
                </div>
            ) : loading && !visible.length ? (
                <div className="product-grid">
                    {[1, 2, 3, 4].map(i => (
                        <div className="skeleton-card" key={i}>
                            <span className="sk-top" />
                            <span className="sk-mark" />
                            <span className="sk-line" />
                            <span className="sk-line short" />
                        </div>
                    ))}
                </div>
            ) : (
                <>
                    <div className="product-grid">
                        {visible.map((p, i) => (
                            <ProductCard
                                key={p.id}
                                product={p}
                                index={i}
                                onAdd={onAdd}
                                liked
                                onLike={onLike}
                            />
                        ))}
                    </div>
                    <div className="profile-actions">
                        <button className="text-button text-danger" onClick={clearAll}>
                            Очистить список
                        </button>
                    </div>
                </>
            )}
        </main>
    );
}

export default Favorites;