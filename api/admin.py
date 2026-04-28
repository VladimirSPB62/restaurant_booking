from django.contrib import admin
from .models import User, Restaurant, Table, TimeSlot, Booking, MenuItem


# Register your models her
admin.site.register(User)
admin.site.register(Restaurant)
admin.site.register(Table)
admin.site.register(Booking)
admin.site.register(TimeSlot)
admin.site.register(MenuItem)
