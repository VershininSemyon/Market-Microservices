import { Link } from 'react-router-dom';
import { Heart, Plus } from 'lucide-react';
import { money, imageFor } from '../shared';

export function ProductCard({ product, index, onAdd, liked, onLike }) {
    return (
        <article className="product-card">
            <div className="product-image-wrap">
                <Link to={`/product/${product.id}`} className="product-image">
                    <img src={imageFor(product, index)} alt={product.name} loading="lazy" />
                    <span className="image-chip">{product.quantity > 0 ? 'В наличии' : 'Нет в наличии'}</span>
                </Link>
                <button
                    className={liked ? 'like-button liked' : 'like-button'}
                    onClick={() => onLike(product.id)}
                    aria-label="В избранное"
                >
                    <Heart size={18} fill={liked ? 'currentColor' : 'none'} />
                </button>
            </div>
            <div className="product-info">
                <Link to={`/product/${product.id}`} className="product-name">{product.name}</Link>
                <p className="product-description">{product.description || 'Качество, продуманное до мелочей.'}</p>
                <div className="product-bottom">
                    <div>
                        <strong>{money(product.price)}</strong>
                        <span className="product-stock">
                            {product.quantity > 0 ? `Осталось ${product.quantity} шт.` : 'Временно нет'}
                        </span>
                    </div>
                    <button
                        disabled={product.quantity < 1}
                        className="add-button"
                        onClick={() => onAdd(product)}
                        aria-label="Добавить в корзину"
                    >
                        <Plus size={20} />
                    </button>
                </div>
            </div>
        </article>
    );
}

export default ProductCard;