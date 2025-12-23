"""
Production-grade validators for route optimization system.
Ensures data integrity and prevents invalid inputs.
"""
from typing import Tuple, Optional
from decimal import Decimal
import re
from django.core.exceptions import ValidationError


class CoordinateValidator:
    """Validates geographic coordinates."""

    @staticmethod
    def validate_latitude(lat: float) -> None:
        """
        Validate latitude is within valid range [-90, 90].

        Args:
            lat: Latitude value to validate

        Raises:
            ValidationError: If latitude is invalid
        """
        if not isinstance(lat, (int, float, Decimal)):
            raise ValidationError(f"Latitude must be numeric, got {type(lat)}")

        if not -90 <= float(lat) <= 90:
            raise ValidationError(f"Latitude must be between -90 and 90, got {lat}")

    @staticmethod
    def validate_longitude(lon: float) -> None:
        """
        Validate longitude is within valid range [-180, 180].

        Args:
            lon: Longitude value to validate

        Raises:
            ValidationError: If longitude is invalid
        """
        if not isinstance(lon, (int, float, Decimal)):
            raise ValidationError(f"Longitude must be numeric, got {type(lon)}")

        if not -180 <= float(lon) <= 180:
            raise ValidationError(f"Longitude must be between -180 and 180, got {lon}")

    @staticmethod
    def validate_coordinates(lat: float, lon: float) -> Tuple[float, float]:
        """
        Validate both latitude and longitude.

        Args:
            lat: Latitude value
            lon: Longitude value

        Returns:
            Tuple of validated (latitude, longitude)

        Raises:
            ValidationError: If either coordinate is invalid
        """
        CoordinateValidator.validate_latitude(lat)
        CoordinateValidator.validate_longitude(lon)
        return (float(lat), float(lon))

    @staticmethod
    def coordinates_match_location(
        coords: Tuple[float, float],
        expected_city: str,
        expected_state: str,
        tolerance_miles: float = 50.0
    ) -> bool:
        """
        Verify coordinates are reasonably close to expected location.

        This prevents data quality issues like the El Centro coordinate mismatch
        in your example data.

        Args:
            coords: (latitude, longitude) tuple
            expected_city: Expected city name
            expected_state: Expected state code
            tolerance_miles: Maximum acceptable distance from expected location

        Returns:
            True if coordinates are within tolerance
        """
        # This would require a geocoding service or database of city coordinates
        # For now, we'll implement basic state boundary checking
        from .utils import get_state_boundaries

        lat, lon = coords
        state_bounds = get_state_boundaries(expected_state)

        if not state_bounds:
            return True  # Can't verify, assume valid

        return (
            state_bounds['min_lat'] <= lat <= state_bounds['max_lat'] and
            state_bounds['min_lon'] <= lon <= state_bounds['max_lon']
        )


class LocationValidator:
    """Validates location strings and addresses."""

    # Common US location patterns
    CITY_STATE_PATTERN = re.compile(r'^[A-Za-z\s\-\.]+,\s*[A-Z]{2}$')
    STATE_CODES = {
        'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA',
        'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD',
        'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ',
        'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC',
        'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY', 'DC'
    }

    @staticmethod
    def validate_location_string(location: str) -> str:
        """
        Validate and normalize location string.

        Args:
            location: Location string (e.g., "Los Angeles, CA")

        Returns:
            Normalized location string

        Raises:
            ValidationError: If location format is invalid
        """
        if not location or not isinstance(location, str):
            raise ValidationError("Location must be a non-empty string")

        location = location.strip()

        if len(location) < 3:
            raise ValidationError("Location string too short")

        if len(location) > 255:
            raise ValidationError("Location string too long (max 255 characters)")

        # Check for common format: "City, ST"
        if ',' in location:
            parts = location.split(',')
            if len(parts) == 2:
                city, state = parts
                state = state.strip().upper()

                if state in LocationValidator.STATE_CODES:
                    return f"{city.strip()}, {state}"

        return location

    @staticmethod
    def extract_state_code(location: str) -> Optional[str]:
        """
        Extract state code from location string if present.

        Args:
            location: Location string

        Returns:
            State code or None
        """
        if ',' in location:
            parts = location.split(',')
            if len(parts) >= 2:
                state = parts[-1].strip().upper()
                if state in LocationValidator.STATE_CODES:
                    return state
        return None


class RouteValidator:
    """Validates route parameters and constraints."""

    @staticmethod
    def validate_distance(distance_miles: float) -> None:
        """
        Validate route distance is reasonable.

        Args:
            distance_miles: Route distance in miles

        Raises:
            ValidationError: If distance is invalid
        """
        if not isinstance(distance_miles, (int, float)):
            raise ValidationError("Distance must be numeric")

        if distance_miles < 0:
            raise ValidationError("Distance cannot be negative")

        if distance_miles > 10000:  # Max ~10,000 miles for US routes
            raise ValidationError(
                f"Distance {distance_miles} miles exceeds maximum (10,000 miles)"
            )

        if distance_miles < 0.1:  # Min ~0.1 miles
            raise ValidationError("Distance too short for routing")

    @staticmethod
    def validate_vehicle_parameters(
        mpg: float,
        range_miles: float,
        tank_capacity: Optional[float] = None
    ) -> None:
        """
        Validate vehicle parameters are reasonable.

        Args:
            mpg: Miles per gallon
            range_miles: Vehicle range in miles
            tank_capacity: Tank capacity in gallons (optional)

        Raises:
            ValidationError: If parameters are invalid
        """
        if mpg <= 0:
            raise ValidationError("MPG must be positive")

        if mpg > 100:  # Unrealistic for trucks
            raise ValidationError("MPG exceeds realistic maximum (100)")

        if range_miles <= 0:
            raise ValidationError("Range must be positive")

        if range_miles > 2000:  # Unrealistic for most vehicles
            raise ValidationError("Range exceeds realistic maximum (2000 miles)")

        if tank_capacity is not None:
            if tank_capacity <= 0:
                raise ValidationError("Tank capacity must be positive")

            if tank_capacity > 500:  # Unrealistic for most vehicles
                raise ValidationError("Tank capacity exceeds realistic maximum (500 gallons)")

            # Verify range = mpg * capacity
            expected_range = mpg * tank_capacity
            if abs(expected_range - range_miles) > 1.0:
                raise ValidationError(
                    f"Range ({range_miles}) doesn't match MPG ({mpg}) × "
                    f"capacity ({tank_capacity}) = {expected_range}"
                )


class FuelStationValidator:
    """Validates fuel station data."""

    @staticmethod
    def validate_price(price: Decimal) -> None:
        """
        Validate fuel price is reasonable.

        Args:
            price: Fuel price per gallon

        Raises:
            ValidationError: If price is invalid
        """
        if not isinstance(price, (int, float, Decimal)):
            raise ValidationError("Price must be numeric")

        price_float = float(price)

        if price_float < 0:
            raise ValidationError("Price cannot be negative")

        if price_float < 0.50:  # Unrealistically cheap
            raise ValidationError(f"Price ${price_float} is unrealistically low")

        if price_float > 20.00:  # Unrealistically expensive
            raise ValidationError(f"Price ${price_float} exceeds maximum ($20/gal)")

    @staticmethod
    def validate_station_data(
        name: str,
        city: str,
        state: str,
        latitude: float,
        longitude: float,
        price: Decimal
    ) -> dict:
        """
        Validate complete fuel station data.

        Args:
            name: Station name
            city: City name
            state: State code
            latitude: Station latitude
            longitude: Station longitude
            price: Fuel price per gallon

        Returns:
            Dictionary of validated data

        Raises:
            ValidationError: If any field is invalid
        """
        errors = []

        # Validate name
        if not name or not name.strip():
            errors.append("Station name cannot be empty")
        elif len(name) > 255:
            errors.append("Station name too long (max 255 characters)")

        # Validate city
        if not city or not city.strip():
            errors.append("City cannot be empty")
        elif len(city) > 100:
            errors.append("City name too long (max 100 characters)")

        # Validate state
        if state.upper() not in LocationValidator.STATE_CODES:
            errors.append(f"Invalid state code: {state}")

        # Validate coordinates
        try:
            CoordinateValidator.validate_coordinates(latitude, longitude)
        except ValidationError as e:
            errors.append(str(e))

        # Validate price
        try:
            FuelStationValidator.validate_price(price)
        except ValidationError as e:
            errors.append(str(e))

        # Check coordinate-location consistency
        try:
            if not CoordinateValidator.coordinates_match_location(
                (latitude, longitude), city, state
            ):
                errors.append(
                    f"Coordinates ({latitude}, {longitude}) appear inconsistent "
                    f"with location {city}, {state}"
                )
        except Exception:
            pass  # Don't fail on verification errors

        if errors:
            raise ValidationError("; ".join(errors))

        return {
            'name': name.strip(),
            'city': city.strip(),
            'state': state.upper(),
            'latitude': float(latitude),
            'longitude': float(longitude),
            'price': Decimal(str(price))
        }
