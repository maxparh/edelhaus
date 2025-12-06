# Generated manually
from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):

    dependencies = [
        ('auth_app', '0001_initial'),  # ← укажи последнюю миграцию
    ]

    operations = [
        migrations.CreateModel(
            name='Invoice',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('invoice_number', models.PositiveIntegerField(unique=True, verbose_name='Номер накладной')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')),
                ('order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='auth_app.orders', verbose_name='Заказ')),
            ],
            options={
                'verbose_name': 'Накладная',
                'verbose_name_plural': 'Накладные',
                'ordering': ['-invoice_number'],
            },
        ),
    ]