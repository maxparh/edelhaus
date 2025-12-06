from django.db import models
from django.utils.translation import gettext_lazy as _


class Invoice(models.Model):
    invoice_number = models.PositiveIntegerField(
        verbose_name="Номер накладной",
        unique=True,
        editable=False
    )
    order = models.ForeignKey(
        'Orders',
        on_delete=models.CASCADE,
        verbose_name="Заказ",
        unique=True  # ← ЭТО КЛЮЧЕВОЕ ИЗМЕНЕНИЕ
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")

    class Meta:
        verbose_name = "Накладная"
        verbose_name_plural = "Накладные"
        ordering = ['-invoice_number']
        # Также можно (и лучше) указать:
        # unique_together = [('order',)]

    def __str__(self):
        return f"Накладная №{self.invoice_number} (Заказ {self.order.order_id})"

    @classmethod
    def get_next_invoice_number(cls):
        last = cls.objects.aggregate(models.Max('invoice_number'))['invoice_number__max']
        return (last or 0) + 1

class Clients(models.Model):
    client_id = models.AutoField(primary_key=True)
    client_name = models.TextField()
    client_phone = models.TextField(blank=True, null=True)
    client_email = models.TextField(blank=True, null=True)
    client_address = models.TextField(blank=True, null=True)
    loyalty_lvl = models.TextField(blank=True, null=True)
    registration_date = models.DateField(blank=True, null=True)

    class Meta:
        db_table = 'clients'


class Suppliers(models.Model):
    supplier_id = models.IntegerField(primary_key=True)
    name = models.TextField()

    class Meta:
        db_table = 'suppliers'


class Warehouses(models.Model):
    warehouse_id = models.IntegerField(primary_key=True)
    warehouse_address = models.TextField(blank=True, null=True)
    warehouse_phone = models.TextField(blank=True, null=True)
    warehouse_lead = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'warehouses'


class Products(models.Model):
    product_id = models.IntegerField(primary_key=True)
    product_name = models.TextField()
    product_price = models.FloatField()
    product_material = models.TextField(blank=True, null=True)
    supplier = models.ForeignKey('Suppliers', models.DO_NOTHING, blank=True, null=True)
    product_weight = models.FloatField(blank=True, null=True)
    product_color = models.TextField(blank=True, null=True)
    date_added = models.DateField(blank=True, null=True)

    class Meta:
        db_table = 'products'


class Orders(models.Model):
    order_id = models.IntegerField(primary_key=True)
    client = models.ForeignKey('Clients', on_delete=models.SET_NULL, blank=True, null=True)
    order_total = models.FloatField(blank=True, null=True)
    delivery_company = models.TextField(blank=True, null=True)
    order_status = models.TextField(blank=True, null=True)
    order_date = models.DateField(blank=True, null=True)

    class Meta:
        db_table = 'orders'


class OrderItem(models.Model):
    order = models.ForeignKey(Orders, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey('Products', on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        db_table = 'order_items'
        # Опционально: запрет дубликатов
        # unique_together = [('order', 'product')]


class ProductStorage(models.Model):
    id = models.AutoField(primary_key=True)
    product = models.ForeignKey('Products', on_delete=models.CASCADE)
    warehouse = models.ForeignKey('Warehouses', on_delete=models.CASCADE)
    amount = models.IntegerField(blank=True, null=True)
    presence = models.BooleanField(blank=True, null=True)

    class Meta:
        db_table = 'product_storage'
        unique_together = [('product', 'warehouse')]