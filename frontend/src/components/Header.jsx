import { useState } from 'react';
import { Link, NavLink } from 'react-router-dom';
import { Leaf, ShoppingBag, LogIn, LogOut, Menu, X } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';

export function Header({ cartCount }) {
    const { user, logout } = useAuth();
    const [open, setOpen] = useState(false);

    return (
        <header className="header">
            <div className="header-inner">
                <Link to="/" className="logo">
                    <span className="logo-mark"><Leaf size={21} /></span>
                    <span>market<span className="logo-dot">.</span></span>
                </Link>
                <nav className={open ? 'nav nav-open' : 'nav'}>
                    <NavLink to="/" onClick={() => setOpen(false)}>Каталог</NavLink>
                    <a href="/#benefits" onClick={() => setOpen(false)}>Почему мы</a>
                    {user && <NavLink to="/orders" onClick={() => setOpen(false)}>Мои заказы</NavLink>}
                </nav>
                <div className="header-actions">
                    <Link to="/cart" className="icon-button cart-button" aria-label="Корзина">
                        <ShoppingBag size={20} />
                        {cartCount > 0 && <span className="cart-count">{cartCount}</span>}
                    </Link>
                    {user ? (
                        <div className="user-menu">
                            <Link className="avatar" to="/profile">
                                {(user.username || 'U').slice(0, 1).toUpperCase()}
                            </Link>
                            <button className="logout-btn" onClick={logout} title="Выйти">
                                <LogOut size={17} />
                            </button>
                        </div>
                    ) : (
                        <Link to="/login" className="button button-dark button-small">
                            <LogIn size={16} /> Войти
                        </Link>
                    )}
                    <button className="mobile-menu" onClick={() => setOpen(!open)} aria-label="Меню">
                        {open ? <X /> : <Menu />}
                    </button>
                </div>
            </div>
        </header>
    );
}

export default Header;