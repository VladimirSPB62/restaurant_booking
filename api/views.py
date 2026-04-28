from rest_framework.exceptions import PermissionDenied, ValidationError
from .models import Restaurant, Table, TimeSlot, Booking, MenuItem, User
from rest_framework import viewsets, permissions, filters, generics, status
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import (
    UserSerializer, RestaurantSerializer, TableSerializer,
    TimeSlotSerializer, BookingSerializer, MenuItemSerializer,
    RegisterSerializer
)


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAdminUser()]
        return [permissions.AllowAny()]

class RestaurantViewSet(viewsets.ModelViewSet):
    queryset = Restaurant.objects.all()
    serializer_class = RestaurantSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'address']
    ordering = ['id']

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAdminUser()]
        return [permissions.AllowAny()]

class TableViewSet(viewsets.ModelViewSet):
    queryset = Table.objects.select_related('restaurant').all()
    serializer_class = TableSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['number']
    filterset_fields = ['restaurant', 'seats']
    ordering = ['id']

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAdminUser()]
        return [permissions.AllowAny()]

class TimeSlotViewSet(viewsets.ModelViewSet):
    queryset = TimeSlot.objects.filter(is_available=True)
    serializer_class = TimeSlotSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['date', 'is_available']
    ordering = ['date', 'start_time']

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAdminUser()]
        return [permissions.AllowAny()]

class BookingViewSet(viewsets.ModelViewSet):
    queryset = Booking.objects.select_related('user', 'table', 'time_slot').all()
    serializer_class = BookingSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['status', 'table', 'time_slot']

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return self.queryset
        return self.queryset.filter(user=user)

    def perform_update(self, serializer):
        booking = self.get_object()
        if booking.user != self.request.user and not self.request.user.is_staff:
            raise PermissionDenied("Вы не можете редактировать это бронирование")
        serializer.save()

    def perform_create(self, serializer):
        time_slot = serializer.validated_data['time_slot']
        if not time_slot.is_available:
            raise ValidationError("Этот временной слот недоступен")
        serializer.save(user=self.request.user)

    def get_permissions(self):
        if self.action in ['list', 'create', 'retrieve', 'destroy']:
            return [permissions.IsAuthenticated()]
        return [permissions.IsAdminUser()]

class MenuItemViewSet(viewsets.ModelViewSet):
    queryset = MenuItem.objects.select_related('restaurant').all()
    serializer_class = MenuItemSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    search_fields = ['name', 'category']
    filterset_fields = ['restaurant', 'category']
    ordering = ['price']

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAdminUser()]
        return [permissions.AllowAny()]

class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        created_user = serializer.save()
        refresh = RefreshToken.for_user(created_user)
        return Response({
            "user": serializer.data,
            "refresh": str(refresh),
            "access": str(refresh.access_token),
        }, status=status.HTTP_201_CREATED)