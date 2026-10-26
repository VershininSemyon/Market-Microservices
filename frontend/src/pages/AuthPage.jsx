import { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { ArrowLeft, ArrowRight, LockKeyhole, Leaf, ShieldCheck } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { errorMessage } from '../config/api';

export function AuthPage({ registerMode = false }) {
    const { login, register, user } = useAuth();
    const navigate = useNavigate();
    const [form, setForm] = useState({ username: '', email: '', password: '' });
    const [error, setError] = useState('');
    const [busy, setBusy] = useState(false);

    useEffect(() => {
        if (user) navigate('/');
    }, [user, navigate]);

    const change = e => setForm({ ...form, [e.target.name]: e.target.value });

    const submit = async e => {
        e.preventDefault();
        setBusy(true);
        setError('');
        try {
            if (registerMode) await register(form);
            else await login(form.username, form.password);
            navigate('/');
        } catch (e) {
            setError(errorMessage(e));
        } finally {
            setBusy(false);
        }
    };

    return (
        <main className="auth-page">
            <div className="auth-aside">
                <Link to="/" className="logo logo-light">
                    <span className="logo-mark"><Leaf /></span>
                    <span>market<span className="logo-dot">.</span></span>
                </Link>
                <div>
                    <div className="eyebrow">ХОРОШИЙ ВЫБОР НАЧИНАЕТСЯ ЗДЕСЬ</div>
                    <h1>
                        Меньше лишнего.
                        <br />
                        <em>Больше вашего.</em>
                    </h1>
                    <p>Войдите в свой аккаунт, чтобы заказывать любимые вещи и следить за покупками.</p>
                </div>
                <small>© 2026 Market</small>
            </div>
            <div className="auth-form-side">
                <div className="auth-form-wrap">
                    <Link to="/" className="back-link">
                        <ArrowLeft size={16} /> На главную
                    </Link>
                    <div className="auth-heading">
                        <span className="auth-symbol"><LockKeyhole /></span>
                        <h2>{registerMode ? 'Создать аккаунт' : 'С возвращением!'}</h2>
                        <p>
                            {registerMode
                                ? 'Присоединяйтесь к осознанным покупкам.'
                                : 'Рады видеть вас снова. Введите свои данные.'}
                        </p>
                    </div>
                    <form onSubmit={submit} className="form-stack">
                        {registerMode && (
                            <label className="form-field">
                                <span>Как к вам обращаться</span>
                                <input
                                    required
                                    name="username"
                                    value={form.username}
                                    onChange={change}
                                    placeholder="Ваше имя"
                                />
                            </label>
                        )}
                        {registerMode && (
                            <label className="form-field">
                                <span>Электронная почта</span>
                                <input
                                    required
                                    type="email"
                                    name="email"
                                    value={form.email}
                                    onChange={change}
                                    placeholder="you@example.com"
                                />
                            </label>
                        )}
                        {!registerMode && (
                            <label className="form-field">
                                <span>Имя пользователя</span>
                                <input
                                    required
                                    name="username"
                                    value={form.username}
                                    onChange={change}
                                    placeholder="Ваш логин"
                                    autoComplete="username"
                                />
                            </label>
                        )}
                        <label className="form-field">
                            <span>Пароль</span>
                            <input
                                required
                                minLength={registerMode ? 8 : 1}
                                type="password"
                                name="password"
                                value={form.password}
                                onChange={change}
                                placeholder={registerMode ? 'Не менее 8 символов' : 'Ваш пароль'}
                                autoComplete={registerMode ? 'new-password' : 'current-password'}
                            />
                        </label>
                        {error && <div className="form-error">{error}</div>}
                        <button disabled={busy} className="button button-dark button-wide">
                            {busy ? 'Подождите…' : registerMode ? 'Создать аккаунт' : 'Войти в аккаунт'}{' '}
                            <ArrowRight size={18} />
                        </button>
                    </form>
                    <p className="auth-switch">
                        {registerMode ? 'Уже есть аккаунт?' : 'Впервые у нас?'}{' '}
                        <Link to={registerMode ? '/login' : '/register'}>
                            {registerMode ? 'Войти' : 'Создать аккаунт'}
                        </Link>
                    </p>
                    <div className="secure-note">
                        <ShieldCheck size={16} /> Ваши данные надёжно защищены
                    </div>
                </div>
            </div>
        </main>
    );
}

export default AuthPage;