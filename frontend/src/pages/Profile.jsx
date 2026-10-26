import { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { errorMessage } from '../config/api';
import { userApi } from '../services/market';

export function Profile() {
    const { user, setUser, logout } = useAuth();
    const [form, setForm] = useState({ username: user?.username || '', email: user?.email || '' });
    const [message, setMessage] = useState('');
    const [error, setError] = useState('');

    useEffect(() => {
        setForm({ username: user?.username || '', email: user?.email || '' });
    }, [user]);

    if (!user) return null;

    const save = async e => {
        e.preventDefault();
        try {
            const { data } = await userApi.update(form);
            setUser(data);
            setMessage('Профиль обновлён');
            setError('');
        } catch (e) {
            setError(errorMessage(e));
        }
    };

    const remove = async () => {
        if (!confirm('Удалить аккаунт без возможности восстановления?')) return;
        try {
            await userApi.remove();
            logout();
        } catch (e) {
            setError(errorMessage(e));
        }
    };

    return (
        <main className="page-shell">
            <div className="eyebrow">ВАШ АККАУНТ</div>
            <h1 className="page-heading">
                Личный <em>профиль.</em>
            </h1>
            <div className="profile-layout">
                <div className="profile-card">
                    <div className="profile-avatar">{user.username.slice(0, 1).toUpperCase()}</div>
                    <h2>{user.username}</h2>
                    <p>{user.email}</p>
                    <small>С нами с {new Date(user.registration_date).toLocaleDateString('ru-RU')}</small>
                </div>
                <form className="profile-form" onSubmit={save}>
                    <h3>Личные данные</h3>
                    <label className="form-field">
                        <span>Имя пользователя</span>
                        <input
                            required
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
                    <button className="button button-dark">Сохранить изменения</button>
                    <button type="button" className="text-danger account-delete" onClick={remove}>
                        Удалить аккаунт
                    </button>
                </form>
            </div>
        </main>
    );
}

export default Profile;