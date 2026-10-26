import { useState, useEffect } from 'react';
import { RefreshCw, Trash2 } from 'lucide-react';
import { errorMessage } from '../config/api';
import { productsApi } from '../services/market';
import { money } from '../shared';

export function AdminProducts() {
    const [products, setProducts] = useState([]);
    const [error, setError] = useState('');
    const [form, setForm] = useState({ name: '', description: '', price: '', quantity: '' });
    const [edit, setEdit] = useState(null);
    const [message, setMessage] = useState('');

    const load = () =>
        productsApi
            .list({ limit: 100 })
            .then(setProducts)
            .catch(e => setError(errorMessage(e)));

    useEffect(() => {
        load();
    }, []);

    const submit = async e => {
        e.preventDefault();
        const data = { ...form, price: Number(form.price), quantity: Number(form.quantity) };
        try {
            if (edit) await productsApi.update(edit, data);
            else await productsApi.create(data);
            setForm({ name: '', description: '', price: '', quantity: '' });
            setEdit(null);
            setMessage('Каталог обновлён');
            setError('');
            load();
        } catch (e) {
            setError(errorMessage(e));
        }
    };

    return (
        <main className="page-shell">
            <div className="eyebrow">ТОВАРЫ</div>
            <h1 className="page-heading">Управление <em>каталогом.</em></h1>
            <div className="admin-products-layout">
                <form className="profile-form" onSubmit={submit}>
                    <h3>{edit ? 'Редактировать товар' : 'Добавить товар'}</h3>
                    {[
                        ['name', 'Название'],
                        ['description', 'Описание'],
                        ['price', 'Цена'],
                        ['quantity', 'Количество']
                    ].map(([k, label]) => (
                        <label className="form-field" key={k}>
                            <span>{label}</span>
                            <input
                                required={k !== 'description'}
                                type={['price', 'quantity'].includes(k) ? 'number' : 'text'}
                                min={k === 'price' ? '0.01' : k === 'quantity' ? '0' : undefined}
                                value={form[k]}
                                onChange={e => setForm({ ...form, [k]: e.target.value })}
                            />
                        </label>
                    ))}
                    {error && <p className="form-error">{error}</p>}
                    {message && <p className="success-text">{message}</p>}
                    <button className="button button-dark button-wide">
                        {edit ? 'Сохранить' : 'Создать товар'}
                    </button>
                    {edit && (
                        <button
                            type="button"
                            className="button button-outline button-wide"
                            onClick={() => {
                                setEdit(null);
                                setForm({ name: '', description: '', price: '', quantity: '' });
                            }}
                        >
                            Отмена
                        </button>
                    )}
                </form>
                <div className="admin-product-list">
                    {products.map(p => (
                        <article key={p.id} className="admin-product-row">
                            <div>
                                <b>{p.name}</b>
                                <small>
                                    {money(p.price)} · Остаток: {p.quantity}
                                </small>
                            </div>
                            <div className="admin-row-actions">
                                <button
                                    onClick={() => {
                                        setEdit(p.id);
                                        setForm({
                                            name: p.name,
                                            description: p.description || '',
                                            price: String(p.price),
                                            quantity: String(p.quantity)
                                        });
                                    }}
                                    title="Редактировать"
                                >
                                    <RefreshCw size={16} />
                                </button>
                                <button
                                    onClick={async () => {
                                        if (confirm('Удалить товар?')) {
                                            try {
                                                await productsApi.remove(p.id);
                                                load();
                                            } catch (e) {
                                                setError(errorMessage(e));
                                            }
                                        }
                                    }}
                                    title="Удалить"
                                >
                                    <Trash2 size={16} />
                                </button>
                            </div>
                        </article>
                    ))}
                </div>
            </div>
        </main>
    );
}

export default AdminProducts;