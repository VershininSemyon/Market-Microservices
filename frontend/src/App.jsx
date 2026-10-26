import { AuthProvider } from './contexts/AuthContext';
import AppBody from './pages/AppBody';

export default function App() {
    return (
        <AuthProvider>
            <AppBody />
        </AuthProvider>
    );
}