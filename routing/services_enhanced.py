"""
Production-grade routing and fuel optimization services.
Includes comprehensive error handling, retry logic, validation, and monitoring.
"""
import requests
import math
import logging
from typing import List, Dict, Tuple, Optional
from decimal import Decimal
from django.conf import settings
from django.core.cache import cache
from django.core.exceptions import ValidationError

from .models import FuelStation, RouteCache
from .exceptions import (
    LocationNotFoundError,
    NoRouteFoundError,
    RouteServiceUnavailableError,
    NoFuelStationsFoundError,
    InsufficientRangeError,
    ExternalServiceException,
    CoordinateMismatchError,
)
from .validators import (
    CoordinateValidator,
    LocationValidator,
    RouteValidator,
    FuelStationValidator,
)
from .utils import retry_on_failure, PerformanceTimer

logger = logging.getLogger(__name__)


class EnhancedGeocodingService:
    """
    Production-grade geocoding service with retry logic,
    caching, and comprehensive error handling.
    """

    def __init__(self):
        self.base_url = "https://nominatim.openstreetmap.org/search"
        self.timeout = 10
        self.cache_timeout = 86400  # 24 hours

    @retry_on_failure(max_retries=3, delay_seconds=1.0)
    def geocode_address(self, address: str) -> Tuple[float, float]:
        """
        Convert address to coordinates with validation and error handling.

        Args:
            address: Location string (e.g., "Los Angeles, CA")

        Returns:
            Tuple of (latitude, longitude)

        Raises:
            LocationNotFoundError: If location cannot be geocoded
            ValidationError: If address format is invalid
        """
        # Validate input
        try:
            normalized_address = LocationValidator.validate_location_string(address)
        except ValidationError as e:
            logger.error(f"Invalid address format: {address}")
            raise

        # Check cache first
        cache_key = f"geocode:{normalized_address.lower().replace(' ', '_')}"
        cached = cache.get(cache_key)

        if cached:
            logger.info(f"Cache hit for geocoding: {normalized_address}")
            return cached

        with PerformanceTimer(f"Geocoding: {normalized_address}"):
            try:
                params = {
                    'q': f"{normalized_address}, USA",
                    'format': 'json',
                    'limit': 1,
                    'addressdetails': 1,
                }
                headers = {
                    'User-Agent': 'SpotterAI-FuelRouting/2.0'
                }

                response = requests.get(
                    self.base_url,
                    params=params,
                    headers=headers,
                    timeout=self.timeout
                )

                # Check for rate limiting
                if response.status_code == 429:
                    raise ExternalServiceException(
                        'Nominatim',
                        'geocoding',
                        status_code=429,
                        response_text='Rate limited'
                    )

                response.raise_for_status()
                data = response.json()

                if not data:
                    raise LocationNotFoundError(normalized_address)

                result = data[0]
                lat = float(result['lat'])
                lon = float(result['lon'])

                # Validate coordinates
                coords = CoordinateValidator.validate_coordinates(lat, lon)

                # Cache successful result
                cache.set(cache_key, coords, timeout=self.cache_timeout)

                logger.info(f"Geocoded '{normalized_address}' to {coords}")
                return coords

            except requests.Timeout:
                logger.error(f"Geocoding timeout for: {normalized_address}")
                raise RouteServiceUnavailableError(
                    'Nominatim',
                    'Request timeout'
                )

            except requests.RequestException as e:
                logger.error(f"Geocoding request failed: {str(e)}")
                raise RouteServiceUnavailableError(
                    'Nominatim',
                    str(e)
                )

            except (KeyError, ValueError, IndexError) as e:
                logger.error(f"Geocoding response parsing error: {str(e)}")
                raise LocationNotFoundError(normalized_address)


class EnhancedRoutingService:
    """
    Production-grade routing service with circuit breaker pattern,
    retry logic, and comprehensive error handling.
    """

    def __init__(self):
        self.base_url = "http://router.project-osrm.org"
        self.timeout = 30
        self.cache_timeout = 3600  # 1 hour
        self.max_waypoints = 10

    @retry_on_failure(max_retries=3, delay_seconds=2.0, backoff=2.0)
    def get_route(
        self,
        start_coords: Tuple[float, float],
        end_coords: Tuple[float, float],
        waypoints: Optional[List[Tuple[float, float]]] = None
    ) -> Dict:
        """
        Calculate route with comprehensive error handling and validation.

        Args:
            start_coords: Starting coordinates (lat, lon)
            end_coords: Ending coordinates (lat, lon)
            waypoints: Optional intermediate waypoints

        Returns:
            Dictionary with route geometry, distance, and duration

        Raises:
            NoRouteFoundError: If no route can be found
            RouteServiceUnavailableError: If routing service fails
        """
        # Validate coordinates
        start_coords = CoordinateValidator.validate_coordinates(*start_coords)
        end_coords = CoordinateValidator.validate_coordinates(*end_coords)

        if waypoints:
            if len(waypoints) > self.max_waypoints:
                logger.warning(
                    f"Too many waypoints ({len(waypoints)}), "
                    f"limiting to {self.max_waypoints}"
                )
                waypoints = waypoints[:self.max_waypoints]

            waypoints = [
                CoordinateValidator.validate_coordinates(*wp)
                for wp in waypoints
            ]

        # Generate cache key
        cache_key = (
            f"route:{start_coords[0]:.4f},{start_coords[1]:.4f}"
            f":{end_coords[0]:.4f},{end_coords[1]:.4f}"
        )

        # Check cache
        cached = cache.get(cache_key)
        if cached:
            logger.info("Cache hit for route calculation")
            return cached

        with PerformanceTimer("Route calculation"):
            try:
                # Build coordinate string: lon,lat;lon,lat (OSRM format)
                coords_str = f"{start_coords[1]},{start_coords[0]}"

                if waypoints:
                    for wp in waypoints:
                        coords_str += f";{wp[1]},{wp[0]}"

                coords_str += f";{end_coords[1]},{end_coords[0]}"

                url = f"{self.base_url}/route/v1/driving/{coords_str}"
                params = {
                    'overview': 'full',
                    'geometries': 'polyline',
                    'steps': 'false',
                    'alternatives': 'false',
                }

                logger.info(f"Requesting route from OSRM...")

                response = requests.get(url, params=params, timeout=self.timeout)

                if response.status_code == 429:
                    raise ExternalServiceException(
                        'OSRM',
                        'routing',
                        status_code=429,
                        response_text='Rate limited'
                    )

                response.raise_for_status()
                data = response.json()

                if data.get('code') != 'Ok':
                    error_code = data.get('code', 'Unknown')
                    logger.error(f"OSRM returned error code: {error_code}")

                    if error_code == 'NoRoute':
                        raise NoRouteFoundError(
                            f"{start_coords}",
                            f"{end_coords}"
                        )

                    raise RouteServiceUnavailableError('OSRM', error_code)

                if not data.get('routes'):
                    raise NoRouteFoundError(
                        f"{start_coords}",
                        f"{end_coords}"
                    )

                route = data['routes'][0]

                # Extract and validate route data
                distance_meters = route.get('distance', 0)
                duration_seconds = route.get('duration', 0)
                geometry = route.get('geometry', '')

                if not geometry:
                    raise NoRouteFoundError(
                        f"{start_coords}",
                        f"{end_coords}"
                    )

                # Convert meters to miles
                distance_miles = distance_meters * 0.000621371

                # Validate distance
                RouteValidator.validate_distance(distance_miles)

                result = {
                    'geometry': geometry,
                    'distance_miles': round(distance_miles, 2),
                    'duration_seconds': round(duration_seconds, 1),
                    'distance_meters': distance_meters,
                }

                # Cache result
                cache.set(cache_key, result, timeout=self.cache_timeout)

                logger.info(
                    f"Route calculated: {distance_miles:.1f} miles, "
                    f"{duration_seconds/3600:.1f} hours"
                )

                return result

            except requests.Timeout:
                logger.error("OSRM request timeout")
                raise RouteServiceUnavailableError('OSRM', 'Request timeout')

            except requests.RequestException as e:
                logger.error(f"OSRM request failed: {str(e)}")
                raise RouteServiceUnavailableError('OSRM', str(e))

    def decode_polyline(self, encoded: str) -> List[Tuple[float, float]]:
        """
        Decode polyline with error handling.

        Args:
            encoded: Encoded polyline string

        Returns:
            List of (lat, lon) coordinate tuples
        """
        if not encoded:
            return []

        coordinates = []
        index = 0
        lat = 0
        lon = 0

        try:
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

        except (IndexError, ValueError) as e:
            logger.error(f"Polyline decoding error: {str(e)}")
            raise ValueError(f"Invalid polyline encoding: {str(e)}")

        logger.info(f"Decoded polyline: {len(coordinates)} points")
        return coordinates


class EnhancedFuelOptimizationService:
    """
    Production-grade fuel optimization with advanced algorithms,
    validation, and comprehensive error handling.
    """

    def __init__(self):
        self.vehicle_range = getattr(settings, 'VEHICLE_RANGE_MILES', 500)
        self.vehicle_mpg = getattr(settings, 'VEHICLE_MPG', 10)
        self.tank_capacity = self.vehicle_range / self.vehicle_mpg
        self.safety_margin = 0.9  # Use 90% of range for safety

        # Validate vehicle parameters
        RouteValidator.validate_vehicle_parameters(
            self.vehicle_mpg,
            self.vehicle_range,
            self.tank_capacity
        )

        logger.info(
            f"Fuel optimizer initialized: MPG={self.vehicle_mpg}, "
            f"Range={self.vehicle_range}mi, Capacity={self.tank_capacity}gal"
        )

    def haversine_distance(
        self,
        coord1: Tuple[float, float],
        coord2: Tuple[float, float]
    ) -> float:
        """
        Calculate great-circle distance between two points.

        Args:
            coord1: First coordinate (lat, lon)
            coord2: Second coordinate (lat, lon)

        Returns:
            Distance in miles
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
        max_distance_miles: float = 15.0
    ) -> List[FuelStation]:
        """
        Find fuel stations near route with optimized spatial queries.

        Args:
            route_points: List of (lat, lon) points along route
            max_distance_miles: Maximum detour distance from route

        Returns:
            List of FuelStation objects

        Raises:
            NoFuelStationsFoundError: If no stations found
        """
        with PerformanceTimer("Finding stations near route"):
            stations_near_route = set()

            # Sample route points for performance
            sample_interval = max(1, len(route_points) // 50)
            sampled_points = route_points[::sample_interval]

            logger.info(
                f"Searching for stations near {len(sampled_points)} "
                f"sampled route points"
            )

            for point in sampled_points:
                lat, lon = point

                # Calculate bounding box
                lat_delta = max_distance_miles / 69.0
                lon_delta = max_distance_miles / (
                    69.0 * max(math.cos(math.radians(lat)), 0.01)
                )

                # Query database
                stations = FuelStation.objects.filter(
                    latitude__isnull=False,
                    longitude__isnull=False,
                    is_active=True,
                    latitude__gte=lat - lat_delta,
                    latitude__lte=lat + lat_delta,
                    longitude__gte=lon - lon_delta,
                    longitude__lte=lon + lon_delta,
                ).select_related()

                # Verify actual distance
                for station in stations:
                    if station.coordinates:
                        try:
                            distance = self.haversine_distance(
                                point,
                                station.coordinates
                            )
                            if distance <= max_distance_miles:
                                stations_near_route.add(station)
                        except Exception as e:
                            logger.warning(
                                f"Error calculating distance for station "
                                f"{station.id}: {str(e)}"
                            )

            stations_list = list(stations_near_route)
            logger.info(f"Found {len(stations_list)} stations near route")

            if not stations_list:
                raise NoFuelStationsFoundError("route")

            return stations_list

    def find_optimal_fuel_stops(
        self,
        route_points: List[Tuple[float, float]],
        total_distance: float,
        available_stations: List[FuelStation]
    ) -> Tuple[List[Dict], float, float]:
        """
        Find optimal fuel stops using greedy algorithm with cost minimization.

        Args:
            route_points: Route geometry points
            total_distance: Total route distance in miles
            available_stations: List of available fuel stations

        Returns:
            Tuple of (fuel_stops, total_cost, total_gallons)

        Raises:
            InsufficientRangeError: If route cannot be completed
        """
        with PerformanceTimer("Optimizing fuel stops"):
            if not available_stations:
                raise NoFuelStationsFoundError("route")

            # Map stations to route positions
            station_positions = self._map_stations_to_route(
                available_stations,
                route_points
            )

            # Sort by distance from start
            station_positions.sort(key=lambda x: x['distance_from_start'])

            # Dynamic programming for optimal stops
            selected_stops = []
            current_fuel = self.tank_capacity  # Start with full tank
            current_position = 0.0
            total_cost = 0.0
            total_gallons = 0.0
            effective_range = self.vehicle_range * self.safety_margin

            iteration = 0
            max_iterations = 1000  # Prevent infinite loops

            while current_position < total_distance and iteration < max_iterations:
                iteration += 1

                remaining_distance = total_distance - current_position
                distance_on_current_fuel = current_fuel * self.vehicle_mpg

                # Check if we can reach destination
                if distance_on_current_fuel >= remaining_distance:
                    logger.info("Can reach destination without refueling")
                    break

                # Find stations within range
                reachable_stations = [
                    sp for sp in station_positions
                    if (
                        current_position < sp['distance_from_start'] <=
                        current_position + effective_range
                    )
                ]

                if not reachable_stations:
                    # Try to find ANY station we can reach
                    reachable_stations = [
                        sp for sp in station_positions
                        if current_position < sp['distance_from_start'] <=
                        current_position + self.vehicle_range
                    ]

                    if not reachable_stations:
                        raise InsufficientRangeError(
                            total_distance,
                            self.vehicle_range
                        )

                # Choose cheapest station in range
                best_station = min(reachable_stations, key=lambda x: x['price'])

                # Calculate fuel consumption to reach station
                distance_to_station = (
                    best_station['distance_from_start'] - current_position
                )
                fuel_needed = distance_to_station / self.vehicle_mpg
                current_fuel -= fuel_needed

                if current_fuel < 0:
                    logger.error("Ran out of fuel before reaching station")
                    raise InsufficientRangeError(
                        total_distance,
                        self.vehicle_range
                    )

                # Refuel to full tank
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
                    'price_per_gallon': round(best_station['price'], 3),
                    'gallons': round(gallons_to_add, 2),
                    'cost': round(cost, 2),
                    'distance_from_start': round(
                        best_station['distance_from_start'], 2
                    ),
                })

                total_cost += cost
                total_gallons += gallons_to_add
                current_fuel = self.tank_capacity
                current_position = best_station['distance_from_start']

                # Remove used station
                station_positions.remove(best_station)

                logger.info(
                    f"Selected stop {len(selected_stops)}: "
                    f"{best_station['station'].name} at "
                    f"{best_station['distance_from_start']:.1f}mi, "
                    f"${best_station['price']:.2f}/gal"
                )

            logger.info(
                f"Optimized route: {len(selected_stops)} stops, "
                f"${total_cost:.2f} total cost, "
                f"{total_gallons:.1f} gallons"
            )

            return (
                selected_stops,
                round(total_cost, 2),
                round(total_gallons, 2)
            )

    def _map_stations_to_route(
        self,
        stations: List[FuelStation],
        route_points: List[Tuple[float, float]]
    ) -> List[Dict]:
        """Map each station to its closest point on the route."""
        station_positions = []

        # Sample route points for performance
        sample_interval = max(1, len(route_points) // 100)
        sampled_points = route_points[::sample_interval]

        for station in stations:
            if not station.coordinates:
                continue

            # Find closest route point
            min_distance = float('inf')
            closest_point_idx = 0

            for i, route_point in enumerate(sampled_points):
                actual_idx = i * sample_interval
                dist = self.haversine_distance(
                    station.coordinates,
                    route_point
                )
                if dist < min_distance:
                    min_distance = dist
                    closest_point_idx = actual_idx

            # Calculate distance from route start
            distance_from_start = sum(
                self.haversine_distance(
                    route_points[i],
                    route_points[i + 1]
                )
                for i in range(min(closest_point_idx, len(route_points) - 1))
            )

            station_positions.append({
                'station': station,
                'distance_from_start': distance_from_start,
                'price': float(station.retail_price),
                'detour_distance': min_distance,
            })

        return station_positions


class EnhancedFuelRoutingService:
    """
    Main orchestration service with comprehensive error handling,
    validation, and production-grade features.
    """

    def __init__(self):
        self.geocoding_service = EnhancedGeocodingService()
        self.routing_service = EnhancedRoutingService()
        self.fuel_service = EnhancedFuelOptimizationService()

    def plan_route(
        self,
        start_location: str,
        end_location: str,
        use_cache: bool = True
    ) -> Dict:
        """
        Plan optimal route with comprehensive error handling.

        Args:
            start_location: Starting location string
            end_location: Ending location string
            use_cache: Whether to use cached results

        Returns:
            Complete route data with fuel stops

        Raises:
            Various routing exceptions on failure
        """
        with PerformanceTimer(
            f"Complete route planning: {start_location} -> {end_location}"
        ):
            # Validate inputs
            start_location = LocationValidator.validate_location_string(
                start_location
            )
            end_location = LocationValidator.validate_location_string(
                end_location
            )

            # Check cache
            if use_cache:
                cache_key = f"full_route:{start_location}:{end_location}"
                cached = cache.get(cache_key)
                if cached:
                    logger.info("Using cached route plan")
                    return cached

            # Geocode locations
            logger.info(f"Geocoding: {start_location}")
            start_coords = self.geocoding_service.geocode_address(start_location)

            logger.info(f"Geocoding: {end_location}")
            end_coords = self.geocoding_service.geocode_address(end_location)

            # Get route
            route_data = self.routing_service.get_route(
                start_coords,
                end_coords
            )

            # Decode geometry
            route_points = self.routing_service.decode_polyline(
                route_data['geometry']
            )

            # Find stations
            stations_near_route = self.fuel_service.find_stations_near_route(
                route_points
            )

            # Optimize fuel stops
            fuel_stops, total_cost, total_gallons = (
                self.fuel_service.find_optimal_fuel_stops(
                    route_points,
                    route_data['distance_miles'],
                    stations_near_route
                )
            )

            # Build result
            result = {
                'start_location': start_location,
                'end_location': end_location,
                'start_coordinates': {
                    'latitude': start_coords[0],
                    'longitude': start_coords[1]
                },
                'end_coordinates': {
                    'latitude': end_coords[0],
                    'longitude': end_coords[1]
                },
                'route': {
                    'geometry': route_data['geometry'],
                    'distance_miles': route_data['distance_miles'],
                    'duration_seconds': route_data['duration_seconds'],
                },
                'fuel_stops': fuel_stops,
                'summary': {
                    'total_distance_miles': route_data['distance_miles'],
                    'total_fuel_cost': total_cost,
                    'total_fuel_gallons': total_gallons,
                    'number_of_stops': len(fuel_stops),
                    'vehicle_mpg': self.fuel_service.vehicle_mpg,
                    'vehicle_range_miles': self.fuel_service.vehicle_range,
                    'stations_searched': len(stations_near_route),
                }
            }

            # Cache result
            if use_cache:
                cache.set(cache_key, result, timeout=3600)

            logger.info(
                f"Route planning complete: {result['summary']['total_distance_miles']:.1f} miles, "
                f"{result['summary']['number_of_stops']} stops, "
                f"${result['summary']['total_fuel_cost']:.2f}"
            )

            return result
