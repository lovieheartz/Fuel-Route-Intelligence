'use client';

/**
 * Main Application Page
 * Production-grade fuel routing optimization interface
 */

import { useState } from 'react';
import dynamic from 'next/dynamic';
import { Fuel, TrendingUp, Clock, AlertCircle } from 'lucide-react';
import RoutePlannerForm from '@/components/RoutePlannerForm';
import FuelStopsList from '@/components/FuelStopsList';
import { api, type RouteResponse } from '@/lib/api';

// Dynamic import for map component (client-side only)
const RouteMap = dynamic(() => import('@/components/RouteMap'), {
  ssr: false,
  loading: () => (
    <div className="w-full h-full bg-gray-100 rounded-lg flex items-center justify-center">
      <div className="text-gray-500">Loading map...</div>
    </div>
  ),
});

export default function Home() {
  const [routeData, setRouteData] = useState<RouteResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handlePlanRoute = async (
    startLocation: string,
    endLocation: string,
    vehicleMpg?: number,
    vehicleRange?: number
  ) => {
    setLoading(true);
    setError(null);

    try {
      const data = await api.planRoute(startLocation, endLocation, vehicleMpg, vehicleRange);
      setRouteData(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An unexpected error occurred');
      setRouteData(null);
    } finally {
      setLoading(false);
    }
  };

  const formatDuration = (seconds: number): string => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    return `${hours}h ${minutes}m`;
  };

  return (
    <main className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
      {/* Header */}
      <header className="bg-white shadow-md">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="bg-primary-600 p-2 rounded-lg">
                <Fuel className="w-8 h-8 text-white" />
              </div>
              <div>
                <h1 className="text-3xl font-bold text-gray-900">Spotter AI</h1>
                <p className="text-sm text-gray-600">Fuel Routing Optimization</p>
              </div>
            </div>
            <div className="hidden md:flex items-center space-x-6 text-sm">
              <div className="flex items-center text-gray-600">
                <TrendingUp className="w-4 h-4 mr-1 text-green-600" />
                Optimal Routes
              </div>
              <div className="flex items-center text-gray-600">
                <Fuel className="w-4 h-4 mr-1 text-orange-600" />
                Best Fuel Prices
              </div>
              <div className="flex items-center text-gray-600">
                <Clock className="w-4 h-4 mr-1 text-blue-600" />
                Real-time Data
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Error Alert */}
        {error && (
          <div className="mb-6 bg-red-50 border-l-4 border-red-500 p-4 rounded-lg animate-in">
            <div className="flex items-start">
              <AlertCircle className="w-5 h-5 text-red-500 mr-3 flex-shrink-0 mt-0.5" />
              <div>
                <h3 className="text-red-800 font-semibold">Error Planning Route</h3>
                <p className="text-red-700 text-sm mt-1">{error}</p>
              </div>
            </div>
          </div>
        )}

        {/* Route Summary Banner */}
        {routeData && (
          <div className="mb-6 bg-gradient-to-r from-primary-600 to-primary-700 text-white rounded-lg shadow-lg p-6 animate-in">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div>
                <p className="text-primary-100 text-xs mb-1">Route</p>
                <p className="font-bold text-lg">
                  {routeData.start_location.split(',')[0]} → {routeData.end_location.split(',')[0]}
                </p>
              </div>
              <div>
                <p className="text-primary-100 text-xs mb-1">Distance</p>
                <p className="font-bold text-lg">
                  {routeData.route.distance_miles.toFixed(0)} miles
                </p>
              </div>
              <div>
                <p className="text-primary-100 text-xs mb-1">Duration</p>
                <p className="font-bold text-lg">
                  {formatDuration(routeData.route.duration_seconds)}
                </p>
              </div>
              <div>
                <p className="text-primary-100 text-xs mb-1">Total Fuel Cost</p>
                <p className="font-bold text-lg">
                  ${routeData.summary.total_fuel_cost.toFixed(2)}
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Main Grid Layout */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Column - Form */}
          <div className="lg:col-span-1 space-y-6">
            <RoutePlannerForm onSubmit={handlePlanRoute} loading={loading} />
          </div>

          {/* Middle Column - Map */}
          <div className="lg:col-span-2">
            <div className="bg-white rounded-lg shadow-lg p-4 h-[600px]">
              <RouteMap routeData={routeData} className="h-full" />
            </div>
          </div>
        </div>

        {/* Fuel Stops Section */}
        {routeData && (
          <div className="mt-6 animate-in">
            <FuelStopsList routeData={routeData} />
          </div>
        )}

        {/* Info Cards */}
        {!routeData && !loading && (
          <div className="mt-12 grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="bg-white rounded-lg shadow-md p-6 text-center">
              <div className="bg-green-100 w-12 h-12 rounded-full flex items-center justify-center mx-auto mb-4">
                <TrendingUp className="w-6 h-6 text-green-700" />
              </div>
              <h3 className="font-bold text-gray-900 mb-2">Optimal Routes</h3>
              <p className="text-sm text-gray-600">
                Advanced algorithms find the most efficient routes with minimal detours
              </p>
            </div>

            <div className="bg-white rounded-lg shadow-md p-6 text-center">
              <div className="bg-orange-100 w-12 h-12 rounded-full flex items-center justify-center mx-auto mb-4">
                <Fuel className="w-6 h-6 text-orange-700" />
              </div>
              <h3 className="font-bold text-gray-900 mb-2">Best Fuel Prices</h3>
              <p className="text-sm text-gray-600">
                Access to 6,700+ fuel stations with real-time pricing data
              </p>
            </div>

            <div className="bg-white rounded-lg shadow-md p-6 text-center">
              <div className="bg-blue-100 w-12 h-12 rounded-full flex items-center justify-center mx-auto mb-4">
                <Clock className="w-6 h-6 text-blue-700" />
              </div>
              <h3 className="font-bold text-gray-900 mb-2">Lightning Fast</h3>
              <p className="text-sm text-gray-600">
                Intelligent caching provides instant results for repeated queries
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Footer */}
      <footer className="bg-white border-t border-gray-200 mt-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="text-center text-gray-600 text-sm">
            <p>Spotter AI - Production-Grade Fuel Routing Optimization System</p>
            <p className="mt-1 text-gray-500">
              Powered by OSRM, Nominatim, and advanced optimization algorithms
            </p>
          </div>
        </div>
      </footer>
    </main>
  );
}
