import { useEffect, useMemo, useState } from 'react';
import { Link, NavLink, Route, Routes, useNavigate, useParams, useSearchParams } from 'react-router-dom';
import {
    ArrowDownUp, ArrowLeft, ArrowRight, ArrowUpRight, Check, ChevronDown, ChevronLeft, ChevronRight,
    Heart, Leaf, LockKeyhole, LogIn, LogOut, Menu, Minus, Package, Plus, Search, ShieldCheck,
    ShoppingBag, SlidersHorizontal, Star, Trash2, Truck, UserRound, X, Zap, LayoutDashboard,
    ChartNoAxesColumnIncreasing, Box, RefreshCw
} from 'lucide-react';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { api, errorMessage } from './config/api';
import { productsApi, ordersApi, reviewsApi, userApi, analyticsApi } from './services/market';

export const money = (n) => new Intl.NumberFormat('ru-RU', {
    style: 'currency',
    currency: 'RUB',
    maximumFractionDigits: 0
}).format(Number(n) || 0);

export const demoImages = [
    'https://images.unsplash.com/photo-1505740420928-5e560c06d30e?auto=format&fit=crop&w=900&q=85',
    'https://images.unsplash.com/photo-1523275335684-37898b6baf30?auto=format&fit=crop&w=900&q=85',
    'https://images.unsplash.com/photo-1542291026-7eec264c27ff?auto=format&fit=crop&w=900&q=85',
    'https://images.unsplash.com/photo-1526170375885-4d8ecf77b99f?auto=format&fit=crop&w=900&q=85',
    'https://images.unsplash.com/photo-1541643600914-78b084683601?auto=format&fit=crop&w=900&q=85',
    'https://images.unsplash.com/photo-1526170315874-1d8b5a7d6e6e?auto=format&fit=crop&w=900&q=85'
];

export const imageFor = (p, i = 0) => p?.image_url || p?.image || demoImages[i % demoImages.length];

export {
    useEffect, useMemo, useState, Link, NavLink, Route, Routes, useNavigate, useParams, useSearchParams,
    ArrowDownUp, ArrowLeft, ArrowRight, ArrowUpRight, Check, ChevronDown, ChevronLeft, ChevronRight,
    Heart, Leaf, LockKeyhole, LogIn, LogOut, Menu, Minus, Package, Plus, Search, ShieldCheck,
    ShoppingBag, SlidersHorizontal, Star, Trash2, Truck, UserRound, X, Zap, LayoutDashboard,
    ChartNoAxesColumnIncreasing, Box, RefreshCw, AuthProvider, useAuth, api, errorMessage,
    productsApi, ordersApi, reviewsApi, userApi, analyticsApi
};