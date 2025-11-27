'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import api from '@/lib/api';
import Button from '@/components/ui/Button';
import { FileText, Calendar, XCircle, ExternalLink, Loader2 } from 'lucide-react';

export default function DashboardPage() {
    const router = useRouter();
    const [userType, setUserType] = useState<string | null>(null);
    const [cotizaciones, setCotizaciones] = useState<any[]>([]);
    const [reservas, setReservas] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const type = localStorage.getItem('user_type');
        if (!type) {
            router.push('/login');
            return;
        }
        setUserType(type);

        if (type === 'CLIENTE') {
            fetchData();
        } else {
            setLoading(false);
        }
    }, []);

    const fetchData = async () => {
        try {
            const [cotRes, resRes] = await Promise.all([
                api.get('/cotizaciones/'),
                api.get('/reservas/')
            ]);
            setCotizaciones(cotRes.data.results || cotRes.data);
            setReservas(resRes.data.results || resRes.data);
        } catch (error) {
            console.error('Error cargando datos:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleCancelarReserva = async (id: string) => {
        if (!confirm('¿Estás seguro de que deseas cancelar esta reserva? Se procesará la devolución de la seña.')) return;

        try {
            await api.post(`/reservas/${id}/cancelar/`);
            fetchData(); // Recargar datos
            alert('Reserva cancelada exitosamente.');
        } catch (error) {
            console.error('Error cancelando reserva:', error);
            alert('No se pudo cancelar la reserva.');
        }
    };

    if (loading) {
        return (
            <div className="min-h-screen flex items-center justify-center">
                <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
            </div>
        );
    }

    // --- VISTA ADMINISTRADOR / VENDEDOR ---
    if (userType !== 'CLIENTE') {
        return (
            <div className="min-h-screen bg-gray-50 p-6">
                <div className="max-w-4xl mx-auto">
                    <h1 className="text-3xl font-bold text-gray-900 mb-6">Panel de Gestión</h1>

                    <div className="bg-white rounded-3xl p-8 shadow-sm border border-gray-100 text-center">
                        <div className="mb-6">
                            <h2 className="text-xl font-semibold mb-2">Administración del Sistema</h2>
                            <p className="text-gray-500">
                                Para gestionar vehículos, ventas y reportes, accede al panel administrativo de Django.
                            </p>
                        </div>

                        <a href="http://localhost:8000/admin" target="_blank" rel="noopener noreferrer">
                            <Button className="gap-2">
                                <ExternalLink className="w-4 h-4" />
                                Ir al Panel Administrativo
                            </Button>
                        </a>
                    </div>
                </div>
            </div>
        );
    }

    // --- VISTA CLIENTE (C.U. 07 y C.U. 06) ---
    return (
        <div className="min-h-screen bg-gray-50 p-6">
            <div className="max-w-6xl mx-auto space-y-8">
                <div className="flex items-center justify-between">
                    <h1 className="text-3xl font-bold text-gray-900">Mi Área Personal</h1>
                    <Button variant="outline" onClick={() => router.push('/')}>
                        Nuevo Vehículo
                    </Button>
                </div>

                {/* SECCIÓN RESERVAS */}
                <section>
                    <h2 className="text-xl font-bold text-gray-900 mb-4 flex items-center gap-2">
                        <Calendar className="w-5 h-5 text-blue-600" />
                        Mis Reservas
                    </h2>

                    {reservas.length === 0 ? (
                        <div className="bg-white p-8 rounded-3xl text-center text-gray-500 border border-gray-100">
                            No tienes reservas activas.
                        </div>
                    ) : (
                        <div className="grid gap-4">
                            {reservas.map((reserva) => (
                                <div key={reserva.id} className="bg-white p-6 rounded-2xl border border-gray-100 shadow-sm flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                                    <div>
                                        <div className="flex items-center gap-3 mb-1">
                                            <span className="font-mono font-bold text-gray-900">{reserva.nro_reserva}</span>
                                            <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${reserva.estado === 'ACTIVA' ? 'bg-green-100 text-green-700' :
                                                    reserva.estado === 'CANCELADA' ? 'bg-red-100 text-red-700' :
                                                        'bg-gray-100 text-gray-700'
                                                }`}>
                                                {reserva.estado}
                                            </span>
                                        </div>
                                        <p className="text-sm text-gray-500">
                                            Vence: {new Date(reserva.fecha_hora_vencimiento).toLocaleDateString()}
                                        </p>
                                        <p className="font-semibold mt-1">
                                            Seña pagada: ${Number(reserva.importe).toLocaleString('es-AR')}
                                        </p>
                                    </div>

                                    {reserva.estado === 'ACTIVA' && (
                                        <Button
                                            variant="outline"
                                            size="sm"
                                            onClick={() => handleCancelarReserva(reserva.id)}
                                            className="text-red-600 border-red-200 hover:bg-red-50 hover:border-red-300"
                                        >
                                            <XCircle className="w-4 h-4 mr-2" />
                                            Cancelar Reserva
                                        </Button>
                                    )}
                                </div>
                            ))}
                        </div>
                    )}
                </section>

                {/* SECCIÓN COTIZACIONES */}
                <section>
                    <h2 className="text-xl font-bold text-gray-900 mb-4 flex items-center gap-2">
                        <FileText className="w-5 h-5 text-blue-600" />
                        Historial de Cotizaciones
                    </h2>

                    {cotizaciones.length === 0 ? (
                        <div className="bg-white p-8 rounded-3xl text-center text-gray-500 border border-gray-100">
                            No has generado cotizaciones aún.
                        </div>
                    ) : (
                        <div className="grid gap-4">
                            {cotizaciones.map((cot) => (
                                <div key={cot.id} className="bg-white p-6 rounded-2xl border border-gray-100 shadow-sm">
                                    <div className="flex justify-between items-start mb-4">
                                        <div>
                                            <p className="text-sm text-gray-500">Cotización #{cot.id.slice(0, 8)}</p>
                                            <p className="text-xs text-gray-400">{new Date(cot.fecha_hora_generada).toLocaleDateString()}</p>
                                        </div>
                                        <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${cot.valida ? 'bg-blue-100 text-blue-700' : 'bg-gray-100 text-gray-600'}`}>
                                            {cot.valida ? 'Vigente' : 'Vencida/Usada'}
                                        </span>
                                    </div>

                                    {cot.vehiculos.map((v: any) => (
                                        <div key={v.id} className="mb-2">
                                            <p className="font-medium text-gray-900">{v.vehiculo_detalle.modelo_nombre}</p>
                                            <p className="text-sm text-gray-500">{v.vehiculo_detalle.marca_nombre} - {v.vehiculo_detalle.anio}</p>
                                        </div>
                                    ))}

                                    <div className="mt-4 pt-4 border-t border-gray-100 flex justify-between items-center">
                                        <span className="text-gray-600">Total Cotizado</span>
                                        <span className="text-lg font-bold text-gray-900">${Number(cot.importe_final).toLocaleString('es-AR')}</span>
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </section>
            </div>
        </div>
    );
}
