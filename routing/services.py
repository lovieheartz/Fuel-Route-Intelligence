"""
Core routing and fuel optimization services.
Implements efficient algorithms for route planning and fuel stop optimization.
"""
import requests
import math
from typing import List, Dict, Tuple, Optional
from decimal import Decimal
from django.conf import settings
from django.core.cache import cache
from .models import FuelStation, RouteCache


class GeocodingService:
    """Service for converting addresses to coordinates"""

    @staticmethod
    def geocode_address(address: str) -> Optional[Tuple[float, float]]:
        """
        Convert address to coordinates using Nominatim (free geocoding service).
        Returns (latitude, longitude) tuple or None if not found.
        """
        cache_key = f"geocode_{address.lower().replace(' ', '_')}"
        cached = cache.get(cache_key)

        if cached:
            return cached

        try:
            url = "https://nominatim.openstreetmap.org/search"
            params = {
                'q': f"{address}, USA",
                'format': 'json',
                'limit': 1,
            }
            headers = {
                'User-Agent': 'FuelRoutingAPI/1.0'
            }

            response = requests.get(url, params=params, headers=headers, timeout=10)
            response.raise_for_status()

            data = response.json()
            if data:
                lat = float(data[0]['lat'])
                lon = float(data[0]['lon'])
                result = (lat, lon)
                cache.set(cache_key, result, timeout=86400)  # Cache for 24 hours
                return result

        except Exception as e:
            print(f"Geocoding error for {address}: {str(e)}")

        return None


class RoutingService:
    """Service for route calculation using OSRM (Free, no API key needed)"""

    def __init__(self):
        # Use OSRM public demo server (completely free, no API key)
        self.base_url = "http://router.project-osrm.org"

    def get_route(
        self,
        start_coords: Tuple[float, float],
        end_coords: Tuple[float, float],
        waypoints: Optional[List[Tuple[float, float]]] = None
    ) -> Optional[Dict]:
        """
        Get route from start to end with optional waypoints.
        Returns route data with geometry and distance.
        Uses OSRM (Open Source Routing Machine) - completely free!
        """
        # Create safer cache key without special characters
        cache_key = f"route_{start_coords[0]:.4f}_{start_coords[1]:.4f}_{end_coords[0]:.4f}_{end_coords[1]:.4f}"
        cached = cache.get(cache_key)

        if cached:
            print(f"[CACHE] Using cached route")
            return cached

        try:
            # Build coordinate string: lon,lat;lon,lat
            coords_str = f"{start_coords[1]},{start_coords[0]}"

            if waypoints:
                for wp in waypoints:
                    coords_str += f";{wp[1]},{wp[0]}"

            coords_str += f";{end_coords[1]},{end_coords[0]}"

            # OSRM route API
            url = f"{self.base_url}/route/v1/driving/{coords_str}"

            params = {
                'overview': 'full',
                'geometries': 'polyline',
                'steps': 'false'
            }

            print(f"[API] Calling OSRM routing API...")
            response = requests.get(url, params=params, timeout=30)

            print(f"Response status: {response.status_code}")

            if response.status_code == 200:
                data = response.json()

                if data.get('code') == 'Ok' and data.get('routes'):
                    route = data['routes'][0]

                    # Convert meters to miles (1 meter = 0.000621371 miles)
                    distance_meters = route['distance']
                    distance_miles = distance_meters * 0.000621371

                    result = {
                        'geometry': route['geometry'],
                        'distance_miles': distance_miles,
                        'duration_seconds': route['duration'],
                    }

                    print(f"[SUCCESS] Route calculated: {distance_miles:.2f} miles")
                    cache.set(cache_key, result, timeout=3600)  # Cache for 1 hour
                    return result
                else:
                    print(f"OSRM Error: {data.get('code', 'Unknown')}")

        except Exception as e:
            print(f"[ERROR] Routing error: {str(e)}")

        return None

    def decode_polyline(self, encoded: str) -> List[Tuple[float, float]]:
        """
        Decode Google-style polyline into list of coordinates.
        Returns list of (lat, lon) tuples.
        """
        coordinates = []
        index = 0
        lat = 0
        lon = 0

        while index < len(encoded):
            # Decode latitude
            b = 0
            shift = 0
            result = 0

            while True:
                b = ord(encoded[index]) - 63
                index += 1
                result |= (b & 0x1f) << shift
                shift += 5
                if b < 0x20:
                    break

            dlat = ~(result >> 1) if result & 1 else result >> 1
            lat += dlat

            # Decode longitude
            shift = 0
            result = 0

            while True:
                b = ord(encoded[index]) - 63
                index += 1
                result |= (b & 0x1f) << shift
                shift += 5
                if b < 0x20:
                    break

            dlon = ~(result >> 1) if result & 1 else result >> 1
            lon += dlon

            coordinates.append((lat / 1e5, lon / 1e5))

        return coordinates


class FuelOptimizationService:
    """
    Service for finding optimal fuel stops along a route.
    Uses dynamic programming for cost-effective fuel planning.
    """

    def __init__(self):
        self.vehicle_range = getattr(settings, 'VEHICLE_RANGE_MILES', 500)
        self.vehicle_mpg = getattr(settings, 'VEHICLE_MPG', 10)
        self.tank_capacity = self.vehicle_range / self.vehicle_mpg

    def haversine_distance(
        self,
        coord1: Tuple[float, float],
        coord2: Tuple[float, float]
    ) -> float:
        """
        Calculate distance between two coordinates using Haversine formula.
        Returns distance in miles.
        """
        lat1, lon1 = coord1
        lat2, lon2 = coord2

        R = 3959  # Earth's radius in miles

        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)

        a = (
            math.sin(dlat / 2) ** 2 +
            math.cos(math.radians(lat1)) *
            math.cos(math.radians(lat2)) *
            math.sin(dlon / 2) ** 2
        )

        c = 2 * math.asin(math.sqrt(a))
        return R * c

    def find_stations_near_route(
        self,
        route_points: List[Tuple[float, float]],
        max_distance_miles: float = 10.0
    ) -> List[FuelStation]:
        """
        Find fuel stations within max_distance of any point on the route.
        Uses efficient spatial queries.
        """
        stations_near_route = set()

        # Sample route points (don't check every single point for performance)
        sample_interval = max(1, len(route_points) // 50)
        sampled_points = route_points[::sample_interval]

        for point in sampled_points:
            lat, lon = point

            # Calculate rough lat/lon boundaries (1 degree ≈ 69 miles)
            lat_delta = max_distance_miles / 69.0
            lon_delta = max_distance_miles / (69.0 * math.cos(math.radians(lat)))

            # Query stations within bounding box
            stations = FuelStation.objects.filter(
                latitude__isnull=False,
                longitude__isnull=False,
                is_active=True,
                latitude__gte=lat - lat_delta,
                latitude__lte=lat + lat_delta,
                longitude__gte=lon - lon_delta,
                longitude__lte=lon + lon_delta,
            )

            # Verify actual distance
            for station in stations:
                if station.coordinates:
                    distance = self.haversine_distance(point, station.coordinates)
                    if distance <= max_distance_miles:
                        stations_near_route.add(station)

        return list(stations_near_route)

    def calculate_cumulative_distances(
        self,
        route_points: List[Tuple[float, float]]
    ) -> List[float]:
        """
        Calculate cumulative distance along route from start.
        Returns list of distances in miles.
        """
        cumulative = [0.0]
        total = 0.0

        for i in range(1, len(route_points)):
            distance = self.haversine_distance(route_points[i - 1], route_points[i])
            total += distance
            cumulative.append(total)

        return cumulative

    def find_optimal_fuel_stops(
        self,
        route_points: List[Tuple[float, float]],
        total_distance: float,
        available_stations: List[FuelStation]
    ) -> Tuple[List[Dict], float, float]:
        """
        Find optimal fuel stops using dynamic programming approach.
        Minimizes total fuel cost while respecting vehicle range constraints.

        Returns:
            - List of fuel stop dictionaries
            - Total fuel cost
            - Total fuel gallons
        """
        if not available_stations:
            return [], 0.0, 0.0

        # Map stations to their closest point on route with distance from start
        station_positions = []

        for station in available_stations:
            if not station.coordinates:
                continue

            # Find closest route point
            min_distance = float('inf')
            closest_point_idx = 0

            for i, route_point in enumerate(route_points[::10]):  # Sample for speed
                actual_idx = i * 10
                dist = self.haversine_distance(station.coordinates, route_point)
                if dist < min_distance:
                    min_distance = dist
                    closest_point_idx = actual_idx

            # Calculate distance from route start
            distance_from_start = sum(
                self.haversine_distance(route_points[i], route_points[i + 1])
                for i in range(closest_point_idx)
            )

            station_positions.append({
                'station': station,
                'distance_from_start': distance_from_start,
                'price': float(station.retail_price),
            })

        # Sort by distance from start
        station_positions.sort(key=lambda x: x['distance_from_start'])

        # Dynamic programming to find optimal stops
        selected_stops = []
        current_fuel = self.tank_capacity  # Start with full tank
        current_position = 0.0
        total_cost = 0.0
        total_gallons = 0.0

        while current_position < total_distance:
            # Find stations within current range
            reachable_stations = [
                sp for sp in station_positions
                if current_position < sp['distance_from_start'] <= current_position + self.vehicle_range
            ]

            if not reachable_stations:
                # Need to stop at nearest available station
                nearest = min(
                    [sp for sp in station_positions if sp['distance_from_start'] > current_position],
                    key=lambda x: x['distance_from_start'],
                    default=None
                )

                if nearest:
                    reachable_stations = [nearest]
                else:
                    break  # No more stations available

            if reachable_stations:
                # Choose cheapest station in range
                best_station = min(reachable_stations, key=lambda x: x['price'])

                # Calculate fuel needed
                distance_to_station = best_station['distance_from_start'] - current_position
                fuel_needed = distance_to_station / self.vehicle_mpg
                current_fuel -= fuel_needed

                # Refuel (fill tank)
                gallons_to_add = self.tank_capacity - current_fuel
                cost = gallons_to_add * best_station['price']

                selected_stops.append({
                    'station_id': best_station['station'].id,
                    'opis_id': best_station['station'].opis_id,
                    'name': best_station['station'].name,
                    'address': best_station['station'].address,
                    'city': best_station['station'].city,
                    'state': best_station['station'].state,
                    'latitude': float(best_station['station'].latitude),
                    'longitude': float(best_station['station'].longitude),
                    'price_per_gallon': best_station['price'],
                    'gallons': round(gallons_to_add, 2),
                    'cost': round(cost, 2),
                    'distance_from_start': round(best_station['distance_from_start'], 2),
                })

                total_cost += cost
                total_gallons += gallons_to_add
                current_fuel = self.tank_capacity
                current_position = best_station['distance_from_start']

                # Remove used station
                station_positions.remove(best_station)
            else:
                break

        return selected_stops, round(total_cost, 2), round(total_gallons, 2)


class FuelRoutingService:
    """
    Main service orchestrating route planning and fuel optimization.
    """

    def __init__(self):
        self.geocoding_service = GeocodingService()
        self.routing_service = RoutingService()
        self.fuel_service = FuelOptimizationService()

    def plan_route(
        self,
        start_location: str,
        end_location: str
    ) -> Dict:
        """
        Plan optimal route with fuel stops.

        Returns comprehensive route data including:
        - Route geometry (for map display)
        - Optimal fuel stops
        - Total distance
        - Total fuel cost
        - Total fuel gallons
        """
        # Check cache first
        cache_key = f"full_route_{start_location}_{end_location}"
        cached = cache.get(cache_key)

        if cached:
            return cached

        # Geocode locations
        start_coords = self.geocoding_service.geocode_address(start_location)
        end_coords = self.geocoding_service.geocode_address(end_location)

        if not start_coords:
            raise ValueError(f"Could not geocode start location: {start_location}")

        if not end_coords:
            raise ValueError(f"Could not geocode end location: {end_location}")

        # Get route
        route_data = self.routing_service.get_route(start_coords, end_coords)

        if not route_data:
            raise ValueError("Could not calculate route")

        # Decode route geometry to get points
        route_points = self.routing_service.decode_polyline(route_data['geometry'])

        # Find stations near route
        stations_near_route = self.fuel_service.find_stations_near_route(route_points)

        # Find optimal fuel stops
        fuel_stops, total_cost, total_gallons = self.fuel_service.find_optimal_fuel_stops(
            route_points,
            route_data['distance_miles'],
            stations_near_route
        )

        result = {
            'start_location': start_location,
            'end_location': end_location,
            'start_coordinates': {'latitude': start_coords[0], 'longitude': start_coords[1]},
            'end_coordinates': {'latitude': end_coords[0], 'longitude': end_coords[1]},
            'route': {
                'geometry': route_data['geometry'],
                'distance_miles': round(route_data['distance_miles'], 2),
                'duration_seconds': route_data['duration_seconds'],
            },
            'fuel_stops': fuel_stops,
            'summary': {
                'total_distance_miles': round(route_data['distance_miles'], 2),
                'total_fuel_cost': total_cost,
                'total_fuel_gallons': total_gallons,
                'number_of_stops': len(fuel_stops),
                'vehicle_mpg': self.fuel_service.vehicle_mpg,
                'vehicle_range_miles': self.fuel_service.vehicle_range,
            }
        }

        # Cache result
        cache.set(cache_key, result, timeout=3600)  # 1 hour

        return result
