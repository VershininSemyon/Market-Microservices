
import { Link } from 'react-router-dom';
import { Heart, Plus } from 'lucide-react';
import { money, productInitial, toneClass } from '../shared';

export function ProductCard({ product, index = 0, onAdd, liked, onLike }) {
    const inStock = product.quantity > 0;

    return (
        <article className="product-card" style={{ animationDelay: `${Math.min(index, 7) * 45}ms` }}>
            <div className="card-top">
                <span className="card-index">
                    <span className="card-number">{String(index + 1).padStart(2, '0')}</span>
                    <span className={inStock ? 'stock-dot' : 'stock-dot is-empty'} aria-hidden="true" />
                    {inStock ? 'В наличии' : 'Нет в наличии'}
                </span>
                <button
                    className={liked ? 'like-button liked' : 'like-button'}
                    onClick={() => onLike(product.id)}
                    aria-label={liked ? 'Убрать из избранного' : 'Добавить в избранное'}
                    aria-pressed={liked}
                    title={liked ? 'Убрать из избранного' : 'Добавить в избранное'}
                >
                    <Heart size={16} fill={liked ? 'currentColor' : 'none'} />
                </button>
            </div>

            <Link to={`/product/${product.id}`} className="product-name">
                <span className={`product-monogram ${toneClass(product)}`} aria-hidden="true">
                    {productInitial(product)}
                </span>
                <span className="product-name-text">{product.name}</span>
            </Link>

            <p className="product-description">
                {product.description || 'Вещь без лишнего шума: понятная, практичная и на каждый день.'}
            </p>

            <div className="product-bottom">
                <div>
                    <strong>{money(product.price)}</strong>
                    <span className="product-stock">
                        {inStock ? `Осталось ${product.quantity} шт.` : 'Поступление ожидается'}
                    </span>
                </div>
                <button
                    disabled={!inStock}
                    className="add-button"
                    onClick={() => onAdd(product)}
                    aria-label={`Добавить «${product.name}» в корзину`}
                    title={inStock ? 'Добавить в корзину' : 'Нет в наличии'}
                >
                    <Plus size={17} />
                </button>
            </div>
        </article>
    );
}

export default ProductCard;
