'use client';

import { useState, useEffect } from 'react';
import api from '@/lib/api';
import Button from './ui/Button';
import { Check, Plus, Loader2, CreditCard } from 'lucide-react';
import { useRouter } from 'next/navigation';

interface Vehiculo {
    id: string;
    modelo_nombre: string;
    marca_nombre: string;
    precio: number;
    modelo: number;
}

interface Accesorio {
    id: string;
    nombre: string;
    precio: number;
    descripcion: string;
}

interface SimuladorProps {
    vehiculo: Vehiculo;
    onClose: () => void;
}

export default function SimuladorCotizacion({ vehiculo, onClose }: SimuladorProps) {
    const router = useRouter();
    const [accesorios, setAccesorios] = useState<Accesorio[]>([]);
    const [selectedAccesorios, setSelectedAccesorios] = useState<string[]>([]);
    const [loading, setLoading] = useState(true);

    // Estados del flujo
    const [simulando, setSimulando] = useState(false);
    const [resultadoSimulacion, setResultadoSimulacion] = useState<any>(null);
    const [cotizacionGenerada, setCotizacionGenerada] = useState<any>(null);
    const [procesandoReserva, setProcesandoReserva] = useState(false);
    const [reservaExitosa, setReservaExitosa] = useState<any>(null);

    useEffect(() => {
        const fetchAccesorios = async () => {
            try {
                const response = await api.get('/accesorios/');
                setAccesorios(response.data.results || response.data);
            } catch (error) {
                console.error('Error cargando accesorios:', error);
            } finally {
                setLoading(false);
            }
        };
        fetchAccesorios();
    }, [vehiculo.id]);

    const toggleAccesorio = (id: string) => {
        setSelectedAccesorios(prev =>
            prev.includes(id) ? prev.filter(a => a !== id) : [...prev, id]
        );
    };

    const handleSimular = async () => {
        setSimulando(true);
        try {
            const payload = {
                vehiculos: [{ vehiculo_id: vehiculo.id, accesorios: selectedAccesorios }]
            };
            const response = await api.post('/cotizaciones/simular/', payload);
            setResultadoSimulacion(response.data);
        } catch (error) {
            console.error('Error simulando:', error);
        } finally {
            setSimulando(false);
        }
    };

    const handleGenerar = async () => {
        const token = localStorage.getItem('access_token');
        if (!token) {
            // Guardar estado para recuperar después del login (opcional)
            router.push('/login');
            return;
        }

        setSimulando(true);
        try {
            const payload = {
                vehiculos: [{ vehiculo_id: vehiculo.id, accesorios: selectedAccesorios }]
            };
            const response = await api.post('/cotizaciones/generar/', payload);
            setCotizacionGenerada(response.data);
        } catch (error) {
            console.error('Error generando cotización:', error);
            alert('Error al generar la cotización. Intenta nuevamente.');
        } finally {
            setSimulando(false);
        }
    };

    const handleReservar = async () => {
        if (!cotizacionGenerada) return;

        setProcesandoReserva(true);
        try {
            // C.U. 03 - Realizar Reserva (incluye pago de seña)
            const response = await api.post('/reservas/crear/', {
                cotizacion_id: cotizacionGenerada.id
            });
            setReservaExitosa(response.data);
        } catch (error: any) {
            console.error('Error reservando:', error);
            alert(error.response?.data?.error || 'Error al procesar la reserva o el pago.');
        } finally {
            setProcesandoReserva(false);
        }
    };

    // --- VISTA: RESERVA EXITOSA ---
    if (reservaExitosa) {
        return (
            <div className="text-center space-y-6 py-8">
                <div className="w-20 h-20 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                    <Check className="w-10 h-10 text-green-600" />
                </div>
                <h3 className="text-2xl font-bold text-gray-900">¡Reserva Exitosa!</h3>
                <p className="text-gray-600">
                    Tu vehículo ha sido reservado correctamente.
                </p>

                <div className="bg-gray-50 p-6 rounded-2xl text-left space-y-3">
                    <div className="flex justify-between">
                        <span className="text-gray-500">Nro. Reserva:</span>
                        <span className="font-mono font-bold">{reservaExitosa.nro_reserva}</span>
                    </div>
                    <div className="flex justify-between">
                        <span className="text-gray-500">Estado:</span>
                        <span className="text-green-600 font-bold">{reservaExitosa.estado}</span>
                    </div>
                    <div className="flex justify-between">
                        <span className="text-gray-500">Vencimiento:</span>
                        <span>{new Date(reservaExitosa.fecha_hora_vencimiento).toLocaleDateString()}</span>
                    </div>
                </div>

                <Button onClick={onClose} className="w-full">
                    Cerrar
                </Button>
            </div>
        );
    }

    // --- VISTA: CONFIRMAR RESERVA (COTIZACIÓN GENERADA) ---
    if (cotizacionGenerada) {
        const importeTotal = Number(cotizacionGenerada.importe_final);
        const seña = importeTotal * 0.05; // 5%

        return (
            <div className="space-y-6">
                <div className="bg-blue-50 p-6 rounded-2xl border border-blue-100">
                    <h3 className="text-lg font-bold text-blue-900 mb-4">Cotización Oficial #{cotizacionGenerada.id.slice(0, 8)}</h3>
                    <div className="space-y-2">
                        <div className="flex justify-between text-blue-800">
                            <span>Total Vehículo + Accesorios:</span>
                            <span className="font-bold">${importeTotal.toLocaleString('es-AR')}</span>
                        </div>
                        <div className="h-px bg-blue-200 my-2"></div>
                        <div className="flex justify-between items-center">
                            <span className="text-blue-900 font-bold">Seña a Pagar (5%):</span>
                            <span className="text-2xl font-bold text-blue-600">${seña.toLocaleString('es-AR')}</span>
                        </div>
                    </div>
                </div>

                <div className="text-sm text-gray-500 bg-gray-50 p-4 rounded-xl">
                    <p>ℹ️ Al confirmar, serás redirigido a la pasarela de pagos para abonar la seña. La reserva tendrá una validez de 7 días.</p>
                </div>

                <div className="flex gap-4">
                    <Button variant="outline" onClick={() => setCotizacionGenerada(null)} disabled={procesandoReserva} className="flex-1">
                        Volver
                    </Button>
                    <Button onClick={handleReservar} disabled={procesandoReserva} className="flex-[2]">
                        {procesandoReserva ? (
                            <><Loader2 className="w-4 h-4 animate-spin" /> Procesando Pago...</>
                        ) : (
                            <><CreditCard className="w-4 h-4" /> Pagar Seña y Reservar</>
                        )}
                    </Button>
                </div>
            </div>
        );
    }

    // --- VISTA: RESULTADO SIMULACIÓN ---
    if (resultadoSimulacion) {
        return (
            <div className="space-y-6">
                <div className="bg-gray-50 p-6 rounded-2xl border border-gray-100 text-center">
                    <p className="text-gray-600 font-medium mb-2">Precio Estimado</p>
                    <p className="text-4xl font-bold text-gray-900">
                        ${Number(resultadoSimulacion.importe_total).toLocaleString('es-AR')}
                    </p>
                </div>

                <div className="space-y-3">
                    <h3 className="font-semibold text-gray-900">Detalle</h3>
                    {resultadoSimulacion.detalle.map((item: any, idx: number) => (
                        <div key={idx} className="bg-white border border-gray-100 p-4 rounded-xl shadow-sm">
                            <div className="flex justify-between font-medium mb-2">
                                <span>{item.vehiculo.modelo}</span>
                                <span>${Number(item.vehiculo.precio).toLocaleString('es-AR')}</span>
                            </div>
                            {item.accesorios.map((acc: any) => (
                                <div key={acc.id} className="flex justify-between text-sm text-gray-600 pl-4 border-l-2 border-gray-200 mt-1">
                                    <span>+ {acc.nombre}</span>
                                    <span>${Number(acc.precio).toLocaleString('es-AR')}</span>
                                </div>
                            ))}
                        </div>
                    ))}
                </div>

                <div className="flex gap-4 pt-4">
                    <Button variant="outline" onClick={() => setResultadoSimulacion(null)} className="flex-1">
                        Modificar
                    </Button>
                    <Button onClick={handleGenerar} className="flex-[2]">
                        Generar Cotización
                    </Button>
                </div>
            </div>
        );
    }

    // --- VISTA: SELECCIÓN DE ACCESORIOS (INICIAL) ---
    return (
        <div className="space-y-6">
            <div className="flex items-start gap-4 p-4 bg-gray-50 rounded-2xl">
                <div className="flex-1">
                    <p className="text-sm text-blue-600 font-semibold">{vehiculo.marca_nombre}</p>
                    <h3 className="text-xl font-bold text-gray-900">{vehiculo.modelo_nombre}</h3>
                </div>
                <div className="text-right">
                    <p className="text-sm text-gray-500">Precio Base</p>
                    <p className="text-lg font-bold text-gray-900">
                        ${Number(vehiculo.precio).toLocaleString('es-AR')}
                    </p>
                </div>
            </div>

            <div>
                <h3 className="font-semibold text-gray-900 mb-4">Agregar Accesorios</h3>
                {loading ? (
                    <div className="text-center py-8 text-gray-400">Cargando accesorios...</div>
                ) : (
                    <div className="grid grid-cols-1 gap-3 max-h-60 overflow-y-auto pr-2">
                        {accesorios.map((acc) => {
                            const selected = selectedAccesorios.includes(acc.id);
                            return (
                                <div
                                    key={acc.id}
                                    onClick={() => toggleAccesorio(acc.id)}
                                    className={`
                    cursor-pointer p-4 rounded-xl border transition-all duration-200 flex items-center justify-between
                    ${selected
                                            ? 'border-blue-500 bg-blue-50 ring-1 ring-blue-500'
                                            : 'border-gray-200 hover:border-blue-200 hover:bg-gray-50'}
                  `}
                                >
                                    <div>
                                        <p className="font-medium text-gray-900">{acc.nombre}</p>
                                        <p className="text-sm text-gray-500">{acc.descripcion}</p>
                                    </div>
                                    <div className={`
                    w-6 h-6 rounded-full flex items-center justify-center transition-colors
                    ${selected ? 'bg-blue-500 text-white' : 'bg-gray-200 text-gray-400'}
                  `}>
                                        {selected ? <Check className="w-4 h-4" /> : <Plus className="w-4 h-4" />}
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                )}
            </div>

            <div className="pt-4 border-t border-gray-100">
                <Button
                    onClick={handleSimular}
                    className="w-full"
                    disabled={simulando}
                >
                    {simulando ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Calcular Precio Final'}
                </Button>
            </div>
        </div>
    );
}
