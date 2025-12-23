"""
Utility functions for routing and geospatial operations.
"""
from typing import Dict, Optional, Tuple
import functools
import time
import logging

logger = logging.getLogger(__name__)


# State boundary data for coordinate validation
STATE_BOUNDARIES = {
    'CA': {'min_lat': 32.5, 'max_lat': 42.0, 'min_lon': -124.5, 'max_lon': -114.0},
    'NY': {'min_lat': 40.5, 'max_lat': 45.0, 'min_lon': -79.8, 'max_lon': -71.8},
    'TX': {'min_lat': 25.8, 'max_lat': 36.5, 'min_lon': -106.6, 'max_lon': -93.5},
    'FL': {'min_lat': 24.5, 'max_lat': 31.0, 'min_lon': -87.6, 'max_lon': -80.0},
    'IL': {'min_lat': 37.0, 'max_lat': 42.5, 'min_lon': -91.5, 'max_lon': -87.5},
    'WA': {'min_lat': 45.5, 'max_lat': 49.0, 'min_lon': -124.8, 'max_lon': -116.9},
    # Add more states as needed
}


def get_state_boundaries(state_code: str) -> Optional[Dict]:
    """
    Get geographic boundaries for a US state.

    Args:
        state_code: Two-letter state code (e.g., 'CA', 'NY')

    Returns:
        Dictionary with min/max lat/lon or None if not available
    """
    return STATE_BOUNDARIES.get(state_code.upper())


def retry_on_failure(max_retries: int = 3, delay_seconds: float = 1.0, backoff: float = 2.0):
    """
    Decorator to retry a function on failure with exponential backoff.

    Args:
        max_retries: Maximum number of retry attempts
        delay_seconds: Initial delay between retries in seconds
        backoff: Multiplier for delay after each retry

    Usage:
        @retry_on_failure(max_retries=3, delay_seconds=1.0)
        def my_function():
            # Function that might fail
            pass
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            retries = 0
            current_delay = delay_seconds

            while retries < max_retries:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    retries += 1
                    if retries >= max_retries:
                        logger.error(
                            f"{func.__name__} failed after {max_retries} retries: {str(e)}"
                        )
                        raise

                    logger.warning(
                        f"{func.__name__} failed (attempt {retries}/{max_retries}), "
                        f"retrying in {current_delay}s: {str(e)}"
                    )
                    time.sleep(current_delay)
                    current_delay *= backoff

            return None
        return wrapper
    return decorator


def calculate_bearing(
    coord1: Tuple[float, float],
    coord2: Tuple[float, float]
) -> float:
    """
    Calculate bearing between two coordinates.

    Args:
        coord1: Starting coordinate (lat, lon)
        coord2: Ending coordinate (lat, lon)

    Returns:
        Bearing in degrees (0-360)
    """
    import math

    lat1, lon1 = math.radians(coord1[0]), math.radians(coord1[1])
    lat2, lon2 = math.radians(coord2[0]), math.radians(coord2[1])

    dlon = lon2 - lon1

    x = math.sin(dlon) * math.cos(lat2)
    y = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(dlon)

    initial_bearing = math.atan2(x, y)
    initial_bearing = math.degrees(initial_bearing)
    compass_bearing = (initial_bearing + 360) % 360

    return compass_bearing


def format_distance(distance_miles: float) -> str:
    """
    Format distance for human-readable display.

    Args:
        distance_miles: Distance in miles

    Returns:
        Formatted string (e.g., "123.5 miles" or "0.5 miles")
    """
    if distance_miles < 1:
        feet = distance_miles * 5280
        return f"{feet:.0f} feet"
    else:
        return f"{distance_miles:.1f} miles"


def format_duration(duration_seconds: float) -> str:
    """
    Format duration for human-readable display.

    Args:
        duration_seconds: Duration in seconds

    Returns:
        Formatted string (e.g., "2h 30m" or "45m")
    """
    hours = int(duration_seconds // 3600)
    minutes = int((duration_seconds % 3600) // 60)

    if hours > 0:
        return f"{hours}h {minutes}m"
    else:
        return f"{minutes}m"


def format_price(price: float) -> str:
    """
    Format price for display.

    Args:
        price: Price in dollars

    Returns:
        Formatted string (e.g., "$3.45")
    """
    return f"${price:.2f}"


class PerformanceTimer:
    """Context manager for timing code execution."""

    def __init__(self, name: str, log_level: int = logging.INFO):
        """
        Initialize timer.

        Args:
            name: Name of the operation being timed
            log_level: Logging level for output
        """
        self.name = name
        self.log_level = log_level
        self.start_time = None
        self.end_time = None

    def __enter__(self):
        """Start timer."""
        self.start_time = time.time()
        logger.log(self.log_level, f"{self.name} started")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Stop timer and log duration."""
        self.end_time = time.time()
        duration = self.end_time - self.start_time

        if exc_type is None:
            logger.log(
                self.log_level,
                f"{self.name} completed in {duration:.3f}s"
            )
        else:
            logger.error(
                f"{self.name} failed after {duration:.3f}s: {exc_val}"
            )

        return False  # Don't suppress exceptions

    @property
    def elapsed(self) -> float:
        """Get elapsed time in seconds."""
        if self.start_time is None:
            return 0.0
        end = self.end_time if self.end_time else time.time()
        return end - self.start_time
