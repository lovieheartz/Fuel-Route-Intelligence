'use client';

/**
 * Fuel Stops List Component
 * Displays detailed list of fuel stops along the route
 */

import { MapPin, DollarSign, Droplet, Navigation } from 'lucide-react';
import type { RouteResponse, FuelStop } from '@/lib/api';

interface FuelStopsListProps {
  routeData: RouteResponse | null;
}

export default function FuelStopsList({ routeData }: FuelStopsListProps) {
  if (!routeData) {
    return (
      <div className="bg-white rounded-lg shadow-lg p-6">
        <h3 className="text-xl font-bold text-gray-900 mb-4">Fuel Stops</h3>
        <div className="text-center py-12 text-gray-500">
          <Droplet className="w-12 h-12 mx-auto mb-3 text-gray-400" />
          <p>No route planned yet</p>
          <p className="text-sm mt-1">Plan a route to see fuel stops</p>
        </div>
      </div>
    );
  }

  const { fuel_stops, summary } = routeData;

  return (
    <div className="bg-white rounded-lg shadow-lg p-6">
      <h3 className="text-xl font-bold text-gray-900 mb-4">
        Fuel Stops ({fuel_stops.length})
      </h3>

      {/* Route Summary */}
      <div className="bg-gradient-to-r from-primary-50 to-primary-100 rounded-lg p-4 mb-6">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <p className="text-xs text-gray-600 mb-1">Total Distance</p>
            <p className="text-lg font-bold text-gray-900">
              {summary.total_distance_miles.toFixed(1)} mi
            </p>
          </div>
          <div>
            <p className="text-xs text-gray-600 mb-1">Total Fuel Cost</p>
            <p className="text-lg font-bold text-green-700">
              ${summary.total_fuel_cost.toFixed(2)}
            </p>
          </div>
          <div>
            <p className="text-xs text-gray-600 mb-1">Total Fuel</p>
            <p className="text-lg font-bold text-gray-900">
              {summary.total_fuel_gallons.toFixed(1)} gal
            </p>
          </div>
          <div>
            <p className="text-xs text-gray-600 mb-1">Fuel Stops</p>
            <p className="text-lg font-bold text-gray-900">
              {summary.number_of_stops}
            </p>
          </div>
        </div>
      </div>

      {/* Fuel Stops List */}
      {fuel_stops.length === 0 ? (
        <div className="text-center py-8 text-gray-500">
          <p>No fuel stops needed for this route</p>
          <p className="text-sm mt-1">Your vehicle can make it without refueling!</p>
        </div>
      ) : (
        <div className="space-y-4">
          {fuel_stops.map((stop: FuelStop, index: number) => (
            <div
              key={`${stop.station_id}-${index}`}
              className="border border-gray-200 rounded-lg p-4 hover:border-primary-300 hover:shadow-md transition-all"
            >
              {/* Stop Number Badge */}
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center space-x-3">
                  <div className="bg-orange-500 text-white rounded-full w-8 h-8 flex items-center justify-center font-bold text-sm">
                    {index + 1}
                  </div>
                  <div>
                    <h4 className="font-bold text-gray-900">{stop.name}</h4>
                    <p className="text-sm text-gray-600">{stop.city}, {stop.state}</p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-xs text-gray-500">Price per gallon</p>
                  <p className="text-lg font-bold text-green-700">
                    ${stop.price_per_gallon.toFixed(3)}
                  </p>
                </div>
              </div>

              {/* Address */}
              <div className="flex items-start text-sm text-gray-600 mb-3">
                <MapPin className="w-4 h-4 mr-2 mt-0.5 flex-shrink-0" />
                <p>{stop.address}</p>
              </div>

              {/* Fuel Details */}
              <div className="grid grid-cols-3 gap-3 pt-3 border-t border-gray-100">
                <div className="text-center">
                  <div className="flex items-center justify-center mb-1">
                    <Droplet className="w-4 h-4 text-blue-600" />
                  </div>
                  <p className="text-xs text-gray-500">Gallons</p>
                  <p className="font-semibold text-gray-900">{stop.gallons.toFixed(1)}</p>
                </div>
                <div className="text-center">
                  <div className="flex items-center justify-center mb-1">
                    <DollarSign className="w-4 h-4 text-green-600" />
                  </div>
                  <p className="text-xs text-gray-500">Cost</p>
                  <p className="font-semibold text-gray-900">${stop.cost.toFixed(2)}</p>
                </div>
                <div className="text-center">
                  <div className="flex items-center justify-center mb-1">
                    <Navigation className="w-4 h-4 text-purple-600" />
                  </div>
                  <p className="text-xs text-gray-500">Distance</p>
                  <p className="font-semibold text-gray-900">{stop.distance_from_start.toFixed(0)} mi</p>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Vehicle Info */}
      <div className="mt-6 pt-4 border-t border-gray-200">
        <p className="text-xs text-gray-500">
          Based on vehicle: {summary.vehicle_mpg.toFixed(1)} MPG, {summary.vehicle_range_miles.toFixed(0)} miles range
        </p>
      </div>
    </div>
  );
}
