from rest_framework import serializers
from .models import User, Restaurant, Table, TimeSlot, Booking, MenuItem
from django.contrib.auth import get_user_model


class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.ReadOnlyField()

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'full_name')
        read_only_fields = ('date_joined', 'last_login')


class RestaurantSerializer(serializers.ModelSerializer):

    class Meta:
        model = Restaurant
        fields = '__all__'


class TableSerializer(serializers.ModelSerializer):
    restaurant_name = serializers.CharField(source='restaurant.name', read_only=True)

    class Meta:
        model = Table
        fields = '__all__'


class TimeSlotSerializer(serializers.ModelSerializer):

    class Meta:
        model = TimeSlot
        fields = '__all__'


class BookingSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    table = TableSerializer(read_only=True)
    time_slot = TimeSlotSerializer(read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        write_only=True,
        source='user'
    )
    table_id = serializers.PrimaryKeyRelatedField(
        queryset=Table.objects.all(),
        write_only=True,
        source='table'
    )
    time_slot_id = serializers.PrimaryKeyRelatedField(
        queryset=TimeSlot.objects.all(),
        write_only=True,
        source='time_slot'
    )

    class Meta:
        model = Booking
        fields = (
            'id', 'user', 'table', 'time_slot', 'created_at',
            'status', 'user_id', 'table_id', 'time_slot_id'
        )


class MenuItemSerializer(serializers.ModelSerializer):
    restaurant_name = serializers.CharField(source='restaurant.name', read_only=True)

    class Meta:
        model = MenuItem
        fields = '__all__'


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = get_user_model()
        fields = ('username', 'email', 'password')

    def create(self, validated_data):
        user = get_user_model().objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email'),
            password=validated_data['password']
        )
        return user