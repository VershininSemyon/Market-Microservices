
import { useState, useEffect, useCallback } from 'react';
import { Routes, Route, Link } from 'react-router-dom';
import { Box, ChartNoAxesColumnIncreasing, LockKeyhole } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import Layout from '../components/Layout';
import Toast from '../components/Toast';
import Catalog from './Catalog';
import AuthPage from './AuthPage';
import ProductDetail from './ProductDetail';
import Cart from './Cart';
import Orders from './Orders';
import Profile from './Profile';
import Favorites from './Favorites';
import Admin from './Admin';
import AdminProducts from './AdminProducts';

function NoAccess() {
    return (
        <main className="page-shell">
            <div className="empty-state">
                <div className="empty-icon"><LockKeyhole /></div>
                <h2>Раздел для администраторов</h2>
                <p>Эта страница доступна только пользователям с правами администратора.</p>
                <Link to="/" className="button button-dark">Вернуться в каталог</Link>
            </div>
        </main>
    );
}

export default function AppBody() {
    const { user, loading, isAdmin } = useAuth();

    const [cart, setCart] = useState(() => {
        try {
            return JSON.parse(localStorage.getItem('market_cart') || '{}');
        } catch {
            return {};
        }
    });
    const [liked, setLiked] = useState(() => {
        try {
            return JSON.parse(localStorage.getItem('market_liked') || '[]');
        } catch {
            return [];
        }
    });
    const [toast, setToast] = useState(null);

    useEffect(() => {
        try {
            localStorage.setItem('market_cart', JSON.stringify(cart));
        } catch { /* хранилище недоступно — не критично */ }
    }, [cart]);

    useEffect(() => {
        try {
            localStorage.setItem('market_liked', JSON.stringify(liked));
        } catch { /* хранилище недоступно — не критично */ }
    }, [liked]);

    const showToast = useCallback((message, type = 'success', action) => {
        setToast({ message, type, action });
    }, []);
    const closeToast = useCallback(() => setToast(null), []);

    const add = useCallback(product => {
        if (!product.quantity) {
            showToast('Товар закончился', 'error');
            return;
        }
        setCart(prev => {
            const current = prev[product.id]?.quantity || 0;
            if (current >= product.quantity) {
                showToast('Достигнуто максимальное количество', 'info');
                return prev;
            }
            showToast('Добавлено в корзину');
            return { ...prev, [product.id]: { product, quantity: current + 1 } };
        });
    }, [showToast]);

    const toggleLike = useCallback(id => {
        setLiked(prev => (prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]));
    }, []);

    const clearLikes = useCallback(() => setLiked([]), []);

    const removeMissingLikes = useCallback(ids => {
        setLiked(prev => prev.filter(id => !ids.includes(id)));
    }, []);

    const cartCount = Object.values(cart).reduce((n, x) => n + x.quantity, 0);

    if (loading) {
        return (
            <div className="app-loading">
                <span className="logo-mark" aria-hidden="true">m</span>
                <p>Market загружается…</p>
            </div>
        );
    }

    return (
        <>
            <Layout cartCount={cartCount} favCount={liked.length}>
                <Routes>
                    <Route path="/" element={<Catalog add={add} liked={liked} onLike={toggleLike} />} />
                    <Route path="/login" element={<AuthPage />} />
                    <Route path="/register" element={<AuthPage registerMode />} />
                    <Route path="/product/:id" element={<ProductDetail add={add} />} />
                    <Route path="/cart" element={<Cart cart={cart} setCart={setCart} toast={showToast} />} />
                    <Route
                        path="/favorites"
                        element={
                            <Favorites
                                liked={liked}
                                onLike={toggleLike}
                                onAdd={add}
                                onClear={clearLikes}
                                onRemoveMissing={removeMissingLikes}
                            />
                        }
                    />
                    <Route path="/orders" element={user ? <Orders /> : <AuthPage />} />
                    <Route path="/profile" element={user ? <Profile /> : <AuthPage />} />
                    <Route path="/admin" element={user ? (isAdmin ? <Admin /> : <NoAccess />) : <AuthPage />} />
                    <Route
                        path="/admin/products"
                        element={user ? (isAdmin ? <AdminProducts /> : <NoAccess />) : <AuthPage />}
                    />
                    <Route
                        path="*"
                        element={
                            <main className="page-shell">
                                <div className="empty-state">
                                    <h1>Страница не найдена</h1>
                                    <p>Похоже, такой страницы не существует.</p>
                                    <Link to="/" className="button button-dark">На главную</Link>
                                </div>
                            </main>
                        }
                    />
                </Routes>
            </Layout>

            <Toast toast={toast} onClose={closeToast} />

            {isAdmin && (
                <div className="admin-shortcuts">
                    <Link to="/admin" title="Аналитика" aria-label="Аналитика">
                        <ChartNoAxesColumnIncreasing size={17} />
                    </Link>
                    <Link to="/admin/products" title="Управление товарами" aria-label="Управление товарами">
                        <Box size={17} />
                    </Link>
                </div>
            )}
        </>
    );
}
