"""
Production-grade API views with comprehensive error handling.
"""
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
from django.core.cache import cache
from django.core.exceptions import ValidationError
import logging

from .models import FuelStation
from .serializers import (
    FuelStationSerializer,
    RouteRequestSerializer,
    RouteResponseSerializer,
)
from .services_enhanced import EnhancedFuelRoutingService
from .exceptions import (
    RoutingException,
    LocationNotFoundError,
    NoRouteFoundError,
    NoFuelStationsFoundError,
    InsufficientRangeError,
    RouteServiceUnavailableError,
    ValidationException,
    RateLimitException,
)

logger = logging.getLogger(__name__)


class EnhancedFuelStationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Production-grade ViewSet for fuel stations with enhanced features.
    """

    queryset = FuelStation.objects.filter(is_active=True).select_related()
    serializer_class = FuelStationSerializer
    filterset_fields = ['state', 'city']
    search_fields = ['name', 'city', 'state', 'address']
    ordering_fields = ['retail_price', 'name', 'city', 'state']
    ordering = ['retail_price']

    @extend_schema(
        summary="List all fuel stations",
        description="Get paginated list of active fuel stations with filtering",
        parameters=[
            OpenApiParameter(
                name='state',
                description='Filter by state code (e.g., CA, NY)',
                required=False,
                type=str
            ),
            OpenApiParameter(
                name='city',
                description='Filter by city name',
                required=False,
                type=str
            ),
            OpenApiParameter(
                name='search',
                description='Search by name, city, state, or address',
                required=False,
                type=str
            ),
        ]
    )
    def list(self, request, *args, **kwargs):
        """List fuel stations with comprehensive filtering."""
        try:
            return super().list(request, *args, **kwargs)
        except Exception as e:
            logger.error(f"Error listing fuel stations: {str(e)}", exc_info=True)
            return Response(
                {'error': 'Failed to retrieve fuel stations', 'details': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @extend_schema(
        summary="Get fuel station details",
        description="Get detailed information about a specific fuel station"
    )
    def retrieve(self, request, *args, **kwargs):
        """Retrieve single fuel station with error handling."""
        try:
            return super().retrieve(request, *args, **kwargs)
        except Exception as e:
            logger.error(f"Error retrieving fuel station: {str(e)}", exc_info=True)
            return Response(
                {'error': 'Fuel station not found', 'details': str(e)},
                status=status.HTTP_404_NOT_FOUND
            )

    @extend_schema(
        summary="Get cheapest stations",
        description="Get the cheapest fuel stations, optionally filtered by state",
        parameters=[
            OpenApiParameter(
                name='state',
                description='Filter by state code',
                required=False,
                type=str
            ),
            OpenApiParameter(
                name='limit',
                description='Maximum number of results (default: 10)',
                required=False,
                type=int
            ),
        ]
    )
    @action(detail=False, methods=['get'])
    def cheapest(self, request):
        """Get cheapest fuel stations."""
        try:
            state = request.query_params.get('state')
            limit = min(int(request.query_params.get('limit', 10)), 100)  # Cap at 100

            queryset = self.get_queryset()

            if state:
                state = state.upper()
                queryset = queryset.filter(state=state)

            queryset = queryset.order_by('retail_price')[:limit]
            serializer = self.get_serializer(queryset, many=True)

            return Response({
                'count': len(serializer.data),
                'state_filter': state,
                'stations': serializer.data
            })

        except ValueError as e:
            return Response(
                {'error': 'Invalid limit parameter', 'details': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Error getting cheapest stations: {str(e)}", exc_info=True)
            return Response(
                {'error': 'Failed to retrieve cheapest stations', 'details': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class EnhancedPlanRouteView(APIView):
    """
    Production-grade API endpoint for route planning with comprehensive error handling.
    """

    @extend_schema(
        summary="Plan optimal fuel route",
        description=(
            "Calculate the optimal route between two US locations with fuel stops.\n\n"
            "**Features:**\n"
            "- Finds best driving route using OSRM\n"
            "- Optimizes fuel stops for minimum cost\n"
            "- Validates all inputs and coordinates\n"
            "- Includes comprehensive error handling\n"
            "- Returns route geometry for map display\n\n"
            "**Vehicle Assumptions:**\n"
            "- Range: 500 miles\n"
            "- Efficiency: 10 MPG\n"
            "- Tank capacity: 50 gallons\n"
            "- Starts with full tank\n\n"
            "**Response includes:**\n"
            "- Route geometry (polyline)\n"
            "- Optimal fuel stops with prices\n"
            "- Total distance and duration\n"
            "- Total fuel cost and consumption\n"
            "- Number of stations searched"
        ),
        request=RouteRequestSerializer,
        responses={
            200: RouteResponseSerializer,
            400: OpenApiExample(
                'Bad Request',
                value={
                    'error': 'LocationNotFoundError',
                    'message': 'Could not find location: InvalidCity, XX'
                },
                response_only=True,
            ),
            404: OpenApiExample(
                'No Route Found',
                value={
                    'error': 'NoRouteFoundError',
                    'message': 'No route found between locations'
                },
                response_only=True,
            ),
            429: OpenApiExample(
                'Rate Limited',
                value={
                    'error': 'RateLimitExceeded',
                    'message': 'Too many requests',
                    'retry_after': 60
                },
                response_only=True,
            ),
            500: OpenApiExample(
                'Server Error',
                value={
                    'error': 'RouteServiceUnavailableError',
                    'message': 'Routing service temporarily unavailable'
                },
                response_only=True,
            ),
        },
        examples=[
            OpenApiExample(
                'Short Route Example',
                value={
                    'start_location': 'Los Angeles, CA',
                    'end_location': 'San Francisco, CA'
                },
                request_only=True,
            ),
            OpenApiExample(
                'Long Route Example',
                value={
                    'start_location': 'New York, NY',
                    'end_location': 'Los Angeles, CA'
                },
                request_only=True,
            ),
            OpenApiExample(
                'Cross-Country Example',
                value={
                    'start_location': 'Seattle, WA',
                    'end_location': 'Miami, FL'
                },
                request_only=True,
            ),
        ],
    )
    def post(self, request):
        """
        Plan optimal route with fuel stops.

        Implements comprehensive error handling for all failure scenarios.
        """
        # Validate request
        serializer = RouteRequestSerializer(data=request.data)

        if not serializer.is_valid():
            logger.warning(f"Invalid request data: {serializer.errors}")
            return Response(
                {
                    'error': 'ValidationError',
                    'message': 'Invalid request data',
                    'details': serializer.errors
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        start_location = serializer.validated_data['start_location']
        end_location = serializer.validated_data['end_location']

        logger.info(
            f"Route planning request: {start_location} -> {end_location} "
            f"from {request.META.get('REMOTE_ADDR', 'unknown')}"
        )

        try:
            # Create service and plan route
            routing_service = EnhancedFuelRoutingService()
            route_data = routing_service.plan_route(
                start_location,
                end_location,
                use_cache=True
            )

            # Validate response data
            response_serializer = RouteResponseSerializer(data=route_data)

            if not response_serializer.is_valid():
                logger.error(
                    f"Response serialization failed: {response_serializer.errors}"
                )
                return Response(
                    {
                        'error': 'InternalError',
                        'message': 'Failed to serialize response',
                        'details': response_serializer.errors
                    },
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            # Success!
            logger.info(
                f"Route planned successfully: {route_data['summary']['total_distance_miles']:.1f} miles, "
                f"{route_data['summary']['number_of_stops']} stops, "
                f"${route_data['summary']['total_fuel_cost']:.2f}"
            )

            return Response(
                response_serializer.data,
                status=status.HTTP_200_OK
            )

        except LocationNotFoundError as e:
            logger.warning(f"Location not found: {str(e)}")
            return Response(
                e.to_dict(),
                status=status.HTTP_404_NOT_FOUND
            )

        except NoRouteFoundError as e:
            logger.warning(f"No route found: {str(e)}")
            return Response(
                e.to_dict(),
                status=status.HTTP_404_NOT_FOUND
            )

        except NoFuelStationsFoundError as e:
            logger.warning(f"No fuel stations found: {str(e)}")
            return Response(
                e.to_dict(),
                status=status.HTTP_404_NOT_FOUND
            )

        except InsufficientRangeError as e:
            logger.warning(f"Insufficient range: {str(e)}")
            return Response(
                e.to_dict(),
                status=status.HTTP_400_BAD_REQUEST
            )

        except RouteServiceUnavailableError as e:
            logger.error(f"Routing service unavailable: {str(e)}")
            return Response(
                e.to_dict(),
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )

        except RateLimitException as e:
            logger.warning(f"Rate limit exceeded: {str(e)}")
            response_data = e.to_dict()
            response = Response(
                response_data,
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )
            if e.retry_after:
                response['Retry-After'] = str(e.retry_after)
            return response

        except ValidationException as e:
            logger.warning(f"Validation error: {str(e)}")
            return Response(
                e.to_dict(),
                status=status.HTTP_400_BAD_REQUEST
            )

        except ValidationError as e:
            logger.warning(f"Django validation error: {str(e)}")
            return Response(
                {
                    'error': 'ValidationError',
                    'message': str(e),
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        except RoutingException as e:
            logger.error(f"Routing exception: {str(e)}", exc_info=True)
            return Response(
                e.to_dict(),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        except Exception as e:
            logger.error(
                f"Unexpected error in route planning: {str(e)}",
                exc_info=True
            )
            return Response(
                {
                    'error': 'InternalServerError',
                    'message': 'An unexpected error occurred',
                    'details': str(e) if request.user.is_staff else None
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class EnhancedHealthCheckView(APIView):
    """
    Comprehensive health check endpoint with detailed diagnostics.
    """

    @extend_schema(
        summary="Health check with diagnostics",
        description=(
            "Check API health and service availability.\n\n"
            "Returns:\n"
            "- Overall status\n"
            "- Database connectivity\n"
            "- Cache availability\n"
            "- Fuel station count\n"
            "- Service versions"
        )
    )
    def get(self, request):
        """Comprehensive health check."""
        health_status = {
            'status': 'healthy',
            'timestamp': cache.get('health_check_time', 0),
            'services': {}
        }

        # Check database
        try:
            station_count = FuelStation.objects.count()
            active_count = FuelStation.objects.filter(is_active=True).count()
            health_status['services']['database'] = {
                'status': 'connected',
                'total_stations': station_count,
                'active_stations': active_count,
            }
        except Exception as e:
            logger.error(f"Database health check failed: {str(e)}")
            health_status['status'] = 'degraded'
            health_status['services']['database'] = {
                'status': 'error',
                'error': str(e)
            }

        # Check cache
        try:
            test_key = 'health_check_test'
            test_value = 'ok'
            cache.set(test_key, test_value, timeout=10)
            retrieved = cache.get(test_key)

            if retrieved == test_value:
                health_status['services']['cache'] = {'status': 'available'}
            else:
                health_status['services']['cache'] = {
                    'status': 'degraded',
                    'message': 'Cache not returning correct values'
                }
                health_status['status'] = 'degraded'

        except Exception as e:
            logger.error(f"Cache health check failed: {str(e)}")
            health_status['status'] = 'degraded'
            health_status['services']['cache'] = {
                'status': 'error',
                'error': str(e)
            }

        # Add version info
        health_status['version'] = '2.0.0'
        health_status['api'] = 'Spotter AI Fuel Routing'

        # Determine HTTP status code
        if health_status['status'] == 'healthy':
            response_status = status.HTTP_200_OK
        elif health_status['status'] == 'degraded':
            response_status = status.HTTP_200_OK  # Still operational
        else:
            response_status = status.HTTP_503_SERVICE_UNAVAILABLE

        return Response(health_status, status=response_status)


class MetricsView(APIView):
    """
    API metrics and statistics endpoint.
    """

    @extend_schema(
        summary="Get API metrics",
        description="Get usage statistics and performance metrics"
    )
    def get(self, request):
        """Return API metrics."""
        try:
            # Calculate metrics from cache
            metrics = {
                'requests': {
                    'total': cache.get('metrics:requests:total', 0),
                    'successful': cache.get('metrics:requests:successful', 0),
                    'failed': cache.get('metrics:requests:failed', 0),
                },
                'routes': {
                    'planned': cache.get('metrics:routes:planned', 0),
                    'cached': cache.get('metrics:routes:cached', 0),
                },
                'cache': {
                    'hit_rate': self._calculate_cache_hit_rate(),
                },
                'fuel_stations': {
                    'total': FuelStation.objects.count(),
                    'active': FuelStation.objects.filter(is_active=True).count(),
                }
            }

            return Response(metrics)

        except Exception as e:
            logger.error(f"Metrics retrieval failed: {str(e)}", exc_info=True)
            return Response(
                {'error': 'Failed to retrieve metrics', 'details': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def _calculate_cache_hit_rate(self) -> float:
        """Calculate cache hit rate percentage."""
        hits = cache.get('metrics:cache:hits', 0)
        misses = cache.get('metrics:cache:misses', 0)
        total = hits + misses

        if total == 0:
            return 0.0

        return round((hits / total) * 100, 2)
