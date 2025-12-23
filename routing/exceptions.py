"""
Custom exceptions for routing system.
Provides clear, actionable error messages for different failure scenarios.
"""


class RoutingException(Exception):
    """Base exception for all routing-related errors."""

    def __init__(self, message: str, details: dict = None):
        """
        Initialize exception with message and optional details.

        Args:
            message: Human-readable error message
            details: Additional context about the error
        """
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def to_dict(self) -> dict:
        """Convert exception to dictionary for API responses."""
        return {
            'error': self.__class__.__name__,
            'message': self.message,
            'details': self.details
        }


class GeocodingException(RoutingException):
    """Raised when geocoding fails."""
    pass


class LocationNotFoundError(GeocodingException):
    """Raised when a location cannot be geocoded."""

    def __init__(self, location: str):
        super().__init__(
            f"Could not find location: {location}",
            {'location': location}
        )
        self.location = location


class AmbiguousLocationError(GeocodingException):
    """Raised when a location string matches multiple places."""

    def __init__(self, location: str, matches: list):
        super().__init__(
            f"Location '{location}' is ambiguous. Please be more specific.",
            {'location': location, 'possible_matches': matches}
        )
        self.location = location
        self.matches = matches


class RouteCalculationException(RoutingException):
    """Raised when route calculation fails."""
    pass


class NoRouteFoundError(RouteCalculationException):
    """Raised when no route can be found between two points."""

    def __init__(self, start: str, end: str):
        super().__init__(
            f"No route found from {start} to {end}",
            {'start': start, 'end': end}
        )
        self.start = start
        self.end = end


class RouteServiceUnavailableError(RouteCalculationException):
    """Raised when routing service is unavailable."""

    def __init__(self, service_name: str, details: str = None):
        message = f"Routing service '{service_name}' is currently unavailable"
        if details:
            message += f": {details}"

        super().__init__(message, {'service': service_name, 'details': details})
        self.service_name = service_name


class FuelOptimizationException(RoutingException):
    """Raised when fuel optimization fails."""
    pass


class NoFuelStationsFoundError(FuelOptimizationException):
    """Raised when no fuel stations are found near the route."""

    def __init__(self, route_description: str):
        super().__init__(
            f"No fuel stations found along route: {route_description}",
            {'route': route_description}
        )


class InsufficientRangeError(FuelOptimizationException):
    """Raised when vehicle range is insufficient for the route."""

    def __init__(self, route_distance: float, vehicle_range: float):
        super().__init__(
            f"Vehicle range ({vehicle_range} miles) is insufficient for "
            f"route distance ({route_distance} miles) with available fuel stations",
            {
                'route_distance': route_distance,
                'vehicle_range': vehicle_range
            }
        )
        self.route_distance = route_distance
        self.vehicle_range = vehicle_range


class ValidationException(RoutingException):
    """Raised when input validation fails."""
    pass


class InvalidCoordinatesError(ValidationException):
    """Raised when coordinates are invalid."""

    def __init__(self, latitude: float, longitude: float, reason: str):
        super().__init__(
            f"Invalid coordinates ({latitude}, {longitude}): {reason}",
            {'latitude': latitude, 'longitude': longitude, 'reason': reason}
        )


class InvalidLocationError(ValidationException):
    """Raised when location string is invalid."""

    def __init__(self, location: str, reason: str):
        super().__init__(
            f"Invalid location '{location}': {reason}",
            {'location': location, 'reason': reason}
        )


class InvalidVehicleParametersError(ValidationException):
    """Raised when vehicle parameters are invalid."""

    def __init__(self, parameter: str, value: float, reason: str):
        super().__init__(
            f"Invalid vehicle parameter {parameter}={value}: {reason}",
            {'parameter': parameter, 'value': value, 'reason': reason}
        )


class DataQualityException(RoutingException):
    """Raised when data quality issues are detected."""
    pass


class CoordinateMismatchError(DataQualityException):
    """Raised when coordinates don't match the stated location."""

    def __init__(
        self,
        stated_location: str,
        coordinates: tuple,
        expected_location: str = None
    ):
        message = (
            f"Coordinates {coordinates} for '{stated_location}' appear incorrect"
        )
        if expected_location:
            message += f" (expected near {expected_location})"

        super().__init__(
            message,
            {
                'stated_location': stated_location,
                'coordinates': coordinates,
                'expected_location': expected_location
            }
        )


class PriceAnomalyError(DataQualityException):
    """Raised when fuel price appears anomalous."""

    def __init__(self, price: float, station_name: str, reason: str):
        super().__init__(
            f"Unusual price ${price:.2f} at {station_name}: {reason}",
            {'price': price, 'station': station_name, 'reason': reason}
        )


class CacheException(RoutingException):
    """Raised when cache operations fail."""
    pass


class CacheUnavailableError(CacheException):
    """Raised when cache service is unavailable."""

    def __init__(self, cache_backend: str):
        super().__init__(
            f"Cache backend '{cache_backend}' is unavailable",
            {'cache_backend': cache_backend}
        )


class RateLimitException(RoutingException):
    """Raised when rate limit is exceeded."""

    def __init__(self, service: str, retry_after: int = None):
        message = f"Rate limit exceeded for {service}"
        if retry_after:
            message += f". Retry after {retry_after} seconds."

        super().__init__(message, {'service': service, 'retry_after': retry_after})
        self.retry_after = retry_after


class ExternalServiceException(RoutingException):
    """Raised when an external service fails."""

    def __init__(
        self,
        service_name: str,
        operation: str,
        status_code: int = None,
        response_text: str = None
    ):
        message = f"{service_name} {operation} failed"
        if status_code:
            message += f" (HTTP {status_code})"

        details = {
            'service': service_name,
            'operation': operation
        }

        if status_code:
            details['status_code'] = status_code
        if response_text:
            details['response'] = response_text[:500]  # Limit response length

        super().__init__(message, details)
