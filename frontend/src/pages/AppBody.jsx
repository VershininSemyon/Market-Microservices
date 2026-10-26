import { useState, useEffect } from 'react';
import { Routes, Route, Link } from 'react-router-dom';
import { Leaf, Box, ChartNoAxesColumnIncreasing } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import Layout from '../components/Layout';
import Toast from '../components/Toast';
import Catalog from './Catalog';
import AuthPage from './AuthPage';
import ProductDetail from './ProductDetail';
import Cart from './Cart';
import Orders from './Orders';
import Profile from './Profile';
import Admin from './Admin';
import AdminProducts from './AdminProducts';

export default function AppBody() {
    const { user, loading } = useAuth();
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
    const [toastMessage, setToastMessage] = useState('');

    useEffect(() => localStorage.setItem('market_cart', JSON.stringify(cart)), [cart]);
    useEffect(() => localStorage.setItem('market_liked', JSON.stringify(liked)), [liked]);

    const toast = m => setToastMessage(m);

    const add = product => {
        if (!product.quantity) {
            toast('Товар закончился');
            return;
        }
        setCart(prev => {
            const current = prev[product.id]?.quantity || 0;
            if (current >= product.quantity) {
                toast('Достигнуто максимальное количество');
                return prev;
            }
            toast('Добавлено в корзину');
            return { ...prev, [product.id]: { product, quantity: current + 1 } };
        });
    };

    const toggleLike = id => setLiked(prev => (prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]));
    const cartCount = Object.values(cart).reduce((n, x) => n + x.quantity, 0);

    if (loading) {
        return (
            <div className="app-loading">
                <span className="logo-mark"><Leaf /></span>
                <p>Market загружается…</p>
            </div>
        );
    }

    return (
        <>
            <Layout cartCount={cartCount}>
                <Routes>
                    <Route path="/" element={<Catalog add={add} liked={liked} onLike={toggleLike} />} />
                    <Route path="/login" element={<AuthPage />} />
                    <Route path="/register" element={<AuthPage registerMode />} />
                    <Route path="/product/:id" element={<ProductDetail add={add} />} />
                    <Route path="/cart" element={<Cart cart={cart} setCart={setCart} add={add} toast={toast} />} />
                    <Route path="/orders" element={user ? <Orders /> : <AuthPage />} />
                    <Route path="/profile" element={user ? <Profile /> : <AuthPage />} />
                    <Route path="/admin" element={user ? <Admin /> : <AuthPage />} />
                    <Route path="/admin/products" element={user ? <AdminProducts /> : <AuthPage />} />
                    <Route
                        path="*"
                        element={
                            <main className="page-shell empty-state">
                                <h1>Страница не найдена</h1>
                                <Link to="/" className="button button-dark">
                                    На главную
                                </Link>
                            </main>
                        }
                    />
                </Routes>
            </Layout>
            <Toast message={toastMessage} onClose={() => setToastMessage('')} />
            {user && (
                <div className="admin-shortcuts">
                    <Link to="/admin" title="Аналитика">
                        <ChartNoAxesColumnIncreasing size={17} />
                    </Link>
                    <Link to="/admin/products" title="Управление товарами">
                        <Box size={17} />
                    </Link>
                </div>
            )}
        </>
    );
}