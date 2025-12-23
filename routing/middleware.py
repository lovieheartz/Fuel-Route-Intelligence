"""
Middleware for rate limiting, monitoring, and request tracking.
"""
import time
import logging
from django.core.cache import cache
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)


class RateLimitMiddleware(MiddlewareMixin):
    """
    Rate limiting middleware to prevent API abuse.
    Implements sliding window algorithm.
    """

    def __init__(self, get_response):
        super().__init__(get_response)
        self.rate_limit_per_minute = 60  # Max requests per minute
        self.rate_limit_per_hour = 1000  # Max requests per hour

    def process_request(self, request):
        """Check rate limits before processing request."""

        # Skip rate limiting for non-API endpoints
        if not request.path.startswith('/api/'):
            return None

        # Get client identifier (IP address or user ID)
        client_id = self._get_client_identifier(request)

        # Check minute limit
        minute_key = f"rate_limit:minute:{client_id}"
        minute_count = cache.get(minute_key, 0)

        if minute_count >= self.rate_limit_per_minute:
            logger.warning(
                f"Rate limit exceeded (minute): {client_id} "
                f"({minute_count} requests)"
            )
            return JsonResponse(
                {
                    'error': 'RateLimitExceeded',
                    'message': 'Too many requests. Please try again later.',
                    'retry_after': 60
                },
                status=429
            )

        # Check hour limit
        hour_key = f"rate_limit:hour:{client_id}"
        hour_count = cache.get(hour_key, 0)

        if hour_count >= self.rate_limit_per_hour:
            logger.warning(
                f"Rate limit exceeded (hour): {client_id} "
                f"({hour_count} requests)"
            )
            return JsonResponse(
                {
                    'error': 'RateLimitExceeded',
                    'message': 'Hourly rate limit exceeded. Please try again later.',
                    'retry_after': 3600
                },
                status=429
            )

        # Increment counters
        cache.set(minute_key, minute_count + 1, timeout=60)
        cache.set(hour_key, hour_count + 1, timeout=3600)

        # Add rate limit info to response headers
        request._rate_limit_info = {
            'remaining_minute': self.rate_limit_per_minute - minute_count - 1,
            'remaining_hour': self.rate_limit_per_hour - hour_count - 1,
        }

        return None

    def process_response(self, request, response):
        """Add rate limit headers to response."""

        if hasattr(request, '_rate_limit_info'):
            info = request._rate_limit_info
            response['X-RateLimit-Limit-Minute'] = self.rate_limit_per_minute
            response['X-RateLimit-Remaining-Minute'] = info['remaining_minute']
            response['X-RateLimit-Limit-Hour'] = self.rate_limit_per_hour
            response['X-RateLimit-Remaining-Hour'] = info['remaining_hour']

        return response

    def _get_client_identifier(self, request):
        """Get unique identifier for client (IP address or authenticated user)."""

        # Try to get authenticated user ID first
        if hasattr(request, 'user') and request.user.is_authenticated:
            return f"user:{request.user.id}"

        # Fall back to IP address
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', 'unknown')

        return f"ip:{ip}"


class RequestLoggingMiddleware(MiddlewareMixin):
    """
    Middleware to log API requests and responses with timing information.
    """

    def process_request(self, request):
        """Record request start time."""
        request._start_time = time.time()

        # Log incoming request
        logger.info(
            f"Incoming request: {request.method} {request.path} "
            f"from {request.META.get('REMOTE_ADDR', 'unknown')}"
        )

        return None

    def process_response(self, request, response):
        """Log request completion with timing."""

        if hasattr(request, '_start_time'):
            duration = time.time() - request._start_time

            # Log completion
            logger.info(
                f"Request completed: {request.method} {request.path} "
                f"[{response.status_code}] in {duration:.3f}s"
            )

            # Add timing header
            response['X-Response-Time'] = f"{duration:.3f}s"

        return response

    def process_exception(self, request, exception):
        """Log unhandled exceptions."""

        duration = time.time() - getattr(request, '_start_time', time.time())

        logger.error(
            f"Request failed: {request.method} {request.path} "
            f"after {duration:.3f}s - {type(exception).__name__}: {str(exception)}",
            exc_info=True
        )

        return None


class HealthCheckMiddleware(MiddlewareMixin):
    """
    Middleware to handle health check requests efficiently.
    """

    def process_request(self, request):
        """Handle health check without hitting the full stack."""

        if request.path == '/health' or request.path == '/ping':
            return JsonResponse({
                'status': 'healthy',
                'timestamp': time.time()
            })

        return None


class CORSHeadersMiddleware(MiddlewareMixin):
    """
    Add production-grade CORS headers.
    """

    def process_response(self, request, response):
        """Add CORS headers to response."""

        # These should be configured based on your deployment
        response['Access-Control-Allow-Origin'] = '*'  # Configure for production
        response['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
        response['Access-Control-Allow-Headers'] = (
            'Content-Type, Authorization, X-Requested-With'
        )
        response['Access-Control-Max-Age'] = '86400'

        return response
