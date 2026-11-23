
import { useState } from 'react';
import { Link, NavLink, useLocation, useNavigate } from 'react-router-dom';
import { Heart, ShoppingBag, LogIn, LogOut, Menu, X } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';

export function Header({ cartCount, favCount }) {
    const { user, logout } = useAuth();
    const [open, setOpen] = useState(false);
    const navigate = useNavigate();
    const location = useLocation();

    const goToSection = id => e => {
        e.preventDefault();
        setOpen(false);
        const scroll = () => document.getElementById(id)?.scrollIntoView({ behavior: 'smooth', block: 'start' });
        if (location.pathname !== '/') {
            navigate('/');
            window.setTimeout(scroll, 120);
        } else {
            scroll();
        }
    };

    const handleLogout = () => {
        setOpen(false);
        logout();
        navigate('/');
    };

    return (
        <header className="header">
            <div className="header-inner">
                <Link to="/" className="logo" onClick={() => setOpen(false)}>
                    <span className="logo-mark" aria-hidden="true">m</span>
                    <span>market<span className="logo-dot">.</span></span>
                </Link>

                <nav className={open ? 'nav nav-open' : 'nav'} aria-label="Основная навигация">
                    <NavLink to="/" end onClick={() => setOpen(false)}>Каталог</NavLink>
                    <a href="/#benefits" onClick={goToSection('benefits')}>Почему мы</a>
                    {user && <NavLink to="/orders" onClick={() => setOpen(false)}>Мои заказы</NavLink>}
                    {user && (
                        <NavLink to="/profile" className="nav-mobile-only" onClick={() => setOpen(false)}>
                            Профиль
                        </NavLink>
                    )}
                    {user && (
                        <button className="nav-logout nav-mobile-only" onClick={handleLogout}>
                            <LogOut size={15} /> Выйти
                        </button>
                    )}
                </nav>

                <div className="header-actions">
                    <Link
                        to="/favorites"
                        className="icon-button"
                        aria-label={favCount > 0 ? `Избранное: ${favCount}` : 'Избранное'}
                        title="Избранное"
                    >
                        <Heart size={18} />
                        {favCount > 0 && <span className="cart-count fav-count">{favCount}</span>}
                    </Link>
                    <Link
                        to="/cart"
                        className="icon-button"
                        aria-label={cartCount > 0 ? `Корзина: ${cartCount} товаров` : 'Корзина'}
                        title="Корзина"
                    >
                        <ShoppingBag size={18} />
                        {cartCount > 0 && <span className="cart-count">{cartCount}</span>}
                    </Link>

                    {user ? (
                        <div className="user-menu">
                            <Link className="avatar" to="/profile" title="Профиль">
                                {(user.username || 'U').slice(0, 1).toUpperCase()}
                            </Link>
                            <button className="logout-btn" onClick={handleLogout} title="Выйти" aria-label="Выйти">
                                <LogOut size={16} />
                            </button>
                        </div>
                    ) : (
                        <Link to="/login" className="button button-dark button-small">
                            <LogIn size={15} /> Войти
                        </Link>
                    )}

                    <button
                        className="mobile-menu"
                        onClick={() => setOpen(!open)}
                        aria-label={open ? 'Закрыть меню' : 'Открыть меню'}
                        aria-expanded={open}
                    >
                        {open ? <X size={20} /> : <Menu size={20} />}
                    </button>
                </div>
            </div>
        </header>
    );
}

export default Header;
