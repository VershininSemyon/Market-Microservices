
import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { LogOut, Trash2 } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { errorMessage } from '../config/api';
import { userApi } from '../services/market';
import { formatDate } from '../shared';

export function Profile() {
    const { user, setUser, logout, isAdmin } = useAuth();
    const navigate = useNavigate();
    const [form, setForm] = useState({ username: user?.username || '', email: user?.email || '' });
    const [message, setMessage] = useState('');
    const [error, setError] = useState('');
    const [busy, setBusy] = useState(false);

    useEffect(() => {
        setForm({ username: user?.username || '', email: user?.email || '' });
    }, [user]);

    if (!user) return null;

    const save = async e => {
        e.preventDefault();
        setBusy(true);
        try {
            const { data } = await userApi.update(form);
            setUser(data);
            setMessage('Профиль обновлён');
            setError('');
        } catch (e) {
            setError(errorMessage(e));
            setMessage('');
        } finally {
            setBusy(false);
        }
    };

    const remove = async () => {
        if (!window.confirm('Удалить аккаунт без возможности восстановления?')) return;
        try {
            await userApi.remove();
            logout();
            navigate('/');
        } catch (e) {
            setError(errorMessage(e));
        }
    };

    const handleLogout = () => {
        logout();
        navigate('/');
    };

    return (
        <main className="page-shell">
            <div className="eyebrow">Ваш аккаунт</div>
            <h1 className="page-heading">
                Личный <em>профиль.</em>
            </h1>

            <div className="profile-layout">
                <div className="profile-card">
                    <div className="profile-avatar">{user.username.slice(0, 1).toUpperCase()}</div>
                    <h2>{user.username}</h2>
                    <p>{user.email}</p>
                    {isAdmin && <span className="profile-role">Администратор</span>}
                    <small>С нами с {formatDate(user.registration_date)}</small>
                </div>

                <form className="profile-form" onSubmit={save}>
                    <h3>Личные данные</h3>
                    <label className="form-field">
                        <span>Имя пользователя</span>
                        <input
                            required
                            maxLength={100}
                            value={form.username}
                            onChange={e => setForm({ ...form, username: e.target.value })}
                        />
                    </label>
                    <label className="form-field">
                        <span>Электронная почта</span>
                        <input
                            required
                            type="email"
                            value={form.email}
                            onChange={e => setForm({ ...form, email: e.target.value })}
                        />
                    </label>
                    {message && <p className="success-text">{message}</p>}
                    {error && <p className="form-error">{error}</p>}
                    <button className="button button-dark" disabled={busy}>
                        {busy ? 'Сохраняем…' : 'Сохранить изменения'}
                    </button>
                    <div className="profile-actions">
                        <button type="button" className="text-button" onClick={handleLogout}>
                            <LogOut size={14} /> Выйти из аккаунта
                        </button>
                        <button type="button" className="text-button text-danger" onClick={remove}>
                            <Trash2 size={14} /> Удалить аккаунт
                        </button>
                    </div>
                </form>
            </div>
        </main>
    );
}

export default Profile;
