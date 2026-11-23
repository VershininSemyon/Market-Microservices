
import { useEffect } from 'react';
import { Check, AlertCircle, Info, X } from 'lucide-react';

const ICONS = { success: Check, error: AlertCircle, info: Info };

export function Toast({ toast, onClose }) {
    const { message, type = 'success', action } = toast || {};

    useEffect(() => {
        if (!message) return;
        const timer = setTimeout(onClose, action ? 6000 : 3400);
        return () => clearTimeout(timer);
    }, [message, type, action, onClose]);

    if (!message) return null;

    const Icon = ICONS[type] || Check;

    return (
        <div className={`toast toast-${type}`} role="status" aria-live="polite">
            <Icon size={17} />
            <span>{message}</span>
            {action && (
                <button
                    className="toast-action"
                    onClick={() => {
                        action.onClick();
                        onClose();
                    }}
                >
                    {action.label}
                </button>
            )}
            <button className="toast-close" onClick={onClose} aria-label="Закрыть уведомление">
                <X size={15} />
            </button>
        </div>
    );
}

export default Toast;
