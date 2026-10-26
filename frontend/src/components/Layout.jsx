import { Link } from 'react-router-dom';
import { Leaf, Truck, ShieldCheck, RefreshCw } from 'lucide-react';
import Header from './Header';

export function Layout({ children, cartCount }) {
    return (
        <>
            <Header cartCount={cartCount} />
            {children}
            <footer className="footer" id="benefits">
                <div className="footer-inner">
                    <Link to="/" className="logo">
                        <span className="logo-mark"><Leaf size={20} /></span>
                        <span>market<span className="logo-dot">.</span></span>
                    </Link>
                    <p>Вещи, которые делают каждый день лучше.</p>
                    <div className="footer-perks">
                        <span><Truck size={16} /> Быстрая доставка</span>
                        <span><ShieldCheck size={16} /> Безопасная покупка</span>
                        <span><RefreshCw size={16} /> Лёгкий возврат</span>
                    </div>
                    <small>© 2026 Market. Покупайте осознанно.</small>
                </div>
            </footer>
        </>
    );
}

export default Layout;