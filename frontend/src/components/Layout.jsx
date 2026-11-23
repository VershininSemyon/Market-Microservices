
import { Link } from 'react-router-dom';
import { Truck, ShieldCheck, RotateCcw } from 'lucide-react';
import Header from './Header';

export function Layout({ children, cartCount, favCount }) {
    return (
        <>
            <Header cartCount={cartCount} favCount={favCount} />
            {children}
            <footer className="footer" id="benefits">
                <div className="footer-inner">
                    <Link to="/" className="logo logo-light">
                        <span className="logo-mark" aria-hidden="true">m</span>
                        <span>market<span className="logo-dot">.</span></span>
                    </Link>
                    <p>Небольшой маркетплейс с ручным отбором. Меньше шума — больше смысла.</p>
                    <div className="footer-perks">
                        <span><Truck size={15} /> Статус заказа — в личном кабинете</span>
                        <span><ShieldCheck size={15} /> Данные аккаунта под защитой</span>
                        <span><RotateCcw size={15} /> История покупок всегда под рукой</span>
                    </div>
                    <small>© 2026 Market — меньше, но лучше.</small>
                </div>
            </footer>
        </>
    );
}

export default Layout;
