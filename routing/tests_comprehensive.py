"""
Comprehensive test suite for routing system.
Tests all components with industry-standard coverage.
"""
import unittest
from decimal import Decimal
from unittest.mock import Mock, patch, MagicMock
from django.test import TestCase, RequestFactory
from django.core.exceptions import ValidationError
from rest_framework.test import APITestCase, APIClient
from rest_framework import status

from .models import FuelStation
from .validators import (
    CoordinateValidator,
    LocationValidator,
    RouteValidator,
    FuelStationValidator,
)
from .exceptions import (
    LocationNotFoundError,
    NoRouteFoundError,
    InsufficientRangeError,
    InvalidCoordinatesError,
)
from .services_enhanced import (
    EnhancedGeocodingService,
    EnhancedRoutingService,
    EnhancedFuelOptimizationService,
    EnhancedFuelRoutingService,
)


class CoordinateValidatorTests(TestCase):
    """Test coordinate validation."""

    def test_valid_latitude(self):
        """Test valid latitude values."""
        CoordinateValidator.validate_latitude(0)
        CoordinateValidator.validate_latitude(45.5)
        CoordinateValidator.validate_latitude(-45.5)
        CoordinateValidator.validate_latitude(90)
        CoordinateValidator.validate_latitude(-90)

    def test_invalid_latitude(self):
        """Test invalid latitude values."""
        with self.assertRaises(ValidationError):
            CoordinateValidator.validate_latitude(91)

        with self.assertRaises(ValidationError):
            CoordinateValidator.validate_latitude(-91)

        with self.assertRaises(ValidationError):
            CoordinateValidator.validate_latitude("invalid")

    def test_valid_longitude(self):
        """Test valid longitude values."""
        CoordinateValidator.validate_longitude(0)
        CoordinateValidator.validate_longitude(120.5)
        CoordinateValidator.validate_longitude(-120.5)
        CoordinateValidator.validate_longitude(180)
        CoordinateValidator.validate_longitude(-180)

    def test_invalid_longitude(self):
        """Test invalid longitude values."""
        with self.assertRaises(ValidationError):
            CoordinateValidator.validate_longitude(181)

        with self.assertRaises(ValidationError):
            CoordinateValidator.validate_longitude(-181)

    def test_validate_coordinates(self):
        """Test coordinate pair validation."""
        lat, lon = CoordinateValidator.validate_coordinates(34.05, -118.25)
        self.assertEqual(lat, 34.05)
        self.assertEqual(lon, -118.25)

        with self.assertRaises(ValidationError):
            CoordinateValidator.validate_coordinates(91, 0)


class LocationValidatorTests(TestCase):
    """Test location validation."""

    def test_valid_location_string(self):
        """Test valid location strings."""
        result = LocationValidator.validate_location_string("Los Angeles, CA")
        self.assertEqual(result, "Los Angeles, CA")

        result = LocationValidator.validate_location_string("New York, NY")
        self.assertEqual(result, "New York, NY")

    def test_invalid_location_string(self):
        """Test invalid location strings."""
        with self.assertRaises(ValidationError):
            LocationValidator.validate_location_string("")

        with self.assertRaises(ValidationError):
            LocationValidator.validate_location_string("  ")

        with self.assertRaises(ValidationError):
            LocationValidator.validate_location_string("AB")

        with self.assertRaises(ValidationError):
            LocationValidator.validate_location_string("x" * 300)

    def test_extract_state_code(self):
        """Test state code extraction."""
        state = LocationValidator.extract_state_code("Los Angeles, CA")
        self.assertEqual(state, "CA")

        state = LocationValidator.extract_state_code("New York, NY")
        self.assertEqual(state, "NY")

        state = LocationValidator.extract_state_code("Invalid Location")
        self.assertIsNone(state)


class RouteValidatorTests(TestCase):
    """Test route validation."""

    def test_valid_distance(self):
        """Test valid distance values."""
        RouteValidator.validate_distance(100)
        RouteValidator.validate_distance(500.5)
        RouteValidator.validate_distance(5000)

    def test_invalid_distance(self):
        """Test invalid distance values."""
        with self.assertRaises(ValidationError):
            RouteValidator.validate_distance(-10)

        with self.assertRaises(ValidationError):
            RouteValidator.validate_distance(20000)

        with self.assertRaises(ValidationError):
            RouteValidator.validate_distance("invalid")

    def test_valid_vehicle_parameters(self):
        """Test valid vehicle parameters."""
        RouteValidator.validate_vehicle_parameters(10, 500, 50)
        RouteValidator.validate_vehicle_parameters(8, 400, 50)

    def test_invalid_vehicle_parameters(self):
        """Test invalid vehicle parameters."""
        with self.assertRaises(ValidationError):
            RouteValidator.validate_vehicle_parameters(0, 500, 50)

        with self.assertRaises(ValidationError):
            RouteValidator.validate_vehicle_parameters(10, 0, 50)

        with self.assertRaises(ValidationError):
            RouteValidator.validate_vehicle_parameters(10, 500, 0)


class FuelStationValidatorTests(TestCase):
    """Test fuel station validation."""

    def test_valid_price(self):
        """Test valid fuel prices."""
        FuelStationValidator.validate_price(Decimal("3.50"))
        FuelStationValidator.validate_price(Decimal("5.99"))
        FuelStationValidator.validate_price(Decimal("2.00"))

    def test_invalid_price(self):
        """Test invalid fuel prices."""
        with self.assertRaises(ValidationError):
            FuelStationValidator.validate_price(Decimal("-1.00"))

        with self.assertRaises(ValidationError):
            FuelStationValidator.validate_price(Decimal("0.25"))

        with self.assertRaises(ValidationError):
            FuelStationValidator.validate_price(Decimal("25.00"))

    def test_validate_station_data(self):
        """Test complete station data validation."""
        data = FuelStationValidator.validate_station_data(
            name="Test Station",
            city="Los Angeles",
            state="CA",
            latitude=34.05,
            longitude=-118.25,
            price=Decimal("3.50")
        )

        self.assertEqual(data['name'], "Test Station")
        self.assertEqual(data['state'], "CA")
        self.assertEqual(data['latitude'], 34.05)


class FuelStationModelTests(TestCase):
    """Test FuelStation model."""

    def setUp(self):
        """Create test fuel station."""
        self.station = FuelStation.objects.create(
            opis_id=12345,
            name="Test Station",
            address="123 Test St",
            city="Los Angeles",
            state="CA",
            latitude=Decimal("34.0522"),
            longitude=Decimal("-118.2437"),
            retail_price=Decimal("3.499"),
            is_active=True
        )

    def test_station_creation(self):
        """Test station was created correctly."""
        self.assertEqual(self.station.name, "Test Station")
        self.assertEqual(self.station.state, "CA")
        self.assertTrue(self.station.is_active)

    def test_coordinates_property(self):
        """Test coordinates property."""
        coords = self.station.coordinates
        self.assertIsNotNone(coords)
        self.assertEqual(len(coords), 2)
        self.assertAlmostEqual(coords[0], 34.0522, places=4)
        self.assertAlmostEqual(coords[1], -118.2437, places=4)

    def test_location_dict_property(self):
        """Test location_dict property."""
        loc_dict = self.station.location_dict
        self.assertIn('latitude', loc_dict)
        self.assertIn('longitude', loc_dict)
        self.assertAlmostEqual(loc_dict['latitude'], 34.0522, places=4)

    def test_string_representation(self):
        """Test string representation."""
        string_rep = str(self.station)
        self.assertIn("Test Station", string_rep)
        self.assertIn("Los Angeles", string_rep)
        self.assertIn("CA", string_rep)


class GeocodingServiceTests(TestCase):
    """Test enhanced geocoding service."""

    @patch('routing.services_enhanced.requests.get')
    def test_successful_geocoding(self, mock_get):
        """Test successful geocoding."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [{
            'lat': '34.0522',
            'lon': '-118.2437'
        }]
        mock_get.return_value = mock_response

        service = EnhancedGeocodingService()
        coords = service.geocode_address("Los Angeles, CA")

        self.assertIsNotNone(coords)
        self.assertEqual(len(coords), 2)
        self.assertAlmostEqual(coords[0], 34.0522, places=4)
        self.assertAlmostEqual(coords[1], -118.2437, places=4)

    @patch('routing.services_enhanced.requests.get')
    def test_location_not_found(self, mock_get):
        """Test location not found error."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = []
        mock_get.return_value = mock_response

        service = EnhancedGeocodingService()

        with self.assertRaises(LocationNotFoundError):
            service.geocode_address("Invalid Location, XX")


class RoutingServiceTests(TestCase):
    """Test enhanced routing service."""

    @patch('routing.services_enhanced.requests.get')
    def test_successful_route_calculation(self, mock_get):
        """Test successful route calculation."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'code': 'Ok',
            'routes': [{
                'geometry': 'test_polyline',
                'distance': 609600,  # 378.75 miles in meters
                'duration': 21600
            }]
        }
        mock_get.return_value = mock_response

        service = EnhancedRoutingService()
        route = service.get_route((34.05, -118.24), (37.77, -122.41))

        self.assertIsNotNone(route)
        self.assertIn('geometry', route)
        self.assertIn('distance_miles', route)
        self.assertAlmostEqual(route['distance_miles'], 378.75, places=1)

    @patch('routing.services_enhanced.requests.get')
    def test_no_route_found(self, mock_get):
        """Test no route found error."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'code': 'NoRoute',
            'routes': []
        }
        mock_get.return_value = mock_response

        service = EnhancedRoutingService()

        with self.assertRaises(NoRouteFoundError):
            service.get_route((34.05, -118.24), (37.77, -122.41))


class FuelOptimizationServiceTests(TestCase):
    """Test enhanced fuel optimization service."""

    def setUp(self):
        """Create test fuel stations."""
        self.stations = [
            FuelStation.objects.create(
                opis_id=1000 + i,
                name=f"Station {i}",
                address=f"{i} Test St",
                city="Test City",
                state="CA",
                latitude=Decimal(str(34.0 + i * 0.1)),
                longitude=Decimal(str(-118.0 + i * 0.1)),
                retail_price=Decimal(str(3.50 + i * 0.10)),
                is_active=True
            )
            for i in range(5)
        ]

    def test_haversine_distance(self):
        """Test haversine distance calculation."""
        service = EnhancedFuelOptimizationService()

        # LA to SF is approximately 380 miles
        distance = service.haversine_distance(
            (34.0522, -118.2437),  # Los Angeles
            (37.7749, -122.4194)   # San Francisco
        )

        self.assertGreater(distance, 300)
        self.assertLess(distance, 450)

    def test_find_stations_near_route(self):
        """Test finding stations near route."""
        service = EnhancedFuelOptimizationService()

        route_points = [
            (34.0 + i * 0.05, -118.0 + i * 0.05)
            for i in range(10)
        ]

        stations = service.find_stations_near_route(
            route_points,
            max_distance_miles=50.0
        )

        self.assertGreater(len(stations), 0)

    def test_fuel_stop_optimization(self):
        """Test fuel stop optimization algorithm."""
        service = EnhancedFuelOptimizationService()

        route_points = [
            (34.0 + i * 0.1, -118.0 + i * 0.1)
            for i in range(50)  # ~600 mile route
        ]

        total_distance = 600

        stops, total_cost, total_gallons = service.find_optimal_fuel_stops(
            route_points,
            total_distance,
            list(self.stations)
        )

        self.assertGreater(len(stops), 0)
        self.assertGreater(total_cost, 0)
        self.assertGreater(total_gallons, 0)


class APIEndpointTests(APITestCase):
    """Test API endpoints."""

    def setUp(self):
        """Set up test client and data."""
        self.client = APIClient()

        # Create test fuel station
        self.station = FuelStation.objects.create(
            opis_id=99999,
            name="Test API Station",
            address="123 API Test St",
            city="Los Angeles",
            state="CA",
            latitude=Decimal("34.0522"),
            longitude=Decimal("-118.2437"),
            retail_price=Decimal("3.499"),
            is_active=True
        )

    def test_health_check(self):
        """Test health check endpoint."""
        response = self.client.get('/api/health/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('status', response.data)

    def test_list_fuel_stations(self):
        """Test listing fuel stations."""
        response = self.client.get('/api/stations/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)

    def test_get_fuel_station_detail(self):
        """Test getting fuel station detail."""
        response = self.client.get(f'/api/stations/{self.station.id}/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], "Test API Station")

    def test_cheapest_stations(self):
        """Test getting cheapest stations."""
        response = self.client.get('/api/stations/cheapest/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @patch('routing.services_enhanced.EnhancedFuelRoutingService.plan_route')
    def test_plan_route_success(self, mock_plan_route):
        """Test successful route planning."""
        mock_plan_route.return_value = {
            'start_location': 'Los Angeles, CA',
            'end_location': 'San Francisco, CA',
            'start_coordinates': {'latitude': 34.05, 'longitude': -118.24},
            'end_coordinates': {'latitude': 37.77, 'longitude': -122.41},
            'route': {
                'geometry': 'test_polyline',
                'distance_miles': 380.5,
                'duration_seconds': 21600.0
            },
            'fuel_stops': [],
            'summary': {
                'total_distance_miles': 380.5,
                'total_fuel_cost': 150.0,
                'total_fuel_gallons': 38.0,
                'number_of_stops': 1,
                'vehicle_mpg': 10.0,
                'vehicle_range_miles': 500.0,
                'stations_searched': 50
            }
        }

        response = self.client.post(
            '/api/plan-route/',
            {
                'start_location': 'Los Angeles, CA',
                'end_location': 'San Francisco, CA'
            },
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('route', response.data)
        self.assertIn('fuel_stops', response.data)

    def test_plan_route_invalid_data(self):
        """Test route planning with invalid data."""
        response = self.client.post(
            '/api/plan-route/',
            {
                'start_location': '',
                'end_location': 'San Francisco, CA'
            },
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class IntegrationTests(TestCase):
    """Integration tests for complete workflows."""

    def setUp(self):
        """Create test data."""
        # Create multiple fuel stations along I-5 corridor
        self.stations = []
        cities = [
            ("Los Angeles", 34.05, -118.24),
            ("Bakersfield", 35.37, -119.02),
            ("Fresno", 36.75, -119.77),
            ("San Jose", 37.34, -121.89),
            ("San Francisco", 37.77, -122.42),
        ]

        for i, (city, lat, lon) in enumerate(cities):
            station = FuelStation.objects.create(
                opis_id=2000 + i,
                name=f"{city} Station",
                address=f"{i} Test St",
                city=city,
                state="CA",
                latitude=Decimal(str(lat)),
                longitude=Decimal(str(lon)),
                retail_price=Decimal(str(3.50 + i * 0.05)),
                is_active=True
            )
            self.stations.append(station)

    @patch('routing.services_enhanced.EnhancedGeocodingService.geocode_address')
    @patch('routing.services_enhanced.EnhancedRoutingService.get_route')
    def test_complete_route_planning_workflow(
        self,
        mock_get_route,
        mock_geocode
    ):
        """Test complete route planning workflow."""
        # Mock geocoding
        mock_geocode.side_effect = [
            (34.05, -118.24),  # Los Angeles
            (37.77, -122.42),  # San Francisco
        ]

        # Mock routing
        mock_get_route.return_value = {
            'geometry': 'test_polyline',
            'distance_miles': 380.0,
            'duration_seconds': 21600.0,
            'distance_meters': 611552.0
        }

        # Mock polyline decoding
        with patch.object(
            EnhancedRoutingService,
            'decode_polyline',
            return_value=[
                (34.05 + i * 0.074, -118.24 + i * 0.084)
                for i in range(50)
            ]
        ):
            # Run route planning
            service = EnhancedFuelRoutingService()
            result = service.plan_route("Los Angeles, CA", "San Francisco, CA")

            # Verify result structure
            self.assertIn('start_location', result)
            self.assertIn('end_location', result)
            self.assertIn('route', result)
            self.assertIn('fuel_stops', result)
            self.assertIn('summary', result)

            # Verify data
            self.assertEqual(result['start_location'], "Los Angeles, CA")
            self.assertEqual(result['end_location'], "San Francisco, CA")
            self.assertGreater(result['summary']['total_distance_miles'], 0)


if __name__ == '__main__':
    unittest.main()
