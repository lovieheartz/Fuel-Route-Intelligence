'use client';

/**
 * Route Planner Form Component
 * Form for inputting start/end locations with autocomplete suggestions
 */

import { useState, useRef, useEffect } from 'react';
import { MapPin, Navigation, Gauge, Fuel, ChevronDown } from 'lucide-react';

interface RoutePlannerFormProps {
  onSubmit: (
    startLocation: string,
    endLocation: string,
    vehicleMpg?: number,
    vehicleRange?: number
  ) => void;
  loading: boolean;
}

// Popular US cities for autocomplete
const US_CITIES = [
  'Los Angeles, CA',
  'San Francisco, CA',
  'San Diego, CA',
  'Sacramento, CA',
  'Oakland, CA',
  'San Jose, CA',
  'New York, NY',
  'Buffalo, NY',
  'Rochester, NY',
  'Chicago, IL',
  'Springfield, IL',
  'Houston, TX',
  'Dallas, TX',
  'Austin, TX',
  'San Antonio, TX',
  'Phoenix, AZ',
  'Tucson, AZ',
  'Philadelphia, PA',
  'Pittsburgh, PA',
  'Seattle, WA',
  'Spokane, WA',
  'Miami, FL',
  'Orlando, FL',
  'Tampa, FL',
  'Jacksonville, FL',
  'Boston, MA',
  'Denver, CO',
  'Colorado Springs, CO',
  'Las Vegas, NV',
  'Reno, NV',
  'Portland, OR',
  'Eugene, OR',
  'Atlanta, GA',
  'Savannah, GA',
  'Detroit, MI',
  'Minneapolis, MN',
  'Cleveland, OH',
  'Columbus, OH',
  'Cincinnati, OH',
  'Nashville, TN',
  'Memphis, TN',
  'Salt Lake City, UT',
  'Albuquerque, NM',
  'Kansas City, MO',
  'St. Louis, MO',
  'Indianapolis, IN',
  'Milwaukee, WI',
  'Charlotte, NC',
  'Raleigh, NC',
];

const POPULAR_ROUTES = [
  { name: 'LA to San Francisco', start: 'Los Angeles, CA', end: 'San Francisco, CA' },
  { name: 'NY to LA', start: 'New York, NY', end: 'Los Angeles, CA' },
  { name: 'Seattle to Miami', start: 'Seattle, WA', end: 'Miami, FL' },
  { name: 'Chicago to Houston', start: 'Chicago, IL', end: 'Houston, TX' },
];

export default function RoutePlannerForm({ onSubmit, loading }: RoutePlannerFormProps) {
  const [startLocation, setStartLocation] = useState('');
  const [endLocation, setEndLocation] = useState('');
  const [vehicleMpg, setVehicleMpg] = useState('10');
  const [vehicleRange, setVehicleRange] = useState('500');
  const [showAdvanced, setShowAdvanced] = useState(false);

  // Autocomplete states
  const [startSuggestions, setStartSuggestions] = useState<string[]>([]);
  const [endSuggestions, setEndSuggestions] = useState<string[]>([]);
  const [showStartSuggestions, setShowStartSuggestions] = useState(false);
  const [showEndSuggestions, setShowEndSuggestions] = useState(false);

  const startInputRef = useRef<HTMLInputElement>(null);
  const endInputRef = useRef<HTMLInputElement>(null);
  const startSuggestionsRef = useRef<HTMLDivElement>(null);
  const endSuggestionsRef = useRef<HTMLDivElement>(null);

  // Handle clicks outside to close suggestions
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (startSuggestionsRef.current && !startSuggestionsRef.current.contains(event.target as Node) &&
          !startInputRef.current?.contains(event.target as Node)) {
        setShowStartSuggestions(false);
      }
      if (endSuggestionsRef.current && !endSuggestionsRef.current.contains(event.target as Node) &&
          !endInputRef.current?.contains(event.target as Node)) {
        setShowEndSuggestions(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleStartChange = (value: string) => {
    setStartLocation(value);
    if (value.length > 0) {
      const filtered = US_CITIES.filter(city =>
        city.toLowerCase().includes(value.toLowerCase())
      ).slice(0, 5);
      setStartSuggestions(filtered);
      setShowStartSuggestions(filtered.length > 0);
    } else {
      setShowStartSuggestions(false);
    }
  };

  const handleEndChange = (value: string) => {
    setEndLocation(value);
    if (value.length > 0) {
      const filtered = US_CITIES.filter(city =>
        city.toLowerCase().includes(value.toLowerCase())
      ).slice(0, 5);
      setEndSuggestions(filtered);
      setShowEndSuggestions(filtered.length > 0);
    } else {
      setShowEndSuggestions(false);
    }
  };

  const selectStartSuggestion = (city: string) => {
    setStartLocation(city);
    setShowStartSuggestions(false);
  };

  const selectEndSuggestion = (city: string) => {
    setEndLocation(city);
    setShowEndSuggestions(false);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    const mpg = vehicleMpg ? parseFloat(vehicleMpg) : undefined;
    const range = vehicleRange ? parseFloat(vehicleRange) : undefined;

    onSubmit(startLocation, endLocation, mpg, range);
  };

  const handleQuickRoute = (route: typeof POPULAR_ROUTES[0]) => {
    setStartLocation(route.start);
    setEndLocation(route.end);
  };

  return (
    <div className="bg-white rounded-lg shadow-lg p-6 border border-gray-200">
      <h2 className="text-2xl font-bold text-gray-900 mb-6">Plan Your Route</h2>

      <form onSubmit={handleSubmit} className="space-y-5">
        {/* Start Location */}
        <div className="relative">
          <label htmlFor="start" className="block text-sm font-medium text-gray-700 mb-2">
            <MapPin className="inline w-4 h-4 mr-1 text-green-600" />
            Start Location
          </label>
          <input
            ref={startInputRef}
            type="text"
            id="start"
            value={startLocation}
            onChange={(e) => handleStartChange(e.target.value)}
            onFocus={() => {
              if (startLocation.length > 0 && startSuggestions.length > 0) {
                setShowStartSuggestions(true);
              }
            }}
            placeholder="e.g., Los Angeles, CA"
            required
            autoComplete="off"
            className="w-full px-4 py-3 text-gray-900 bg-white border-2 border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all text-base placeholder-gray-400"
          />

          {/* Start Suggestions Dropdown */}
          {showStartSuggestions && startSuggestions.length > 0 && (
            <div
              ref={startSuggestionsRef}
              className="absolute z-50 w-full mt-1 bg-white border-2 border-blue-500 rounded-lg shadow-xl max-h-60 overflow-auto"
            >
              {startSuggestions.map((city, index) => (
                <button
                  key={index}
                  type="button"
                  onClick={() => selectStartSuggestion(city)}
                  className="w-full text-left px-4 py-3 hover:bg-blue-50 transition-colors text-gray-900 border-b border-gray-100 last:border-b-0"
                >
                  <MapPin className="inline w-4 h-4 mr-2 text-green-600" />
                  {city}
                </button>
              ))}
            </div>
          )}
        </div>

        {/* End Location */}
        <div className="relative">
          <label htmlFor="end" className="block text-sm font-medium text-gray-700 mb-2">
            <Navigation className="inline w-4 h-4 mr-1 text-red-600" />
            End Location
          </label>
          <input
            ref={endInputRef}
            type="text"
            id="end"
            value={endLocation}
            onChange={(e) => handleEndChange(e.target.value)}
            onFocus={() => {
              if (endLocation.length > 0 && endSuggestions.length > 0) {
                setShowEndSuggestions(true);
              }
            }}
            placeholder="e.g., San Francisco, CA"
            required
            autoComplete="off"
            className="w-full px-4 py-3 text-gray-900 bg-white border-2 border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all text-base placeholder-gray-400"
          />

          {/* End Suggestions Dropdown */}
          {showEndSuggestions && endSuggestions.length > 0 && (
            <div
              ref={endSuggestionsRef}
              className="absolute z-50 w-full mt-1 bg-white border-2 border-red-500 rounded-lg shadow-xl max-h-60 overflow-auto"
            >
              {endSuggestions.map((city, index) => (
                <button
                  key={index}
                  type="button"
                  onClick={() => selectEndSuggestion(city)}
                  className="w-full text-left px-4 py-3 hover:bg-red-50 transition-colors text-gray-900 border-b border-gray-100 last:border-b-0"
                >
                  <Navigation className="inline w-4 h-4 mr-2 text-red-600" />
                  {city}
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Advanced Options Toggle */}
        <button
          type="button"
          onClick={() => setShowAdvanced(!showAdvanced)}
          className="flex items-center text-sm text-blue-600 hover:text-blue-700 font-medium"
        >
          <ChevronDown className={`w-4 h-4 mr-1 transition-transform ${showAdvanced ? 'rotate-180' : ''}`} />
          {showAdvanced ? 'Hide' : 'Show'} Advanced Options
        </button>

        {/* Advanced Options */}
        {showAdvanced && (
          <div className="space-y-4 pt-4 border-t border-gray-200 animate-in">
            <div className="grid grid-cols-2 gap-4">
              {/* Vehicle MPG */}
              <div>
                <label htmlFor="mpg" className="block text-sm font-medium text-gray-700 mb-2">
                  <Gauge className="inline w-4 h-4 mr-1 text-blue-600" />
                  Vehicle MPG
                </label>
                <input
                  type="number"
                  id="mpg"
                  value={vehicleMpg}
                  onChange={(e) => setVehicleMpg(e.target.value)}
                  placeholder="10"
                  step="0.1"
                  min="1"
                  max="50"
                  className="w-full px-4 py-2 text-gray-900 bg-white border-2 border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>

              {/* Vehicle Range */}
              <div>
                <label htmlFor="range" className="block text-sm font-medium text-gray-700 mb-2">
                  <Fuel className="inline w-4 h-4 mr-1 text-orange-600" />
                  Range (miles)
                </label>
                <input
                  type="number"
                  id="range"
                  value={vehicleRange}
                  onChange={(e) => setVehicleRange(e.target.value)}
                  placeholder="500"
                  step="10"
                  min="50"
                  max="1000"
                  className="w-full px-4 py-2 text-gray-900 bg-white border-2 border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
            </div>
          </div>
        )}

        {/* Submit Button */}
        <button
          type="submit"
          disabled={loading || !startLocation || !endLocation}
          className="w-full bg-blue-600 text-white py-3 px-6 rounded-lg font-semibold hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-all shadow-md hover:shadow-lg text-base"
        >
          {loading ? (
            <span className="flex items-center justify-center">
              <svg
                className="animate-spin -ml-1 mr-3 h-5 w-5 text-white"
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
              >
                <circle
                  className="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  strokeWidth="4"
                ></circle>
                <path
                  className="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                ></path>
              </svg>
              Planning Route...
            </span>
          ) : (
            'Plan Route'
          )}
        </button>
      </form>

      {/* Popular Routes Quick Select */}
      <div className="mt-6 pt-6 border-t border-gray-200">
        <p className="text-sm font-medium text-gray-700 mb-3">Popular Routes:</p>
        <div className="grid grid-cols-2 gap-2">
          {POPULAR_ROUTES.map((route) => (
            <button
              key={route.name}
              type="button"
              onClick={() => handleQuickRoute(route)}
              disabled={loading}
              className="text-xs text-left px-3 py-2 bg-blue-50 hover:bg-blue-100 border-2 border-blue-200 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <div className="font-medium text-gray-900">{route.name}</div>
              <div className="text-gray-600 truncate text-[10px]">{route.start} → {route.end}</div>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
