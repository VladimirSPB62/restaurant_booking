from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth import get_user_model
from rest_framework.exceptions import ValidationError


# Модель пользователя.
class User(AbstractUser):
    # Дополнительные поля (можно расширить по необходимости)
    phone_number = models.CharField(
        max_length=20,
        blank=True,
        verbose_name="Номер телефона"
    )

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"

    def __str__(self):
        return self.username

    @property
    def full_name(self):
        """Возвращает полное имя пользователя"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.username


# Данные ресторана (название, адрес, описание, телефон).
class Restaurant(models.Model):
    name = models.CharField(max_length=100, verbose_name="Название")
    address = models.TextField(verbose_name="Адрес")
    description = models.TextField(blank=True)
    phone = models.CharField(max_length=20, blank=True)

    class Meta:
        verbose_name = "Ресторан"
        verbose_name_plural = "Рестораны"

    def __str__(self):
        return self.name


# Столик (номер, количество мест).
class Table(models.Model):
    restaurant = models.ForeignKey(
        Restaurant,
        on_delete=models.CASCADE,
        verbose_name="Ресторан"
    )
    number = models.IntegerField(verbose_name="Номер столика")
    seats = models.IntegerField(verbose_name="Количество мест")

    def clean(self):
        if self.seats <= 0:
            raise ValidationError("Количество мест должно быть положительным")

    class Meta:
        verbose_name = "Стол"
        verbose_name_plural = "Столики"

    def __str__(self):
        return f"Столик {self.number} ({self.seats} мест) в {self.restaurant.name}"


# Слот времени (дата, время начала/окончания).
class TimeSlot(models.Model):
    date = models.DateField(verbose_name="Дата")
    start_time = models.TimeField(verbose_name="Время начала")
    end_time = models.TimeField(verbose_name="Время окончания")
    is_available = models.BooleanField(default=True, verbose_name="Доступен")

    def clean(self):
        if self.start_time >= self.end_time:
            raise ValidationError("Время начала должно быть раньше времени окончания")

    class Meta:
        verbose_name = "Слот времени"
        verbose_name_plural = "Слоты времени"
        ordering = ['date', 'start_time']

    def __str__(self):
        return f"{self.date} {self.start_time}-{self.end_time}"


# Бронирование (пользователь, столик, слот, статус занятости).
class Booking(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('cancelled', 'Cancelled'),
    ]
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, verbose_name="Пользователь")
    table = models.ForeignKey(Table, on_delete=models.CASCADE, verbose_name="Столик")
    time_slot = models.ForeignKey(TimeSlot, on_delete=models.CASCADE, verbose_name="Временной слот")
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active',
        verbose_name = "Статус",
    )

    class Meta:
        verbose_name = "Бронирование"
        verbose_name_plural = "Бронирования"
        unique_together = ['table', 'time_slot']

    def __str__(self):
        return f"Бронирование для {self.table} на {self.time_slot}"


# Меню
class MenuItem(models.Model):
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, verbose_name="Ресторан")
    name = models.CharField(max_length=100, verbose_name="Название блюда")
    description = models.TextField(blank=True, verbose_name="Описание")
    price = models.DecimalField(max_digits=8, decimal_places=2, verbose_name="Цена")
    category = models.CharField(max_length=50, blank=True, verbose_name="Категория")

    class Meta:
        verbose_name = "Блюдо меню"
        verbose_name_plural = "Блюда меню"

    def __str__(self):
        return f"{self.name} - {self.price} руб."
