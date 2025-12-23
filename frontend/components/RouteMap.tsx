'use client';

/**
 * Interactive Route Map Component
 * Displays routes, fuel stops, and interactive markers using Leaflet
 */

import { useEffect, useRef, useState } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { decodePolyline, getPolylineBounds, type LatLng } from '@/lib/polyline';
import type { RouteResponse, FuelStop } from '@/lib/api';

interface RouteMapProps {
  routeData: RouteResponse | null;
  className?: string;
}

export default function RouteMap({ routeData, className = '' }: RouteMapProps) {
  const mapRef = useRef<L.Map | null>(null);
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const [isMapReady, setIsMapReady] = useState(false);

  // Initialize map
  useEffect(() => {
    if (!mapContainerRef.current || mapRef.current) return;

    // Create map instance
    const map = L.map(mapContainerRef.current, {
      center: [39.8283, -98.5795], // Center of USA
      zoom: 4,
      zoomControl: true,
      scrollWheelZoom: true,
    });

    // Add OpenStreetMap tiles
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
      maxZoom: 19,
    }).addTo(map);

    mapRef.current = map;
    setIsMapReady(true);

    return () => {
      if (mapRef.current) {
        mapRef.current.remove();
        mapRef.current = null;
      }
    };
  }, []);

  // Update map when route data changes
  useEffect(() => {
    if (!isMapReady || !mapRef.current || !routeData) return;

    const map = mapRef.current;

    // Clear existing layers
    map.eachLayer((layer) => {
      if (layer instanceof L.Polyline || layer instanceof L.Marker) {
        map.removeLayer(layer);
      }
    });

    // Decode and draw route polyline
    const routeCoordinates = decodePolyline(routeData.route.geometry);
    const latLngs: [number, number][] = routeCoordinates.map((coord) => [coord.lat, coord.lng]);

    // Draw route line
    const routeLine = L.polyline(latLngs, {
      color: '#0ea5e9',
      weight: 4,
      opacity: 0.8,
    }).addTo(map);

    // Create custom icons
    const startIcon = L.divIcon({
      className: 'custom-marker',
      html: `
        <div style="
          background-color: #10b981;
          width: 32px;
          height: 32px;
          border-radius: 50%;
          border: 3px solid white;
          box-shadow: 0 2px 8px rgba(0,0,0,0.3);
          display: flex;
          align-items: center;
          justify-content: center;
          font-weight: bold;
          color: white;
          font-size: 16px;
        ">A</div>
      `,
      iconSize: [32, 32],
      iconAnchor: [16, 16],
    });

    const endIcon = L.divIcon({
      className: 'custom-marker',
      html: `
        <div style="
          background-color: #ef4444;
          width: 32px;
          height: 32px;
          border-radius: 50%;
          border: 3px solid white;
          box-shadow: 0 2px 8px rgba(0,0,0,0.3);
          display: flex;
          align-items: center;
          justify-content: center;
          font-weight: bold;
          color: white;
          font-size: 16px;
        ">B</div>
      `,
      iconSize: [32, 32],
      iconAnchor: [16, 16],
    });

    const fuelIcon = L.divIcon({
      className: 'custom-marker',
      html: `
        <div style="
          background-color: #f59e0b;
          width: 28px;
          height: 28px;
          border-radius: 50%;
          border: 3px solid white;
          box-shadow: 0 2px 8px rgba(0,0,0,0.3);
          display: flex;
          align-items: center;
          justify-content: center;
          color: white;
          font-size: 14px;
        ">⛽</div>
      `,
      iconSize: [28, 28],
      iconAnchor: [14, 14],
    });

    // Add start marker
    const startMarker = L.marker(
      [routeData.start_coordinates.latitude, routeData.start_coordinates.longitude],
      { icon: startIcon }
    ).addTo(map);

    startMarker.bindPopup(`
      <div style="font-family: system-ui; padding: 4px;">
        <strong style="color: #10b981;">Start</strong><br/>
        ${routeData.start_location}
      </div>
    `);

    // Add end marker
    const endMarker = L.marker(
      [routeData.end_coordinates.latitude, routeData.end_coordinates.longitude],
      { icon: endIcon }
    ).addTo(map);

    endMarker.bindPopup(`
      <div style="font-family: system-ui; padding: 4px;">
        <strong style="color: #ef4444;">Destination</strong><br/>
        ${routeData.end_location}
      </div>
    `);

    // Add fuel stop markers
    routeData.fuel_stops.forEach((stop: FuelStop, index: number) => {
      const marker = L.marker([stop.latitude, stop.longitude], { icon: fuelIcon }).addTo(map);

      marker.bindPopup(`
        <div style="font-family: system-ui; padding: 8px; min-width: 200px;">
          <strong style="color: #f59e0b; font-size: 16px;">Fuel Stop ${index + 1}</strong><br/>
          <div style="margin-top: 8px; font-size: 14px;">
            <strong>${stop.name}</strong><br/>
            ${stop.address}<br/>
            ${stop.city}, ${stop.state}<br/><br/>
            <div style="background: #fef3c7; padding: 6px; border-radius: 4px; margin-top: 4px;">
              <strong>Price:</strong> $${stop.price_per_gallon.toFixed(3)}/gal<br/>
              <strong>Gallons:</strong> ${stop.gallons.toFixed(2)} gal<br/>
              <strong>Cost:</strong> $${stop.cost.toFixed(2)}
            </div>
            <div style="margin-top: 6px; color: #64748b; font-size: 12px;">
              ${stop.distance_from_start.toFixed(1)} miles from start
            </div>
          </div>
        </div>
      `);
    });

    // Fit map to route bounds with padding
    const bounds = getPolylineBounds(routeCoordinates);
    map.fitBounds(
      [
        [bounds.south, bounds.west],
        [bounds.north, bounds.east],
      ],
      { padding: [50, 50] }
    );
  }, [isMapReady, routeData]);

  return (
    <div className={`relative ${className}`}>
      <div ref={mapContainerRef} className="w-full h-full rounded-lg overflow-hidden shadow-lg" />

      {!routeData && (
        <div className="absolute inset-0 flex items-center justify-center bg-gray-100 rounded-lg">
          <div className="text-center text-gray-500">
            <svg
              className="mx-auto h-12 w-12 text-gray-400 mb-2"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7"
              />
            </svg>
            <p className="text-sm">Plan a route to see it on the map</p>
          </div>
        </div>
      )}
    </div>
  );
}
