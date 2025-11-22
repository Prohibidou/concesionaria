import Image from 'next/image';
import { Car, Check } from 'lucide-react';
import Button from './ui/Button';

interface VehiculoCardProps {
    vehiculo: {
        id: string;
        modelo_nombre: string;
        marca_nombre: string;
        precio: number;
        anio: number;
        imagen?: string;
    };
    onSimular: () => void;
}

export default function VehiculoCard({ vehiculo, onSimular }: VehiculoCardProps) {
    return (
        <div className="group relative bg-white rounded-3xl overflow-hidden border border-gray-100 shadow-sm hover:shadow-2xl transition-all duration-300 hover:-translate-y-1">
            <div className="aspect-[4/3] relative bg-gray-100 overflow-hidden">
                {/* Placeholder de imagen si no hay una real */}
                <div className="absolute inset-0 flex items-center justify-center bg-gradient-to-br from-gray-100 to-gray-200">
                    <Car className="w-20 h-20 text-gray-300" />
                </div>
                {/* Overlay gradiente */}
                <div className="absolute inset-0 bg-gradient-to-t from-black/50 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
            </div>

            <div className="p-6">
                <div className="mb-4">
                    <p className="text-sm font-semibold text-blue-600 mb-1">{vehiculo.marca_nombre}</p>
                    <h3 className="text-2xl font-bold text-gray-900">{vehiculo.modelo_nombre}</h3>
                    <p className="text-gray-500">{vehiculo.anio}</p>
                </div>

                <div className="flex items-end justify-between mb-6">
                    <div>
                        <p className="text-sm text-gray-500 mb-1">Precio desde</p>
                        <p className="text-2xl font-bold text-gray-900">
                            ${Number(vehiculo.precio).toLocaleString('es-AR')}
                        </p>
                    </div>
                </div>

                <Button onClick={onSimular} className="w-full" variant="outline">
                    Simular Cotización
                </Button>
            </div>
        </div>
    );
}
