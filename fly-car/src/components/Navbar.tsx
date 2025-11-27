'use client';

import Link from 'next/link';
import { useState, useEffect } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import Button from './ui/Button';
import { User, LogOut, Car } from 'lucide-react';

export default function Navbar() {
    const router = useRouter();
    const pathname = usePathname();
    const [isLoggedIn, setIsLoggedIn] = useState(false);
    const [userType, setUserType] = useState<string | null>(null);

    // Verificar estado de login al montar y cuando cambie la ruta
    useEffect(() => {
        const checkLogin = () => {
            const token = localStorage.getItem('access_token');
            const type = localStorage.getItem('user_type');
            setIsLoggedIn(!!token);
            setUserType(type);
        };

        checkLogin();

        // Escuchar evento de almacenamiento para sincronizar pestañas o cambios
        window.addEventListener('storage', checkLogin);
        return () => window.removeEventListener('storage', checkLogin);
    }, [pathname]);

    const handleLogout = () => {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('user_type');
        setIsLoggedIn(false);
        setUserType(null);
        router.push('/login');
        router.refresh();
    };

    return (
        <nav className="bg-white border-b border-gray-100 sticky top-0 z-40">
            <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
                {/* Logo */}
                <Link href="/" className="flex items-center gap-2 font-bold text-xl text-gray-900">
                    <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center text-white">
                        <Car className="w-5 h-5" />
                    </div>
                    FLY CAR
                </Link>

                {/* Menú */}
                <div className="flex items-center gap-4">
                    {isLoggedIn ? (
                        <>
                            <div className="hidden md:flex items-center gap-2 text-sm text-gray-600 bg-gray-50 px-3 py-1.5 rounded-full mr-2">
                                <User className="w-4 h-4" />
                                <span>{userType === 'CLIENTE' ? 'Cliente' : 'Usuario'}</span>
                            </div>

                            <Link href="/dashboard">
                                <Button variant="ghost" size="sm" className="text-gray-700 hover:bg-gray-100">
                                    Mi Cuenta
                                </Button>
                            </Link>

                            <Button
                                variant="ghost"
                                size="sm"
                                onClick={handleLogout}
                                className="text-red-600 hover:text-red-700 hover:bg-red-50"
                            >
                                <LogOut className="w-4 h-4 mr-2" />
                                Salir
                            </Button>
                        </>
                    ) : (
                        <>
                            <Link href="/login">
                                <Button variant="ghost" size="sm">Iniciar Sesión</Button>
                            </Link>
                            <Link href="/registro">
                                <Button variant="primary" size="sm">Registrarse</Button>
                            </Link>
                        </>
                    )}
                </div>
            </div>
        </nav>
    );
}
