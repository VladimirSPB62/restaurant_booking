# Create your tests here.
import os
import django
from django.conf import settings

os.environ['DJANGO_SETTINGS_MODULE'] = 'project.settings'
settings.ALLOWED_HOSTS = ['localhost', '127.0.0.1', 'testserver']
django.setup()

from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from .models import Restaurant, Table, TimeSlot, Booking, MenuItem
from datetime import date, time, timedelta

User = get_user_model()


class RestaurantBookingApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

        # Создаём пользователей
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.admin = User.objects.create_superuser(
            username='adminuser',
            email='admin@example.com',
            password='adminpass123'
        )

        # Создаём ресторан
        self.restaurant = Restaurant.objects.create(
            name='Test Restaurant',
            address='Test Address',
            description='Test Description',
            phone='+79991234567'
        )

        # Создаём столик
        self.table = Table.objects.create(
            restaurant=self.restaurant,
            number=1,
            seats=4
        )

        # Создаём временной слот
        self.time_slot = TimeSlot.objects.create(
            date=date.today(),
            start_time=time(19, 0),
            end_time=time(21, 0)
        )

        # Создаём блюдо меню
        self.menu_item = MenuItem.objects.create(
            restaurant=self.restaurant,
            name='Test Dish',
            description='Tasty dish',
            price=500.00,
            category='main'
        )

    def authenticate_user(self):
        """Аутентификация обычного пользователя"""
        response = self.client.post(reverse('token_obtain_pair'), {
            'username': 'testuser',
            'password': 'testpass123'
        })
        token = response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + token)

    def authenticate_admin(self):
        """Аутентификация администратора"""
        response = self.client.post(reverse('token_obtain_pair'), {
            'username': 'adminuser',
            'password': 'adminpass123'
        })
        token = response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + token)

    def test_register_user(self):
        """Тест регистрации нового пользователя"""
        response = self.client.post(reverse('register'), {
            'username': 'newuser',
            'email': 'new@example.com',
            'password': 'newpass123',
            'password_confirm': 'newpass123'
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('access', response.data)
        self.assertEqual(User.objects.count(), 3)  # 2 созданных в setUp + 1 новый

    def test_create_restaurant_admin(self):
        """Тест создания ресторана администратором"""
        self.authenticate_admin()
        response = self.client.post('/api/restaurants/', {
            'name': 'New Restaurant',
            'address': 'New Address',
            'description': 'New Description',
            'phone': '+79997654321'
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Restaurant.objects.count(), 2)

    def test_list_restaurants_unauthenticated(self):
        """Тест просмотра списка ресторанов неавторизованным пользователем"""
        response = self.client.get('/api/restaurants/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_create_table_admin(self):
        """Тест создания столика администратором"""
        self.authenticate_admin()
        response = self.client.post('/api/tables/', {
            'restaurant': self.restaurant.id,
            'number': 2,
            'seats': 6
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Table.objects.count(), 2)

    def test_list_tables_filter_by_restaurant(self):
        """Тест фильтрации столиков по ресторану"""
        response = self.client.get(f'/api/tables/?restaurant={self.restaurant.id}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_create_timeslot_admin(self):
        """Тест создания временного слота администратором"""
        self.authenticate_admin()
        tomorrow = date.today() + timedelta(days=1)
        response = self.client.post('/api/time-slots/', {
            'date': tomorrow,
            'start_time': '18:00',
            'end_time': '20:00'
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_list_available_timeslots(self):
        """Тест просмотра доступных временных слотов"""
        response = self.client.get('/api/time-slots/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Должен вернуть только доступные слоты
        for slot in response.data:
            self.assertTrue(slot['is_available'])

    def test_create_booking_authenticated(self):
        """Тест создания бронирования авторизованным пользователем"""
        self.authenticate_user()
        response = self.client.post('/api/bookings/', {
            'table_id': self.table.id,
            'time_slot_id': self.time_slot.id,
            'status': 'active'
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Booking.objects.count(), 1)
        booking = Booking.objects.first()
        self.assertEqual(booking.user, self.user)
        self.assertEqual(booking.table, self.table)

    def test_booking_conflict(self):
        """Тест попытки создать бронирование на занятый столик и слот"""
        self.authenticate_user()
        # Сначала создаём бронирование
        Booking.objects.create(
            user=self.user,
            table=self.table,
            time_slot=self.time_slot,
            status='active'
        )
        # Пытаемся создать второе бронирование на тот же столик и слот
        response = self.client.post('/api/bookings/', {
            'table_id': self.table.id,
            'time_slot_id': self.time_slot.id
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('non_field_errors', response.data)

    def test_user_can_only_see_own_bookings(self):
        """Тест что пользователь видит только свои бронирования"""
        # Создаём бронирование для другого пользователя
        other_user = User.objects.create_user(username='other', password='pass')
        Booking.objects.create(user=other_user, table=self.table, time_slot=self.time_slot)

        self.authenticate_user()
        response = self.client.get('/api/bookings/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Пользователь не должен видеть бронирование другого пользователя
        self.assertEqual(len(response.data), 0)

    def test_admin_can_see_all_bookings(self):
        """Тест что администратор видит все бронирования"""
        # Создаём несколько бронирований для разных пользователей
        other_user = User.objects.create_user(username='other', password='pass')
        Booking.objects.create(user=self.user, table=self.table, time_slot=self.time_slot)
        Booking.objects.create(user=other_user, table=self.table, time_slot=self.time_slot)

        self.authenticate_admin()
        response = self.client.get('/api/bookings/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)  # Администратор видит все бронирования

    def test_update_booking_owner(self):
        """Тест обновления бронирования владельцем"""
        self.authenticate_user()
        booking = Booking.objects.create(
            user=self.user,
            table=self.table,
            time_slot=self.time_slot,
            status='active'
        )

        response = self.client.patch(f'/api/bookings/{booking.id}/', {
            'status': 'cancelled'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        booking.refresh_from_db()
        self.assertEqual(booking.status, 'cancelled')

    def test_update_booking_other_user_forbidden(self):
        """Тест запрета обновления чужого бронирования"""
        other_user = User.objects.create_user(username='other', password='pass')
        booking = Booking.objects.create(
            user=other_user,
            table=self.table,
            time_slot=self.time_slot
        )

        self.authenticate_user()  # Аутентифицируемся как другой пользователь
        response = self.client.patch(f'/api/bookings/{booking.id}/', {
            'status': 'cancelled'
        })
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_booking_owner(self):
        """Тест удаления бронирования владельцем"""
        self.authenticate_user()
        booking = Booking.objects.create(
            user=self.user,
            table=self.table,
            time_slot=self.time_slot
        )

        response = self.client.delete(f'/api/bookings/{booking.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        with self.assertRaises(Booking.DoesNotExist):
            booking.refresh_from_db()

    def test_create_menuitem_admin(self):
        """Тест создания блюда меню администратором"""
        self.authenticate_admin()
        response = self.client.post('/api/menu-items/', {
            'restaurant': self.restaurant.id,
            'name': 'New Dish',
            'description': 'New tasty dish',
            'price': 600.00,
            'category': 'dessert'
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(MenuItem.objects.count(), 2)

    def test_list_menuitems_filter_by_restaurant(self):
        """Тест фильтрации блюд меню по ресторану"""
        response = self.client.get(f'/api/menu-items/?restaurant={self.restaurant.id}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_search_restaurants_by_name(self):
        """Тест поиска ресторанов по названию"""
        response = self.client.get('/api/restaurants/?search=Test')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertIn('Test Restaurant', response.data[0]['name'])

    def test_ordering_restaurants_by_id(self):
        """Тест сортировки ресторанов по ID"""
        Restaurant.objects.create(name='Another Restaurant', address='Another Address')
        response = self.client.get('/api/restaurants/?ordering=id')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        names = [restaurant['name'] for restaurant in response.data]
        self.assertTrue(names[0] == 'Test Restaurant')  # Первый по ID

    def test_get_user_profile(self):
        """Тест получения профиля пользователя"""
        self.authenticate_user()
        response = self.client.get('/api/users/profile/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'testuser')
        self.assertIn('full_name', response.data)

    def test_invalid_registration_password_mismatch(self):
        """Тест регистрации с несовпадающими паролями"""
        response = self.client.post(reverse('register'), {
            'username': 'newuser',
            'email': 'new@example.com',
            'password': 'newpass123',
            'password_confirm': 'differentpass'
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password_confirm', response.data)
        self.assertIn('Пароли не совпадают.', response.data['password_confirm'][0])

    def test_create_timeslot_invalid_time(self):
        """Тест создания временного слота с некорректным временем"""
        self.authenticate_admin()
        tomorrow = date.today() + timedelta(days=1)
        response = self.client.post('/api/time-slots/', {
            'date': tomorrow,
            'start_time': '20:00',
            'end_time': '18:00'  # Конец раньше начала
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def tearDown(self):
        """Очистка после тестов"""
        User.objects.all().delete()
        Restaurant.objects.all().delete()
        Table.objects.all().delete()
        TimeSlot.objects.all().delete()
        Booking.objects.all().delete()
        MenuItem.objects.all().delete()
