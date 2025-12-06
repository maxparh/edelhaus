from django.contrib import admin
from .models import Orders, Clients, Suppliers

@admin.register(Orders)
class OrdersAdmin(admin.ModelAdmin):
    list_display = ("order_id", "client", "order_total", "order_status", "order_date")

@admin.register(Clients)
class ClientsAdmin(admin.ModelAdmin):
    list_display = ('client_id', 'client_name', 'client_phone', 'client_email', 'client_address', 'loyalty_lvl', 'registration_date')

@admin.register(Suppliers)
class SuppliersAdmin(admin.ModelAdmin):
    list_display = ('supplier_id', 'name')