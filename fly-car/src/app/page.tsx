'use client';

import { useEffect, useState } from 'react';
import api from '@/lib/api';
import VehiculoCard from '@/components/VehiculoCard';
import { Loader2 } from 'lucide-react';

interface Vehiculo {
  id: string;
  modelo_nombre: string;
  marca_nombre: string;
  precio: number;
  anio: number;
  estado: string;
  modelo: number;
}

import Modal from '@/components/ui/Modal';
import SimuladorCotizacion from '@/components/SimuladorCotizacion';

export default function Home() {
  const [vehiculos, setVehiculos] = useState<Vehiculo[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedVehiculo, setSelectedVehiculo] = useState<Vehiculo | null>(null);

  useEffect(() => {
    const fetchVehiculos = async () => {
      try {
        const response = await api.get('/vehiculos/?estado=DISPONIBLE');
        // Manejar respuesta paginada (Django REST Framework)
        if (response.data.results) {
          setVehiculos(response.data.results);
        } else if (Array.isArray(response.data)) {
          setVehiculos(response.data);
        } else {
          setVehiculos([]);
        }
      } catch (error) {
        console.error('Error al cargar vehículos:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchVehiculos();
  }, []);

  return (
    <main className="min-h-screen bg-gray-50">
      {/* Hero Section */}
      <section className="bg-gray-900 text-white py-20 px-6">
        <div className="max-w-7xl mx-auto">
          <h1 className="text-5xl md:text-7xl font-bold mb-6 tracking-tight">
            FLY CAR <span className="text-blue-500">Premium</span>
          </h1>
          <p className="text-xl text-gray-400 max-w-2xl mb-8">
            Descubre la experiencia de conducir el futuro. Vehículos exclusivos, atención personalizada y la mejor financiación del mercado.
          </p>
        </div>
      </section>

      {/* Catálogo */}
      <section className="max-w-7xl mx-auto px-6 py-16">
        <div className="flex items-center justify-between mb-12">
          <h2 className="text-3xl font-bold text-gray-900">Vehículos Disponibles</h2>
          <div className="flex gap-2">
            {/* Filtros podrían ir aquí */}
          </div>
        </div>

        {loading ? (
          <div className="flex justify-center py-20">
            <Loader2 className="w-10 h-10 animate-spin text-blue-600" />
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {vehiculos.map((vehiculo) => (
              <VehiculoCard
                key={vehiculo.id}
                vehiculo={vehiculo}
                onSimular={() => setSelectedVehiculo(vehiculo)}
              />
            ))}
          </div>
        )}
      </section>

      {/* Modal de Simulación */}
      <Modal
        isOpen={!!selectedVehiculo}
        onClose={() => setSelectedVehiculo(null)}
        title="Simular Cotización"
      >
        {selectedVehiculo && (
          <SimuladorCotizacion
            vehiculo={selectedVehiculo}
            onClose={() => setSelectedVehiculo(null)}
          />
        )}
      </Modal>
    </main>
  );
}
