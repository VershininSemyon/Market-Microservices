import { useEffect } from 'react';
import { Check, X } from 'lucide-react';

export function Toast({ message, onClose }) {
    useEffect(() => {
        if (!message) return;
        const t = setTimeout(onClose, 3200);
        return () => clearTimeout(t);
    }, [message, onClose]);

    return message ? (
        <div className="toast">
            <Check size={18} />
            <span>{message}</span>
            <button onClick={onClose}><X size={16} /></button>
        </div>
    ) : null;
}

export default Toast;