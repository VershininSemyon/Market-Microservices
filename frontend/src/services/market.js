import { api } from '../config/api';

export const productsApi = {
    list: params => api.get('/products/', { params }).then(r => r.data),
    get: id => api.get(`/products/${id}`).then(r => r.data),
    create: data => api.post('/products/', data).then(r => r.data),
    update: (id, data) => api.put(`/products/${id}`, data).then(r => r.data),
    remove: id => api.delete(`/products/${id}`)
};

export const ordersApi = {
    list: () => api.get('/orders/').then(r => r.data),
    get: id => api.get(`/orders/${id}`).then(r => r.data),
    create: products => api.post('/orders/', { products }).then(r => r.data)
};

export const reviewsApi = {
    list: product_id => api.get('/reviews/', { params: { product_id } }).then(r => r.data),
    create: data => api.post('/reviews/', data).then(r => r.data),
    update: (id, data) => api.put(`/reviews/${id}`, data).then(r => r.data),
    remove: id => api.delete(`/reviews/${id}`)
};

export const userApi = {
    update: data => api.put('/auth/users/me', data),
    remove: () => api.delete('/auth/users/me')
};

export const analyticsApi = {
    stats: period => api.get('/analytics/stats', { params: { period } }).then(r => r.data)
};