
import { useState, useEffect, useCallback } from 'react';
import { Pencil, Trash2, Search } from 'lucide-react';
import { errorMessage } from '../config/api';
import { productsApi } from '../services/market';
import { money, formatDate } from '../shared';

const EMPTY_FORM = { name: '', description: '', price: '', quantity: '' };

const FIELDS = [
    ['name', 'Название', 'text'],
    ['description', 'Описание', 'text'],
    ['price', 'Цена, ₽', 'number'],
    ['quantity', 'Количество, шт.', 'number']
];

export function AdminProducts() {
    const [products, setProducts] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [form, setForm] = useState(EMPTY_FORM);
    const [edit, setEdit] = useState(null);
    const [message, setMessage] = useState('');
    const [busy, setBusy] = useState(false);
    const [search, setSearch] = useState('');

    const load = useCallback(() => {
        setLoading(true);
        return productsApi
            .list({ limit: 100, order_by: 'name', order: 'asc' })
            .then(data => {
                setProducts(data);
                setError('');
            })
            .catch(e => setError(errorMessage(e)))
            .finally(() => setLoading(false));
    }, []);

    useEffect(() => {
        load();
    }, [load]);

    const resetForm = () => {
        setEdit(null);
        setForm(EMPTY_FORM);
    };

    const submit = async e => {
        e.preventDefault();
        setBusy(true);
        const data = {
            name: form.name,
            description: form.description || null,
            price: Number(form.price),
            quantity: Number(form.quantity)
        };
        try {
            if (edit) await productsApi.update(edit, data);
            else await productsApi.create(data);
            resetForm();
            setMessage(edit ? 'Товар обновлён' : 'Товар добавлен в каталог');
            await load();
        } catch (e) {
            setError(errorMessage(e));
            setMessage('');
        } finally {
            setBusy(false);
        }
    };

    const startEdit = p => {
        setEdit(p.id);
        setForm({
            name: p.name,
            description: p.description || '',
            price: String(p.price),
            quantity: String(p.quantity)
        });
        setMessage('');
        window.scrollTo({ top: 0, behavior: 'smooth' });
    };

    const remove = async p => {
        if (!window.confirm(`Удалить товар «${p.name}»? Отзывы на него тоже будут удалены.`)) return;
        try {
            await productsApi.remove(p.id);
            if (edit === p.id) resetForm();
            setMessage('Товар удалён');
            await load();
        } catch (e) {
            setError(errorMessage(e));
            setMessage('');
        }
    };

    const filtered = products.filter(p => p.name.toLowerCase().includes(search.trim().toLowerCase()));

    return (
        <main className="page-shell">
            <div className="eyebrow">Товары</div>
            <h1 className="page-heading">
                Управление <em>каталогом.</em>
            </h1>

            <div className="admin-products-layout">
                <form className="profile-form" onSubmit={submit}>
                    <h3>{edit ? 'Редактировать товар' : 'Добавить товар'}</h3>
                    {FIELDS.map(([key, label, type]) => (
                        <label className="form-field" key={key}>
                            <span>{label}</span>
                            <input
                                required={key !== 'description'}
                                type={type}
                                min={key === 'price' ? '0.01' : key === 'quantity' ? '0' : undefined}
                                step={key === 'price' ? '0.01' : key === 'quantity' ? '1' : undefined}
                                maxLength={key === 'name' ? 200 : undefined}
                                value={form[key]}
                                onChange={e => setForm({ ...form, [key]: e.target.value })}
                            />
                        </label>
                    ))}
                    {error && <p className="form-error">{error}</p>}
                    {message && <p className="success-text">{message}</p>}
                    <button className="button button-dark button-wide" disabled={busy}>
                        {busy ? 'Сохраняем…' : edit ? 'Сохранить изменения' : 'Создать товар'}
                    </button>
                    {edit && (
                        <button
                            type="button"
                            className="button button-outline button-wide"
                            onClick={resetForm}
                            style={{ marginTop: 10 }}
                        >
                            Отмена
                        </button>
                    )}
                </form>

                <div>
                    <label className="search-box admin-search">
                        <Search size={17} />
                        <input
                            value={search}
                            onChange={e => setSearch(e.target.value)}
                            placeholder="Найти товар по названию…"
                            aria-label="Поиск товара в списке"
                        />
                    </label>
                    <p className="admin-list-meta">
                        {loading ? 'Загружаем каталог…' : `${filtered.length} из ${products.length} товаров`}
                    </p>

                    {loading ? (
                        <div className="admin-product-list">
                            {[1, 2, 3, 4].map(i => (
                                <div className="skeleton-card" key={i}>
                                    <span className="sk-line" />
                                    <span className="sk-line short" />
                                </div>
                            ))}
                        </div>
                    ) : !filtered.length ? (
                        <div className="admin-empty">
                            {products.length
                                ? 'По этому запросу ничего не найдено.'
                                : 'Каталог пуст — добавьте первый товар слева.'}
                        </div>
                    ) : (
                        <div className="admin-product-list">
                            {filtered.map(p => (
                                <article key={p.id} className="admin-product-row">
                                    <div>
                                        <b>{p.name}</b>
                                        <small>
                                            {money(p.price)} ·{' '}
                                            {p.quantity > 0 ? (
                                                <>остаток: {p.quantity}</>
                                            ) : (
                                                <span className="is-empty">нет в наличии</span>
                                            )}{' '}
                                            · с {formatDate(p.created_at)}
                                        </small>
                                    </div>
                                    <div className="admin-row-actions">
                                        <button onClick={() => startEdit(p)} title="Редактировать" aria-label={`Редактировать «${p.name}»`}>
                                            <Pencil size={15} />
                                        </button>
                                        <button onClick={() => remove(p)} title="Удалить" aria-label={`Удалить «${p.name}»`}>
                                            <Trash2 size={15} />
                                        </button>
                                    </div>
                                </article>
                            ))}
                        </div>
                    )}
                </div>
            </div>
        </main>
    );
}

export default AdminProducts;
