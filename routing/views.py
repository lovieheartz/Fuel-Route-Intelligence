"""
API views for fuel routing.
"""
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
from django.core.cache import cache
from .models import FuelStation
from .serializers import (
    FuelStationSerializer,
    RouteRequestSerializer,
    RouteResponseSerializer,
)
from .services import FuelRoutingService
import logging

logger = logging.getLogger(__name__)


class FuelStationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing fuel stations.
    Provides list and detail endpoints.
    """

    queryset = FuelStation.objects.filter(is_active=True)
    serializer_class = FuelStationSerializer
    filterset_fields = ['state', 'city']
    search_fields = ['name', 'city', 'state']
    ordering_fields = ['retail_price', 'name', 'city', 'state']
    ordering = ['retail_price']  # Default ordering by price

    @extend_schema(
        summary="List all fuel stations",
        description="Get a list of all active fuel stations with optional filtering by state and city",
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
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(
        summary="Get fuel station details",
        description="Get detailed information about a specific fuel station"
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        summary="Get cheapest stations",
        description="Get the cheapest fuel stations, optionally filtered by state"
    )
    @action(detail=False, methods=['get'])
    def cheapest(self, request):
        """Get cheapest fuel stations"""
        state = request.query_params.get('state')
        limit = int(request.query_params.get('limit', 10))

        queryset = self.get_queryset()

        if state:
            queryset = queryset.filter(state=state.upper())

        queryset = queryset.order_by('retail_price')[:limit]
        serializer = self.get_serializer(queryset, many=True)

        return Response(serializer.data)


class PlanRouteView(APIView):
    """
    API endpoint for planning optimal fuel route.
    """

    @extend_schema(
        summary="Plan optimal fuel route",
        description=(
            "Calculate the optimal route between two US locations with fuel stops. "
            "The API will:\n"
            "1. Find the best driving route\n"
            "2. Identify optimal fuel stops (cost-effective)\n"
            "3. Calculate total fuel cost and consumption\n"
            "4. Return route geometry for map display\n\n"
            "Assumes:\n"
            "- Vehicle range: 500 miles\n"
            "- Fuel efficiency: 10 MPG\n"
            "- Start with full tank"
        ),
        request=RouteRequestSerializer,
        responses={
            200: RouteResponseSerializer,
            400: OpenApiExample(
                'Bad Request',
                value={'error': 'Invalid location format'},
                response_only=True,
            ),
            500: OpenApiExample(
                'Server Error',
                value={'error': 'Route calculation failed'},
                response_only=True,
            ),
        },
        examples=[
            OpenApiExample(
                'Example Request',
                value={
                    'start_location': 'Los Angeles, CA',
                    'end_location': 'New York, NY'
                },
                request_only=True,
            ),
            OpenApiExample(
                'Example with City Names',
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
        Plan a route with optimal fuel stops.

        Request body:
        {
            "start_location": "Los Angeles, CA",
            "end_location": "New York, NY"
        }

        Response includes:
        - Route geometry (for map display)
        - List of optimal fuel stops with costs
        - Total distance, fuel cost, and fuel consumption
        """
        # Validate request
        serializer = RouteRequestSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        start_location = serializer.validated_data['start_location']
        end_location = serializer.validated_data['end_location']

        try:
            # Plan route
            logger.info(f"Planning route from {start_location} to {end_location}")

            routing_service = FuelRoutingService()
            route_data = routing_service.plan_route(start_location, end_location)

            # Debug: Print route data
            print("=" * 60)
            print("ROUTE DATA:")
            print(route_data)
            print("=" * 60)

            # Serialize response
            response_serializer = RouteResponseSerializer(data=route_data)

            if response_serializer.is_valid():
                return Response(
                    response_serializer.data,
                    status=status.HTTP_200_OK
                )
            else:
                print("=" * 60)
                print("SERIALIZATION ERRORS:")
                print(response_serializer.errors)
                print("=" * 60)
                logger.error(f"Response serialization error: {response_serializer.errors}")
                return Response(
                    {
                        'error': 'Response serialization failed',
                        'details': response_serializer.errors
                    },
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        except ValueError as e:
            logger.warning(f"Validation error: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

        except Exception as e:
            logger.error(f"Route planning error: {str(e)}", exc_info=True)
            return Response(
                {'error': f'Route planning failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class HealthCheckView(APIView):
    """
    Simple health check endpoint.
    """

    @extend_schema(
        summary="Health check",
        description="Check if the API is running and database is accessible"
    )
    def get(self, request):
        """Health check endpoint"""
        try:
            # Check database
            station_count = FuelStation.objects.count()

            return Response({
                'status': 'healthy',
                'database': 'connected',
                'fuel_stations_loaded': station_count,
            })

        except Exception as e:
            return Response(
                {
                    'status': 'unhealthy',
                    'error': str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
