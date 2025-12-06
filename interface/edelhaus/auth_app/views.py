import os
from datetime import date

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Max
from django.http import (
    FileResponse,
    Http404,
    HttpResponse,
    HttpResponseRedirect,
    JsonResponse
)
from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import render_to_string
from django.urls import reverse

from weasyprint import HTML

from .models import Orders, Clients, Suppliers, Products, OrderItem, Invoice

# Используем допустимые статусы заказа
VALID_STATUSES = {"Принят", "В обработке", "Выполняется", "Выполнен"}


def login_view(request):
    # Авторизация пользователя
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user:
            login(request, user)
            return HttpResponseRedirect(reverse('home'))
        else:
            return render(request, 'auth_app/login.html', {
                'error': "Неверный логин или пароль"
            })

    return render(request, 'auth_app/login.html')


@login_required
def home_view(request):
    # Главная панель после входа
    return render(request, 'auth_app/home.html')


def logout_view(request):
    # Выход из системы
    logout(request)
    return redirect('login')


def documents_view(request):
    # Страница со списком документов
    return render(request, 'docs/documents.html')


def orders_list(request):
    # Вывод всех заказов с пагинацией
    orders = Orders.objects.select_related('client').order_by('order_id')
    paginator = Paginator(orders, 5)

    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    return render(request, 'orders/orders_list.html', {'page_obj': page_obj})


def order_add(request):
    # Добавление нового заказа
    clients = Clients.objects.all().order_by('client_name')
    products = Products.objects.all().order_by('product_name')

    if request.method == 'POST':
        client_id = request.POST.get('client_id') or None
        delivery_company = request.POST.get('delivery_company', '').strip() or None
        order_status = request.POST.get('order_status', '').strip()
        order_date = request.POST.get('order_date')
        order_total = request.POST.get('order_total')

        errors = []

        # Проверка даты
        if not order_date:
            errors.append('Дата заказа обязательна.')
        else:
            try:
                order_date_parsed = date.fromisoformat(order_date)
                if order_date_parsed > date.today():
                    errors.append('Дата заказа не может быть в будущем.')
            except ValueError:
                errors.append('Неверный формат даты.')

        # Проверка статуса
        if not order_status:
            errors.append('Статус заказа обязателен.')
        elif order_status not in VALID_STATUSES:
            errors.append('Недопустимый статус заказа.')

        # Проверка товаров
        product_ids = request.POST.getlist('product_id[]')
        quantities = request.POST.getlist('quantity[]')

        products_dict = {str(p.product_id): p for p in Products.objects.all()}
        valid_items = []
        calculated_total = 0

        for pid, qty in zip(product_ids, quantities):
            if not pid or not qty:
                continue

            try:
                qty_int = int(qty)
                if qty_int <= 0:
                    continue

                product = products_dict.get(pid)
                if not product:
                    continue

                subtotal = (product.product_price or 0) * qty_int
                calculated_total += subtotal
                valid_items.append((product, qty_int))

            except (ValueError, TypeError):
                continue

        if not valid_items:
            errors.append('Не удалось добавить ни одного корректного товара.')

        if errors:
            for err in errors:
                messages.error(request, err)

            return render(request, 'orders/order_add.html', {
                'clients': clients,
                'products': products,
                'client_id': client_id,
                'delivery_company': delivery_company,
                'order_status': order_status,
                'order_date': order_date,
                'order_total': order_total,
            })

        # Генерация нового ID заказа
        last_order = Orders.objects.aggregate(Max('order_id'))['order_id__max']
        new_order_id = (last_order or 0) + 1

        # Разбор суммы
        total_value = None
        if order_total:
            try:
                total_value = float(order_total.replace(',', '.'))
                if total_value < 0:
                    total_value = None
            except ValueError:
                pass

        if total_value is None:
            total_value = calculated_total

        # Создание заказа
        order = Orders.objects.create(
            order_id=new_order_id,
            client_id=client_id,
            delivery_company=delivery_company,
            order_status=order_status,
            order_date=order_date_parsed,
            order_total=total_value
        )

        # Создание позиций заказа
        OrderItem.objects.bulk_create([
            OrderItem(order=order, product=prod, quantity=qty)
            for prod, qty in valid_items
        ])

        messages.success(request, f'Заказ №{new_order_id} успешно добавлен.')
        return redirect('orders')

    return render(request, 'orders/order_add.html', {
        'clients': clients,
        'products': products,
    })


def order_edit(request, order_id):
    # Редактирование существующего заказа
    order = get_object_or_404(Orders, order_id=order_id)
    clients = Clients.objects.all().order_by('client_name')

    if request.method == 'POST':
        client_id = request.POST.get('client_id') or None
        delivery_company = request.POST.get('delivery_company', '').strip() or None
        order_status = request.POST.get('order_status', '').strip() or None
        order_date = request.POST.get('order_date')
        order_total = request.POST.get('order_total')

        if not order_date:
            messages.error(request, 'Дата заказа обязательна.')
        else:
            try:
                order_date_parsed = date.fromisoformat(order_date)
                if order_date_parsed > date.today():
                    messages.error(request, 'Дата заказа не может быть в будущем.')
                    raise ValueError
            except ValueError:
                messages.error(request, 'Неверный формат даты.')
                order_date_parsed = None

            if order_date_parsed:
                total = None
                if order_total:
                    try:
                        total = float(order_total.replace(',', '.'))
                        if total < 0:
                            messages.error(request, 'Сумма не может быть отрицательной.')
                            total = None
                    except ValueError:
                        messages.error(request, 'Некорректная сумма заказа.')
                        total = None

                order.client_id = client_id
                order.delivery_company = delivery_company
                order.order_status = order_status
                order.order_date = order_date_parsed
                order.order_total = total
                order.save()

                messages.success(request, f'Заказ №{order_id} успешно обновлён.')
                return redirect('orders')

    return render(request, 'orders/order_edit.html', {
        'order': order,
        'clients': clients,
    })


def order_delete(request, order_id):
    # Удаление заказа
    order = get_object_or_404(Orders, order_id=order_id)

    if request.method == 'POST':
        order_id_val = order.order_id
        order.delete()
        messages.success(request, f'Заказ №{order_id_val} успешно удалён.')

    return redirect('orders')


def order_items_view(request, order_id):
    # Детали заказа всплывающим окном
    order = get_object_or_404(Orders, order_id=order_id)
    items = order.items.select_related('product').all()

    items_data = []
    total = 0

    for item in items:
        price = item.product.product_price or 0
        subtotal = price * item.quantity
        total += subtotal

        items_data.append({
            'product_name': item.product.product_name,
            'quantity': item.quantity,
            'price': price,
            'subtotal': subtotal
        })

    html_content = render_to_string('orders/order_items_popup_content.html', {
        'order_id': order_id,
        'items': items_data,
        'total': total
    })

    return JsonResponse({'html': html_content})


def clients_list(request):
    # Список клиентов с пагинацией
    clients_list = Clients.objects.all().order_by('client_id')
    paginator = Paginator(clients_list, 5)

    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    return render(request, 'clients/clients.html', {'page_obj': page_obj})


def client_add(request):
    # Добавление нового клиента
    if request.method == 'POST':
        client_name = request.POST.get('client_name')
        client_phone = request.POST.get('client_phone', '')
        client_email = request.POST.get('client_email', '')
        client_address = request.POST.get('client_address', '')
        loyalty_lvl = request.POST.get('loyalty_lvl', '')
        registration_date = request.POST.get('registration_date', None)

        if not client_name:
            messages.error(request, 'Имя клиента обязательно!')
            return render(request, 'clients/client_add.html', {
                'client_name': client_name,
                'client_phone': client_phone,
                'client_email': client_email,
                'client_address': client_address,
                'loyalty_lvl': loyalty_lvl,
                'registration_date': registration_date,
            })

        if not loyalty_lvl:
            messages.error(request, 'Уровень лояльности обязателен!')
            return render(request, 'clients/client_add.html', {
                'client_name': client_name,
                'client_phone': client_phone,
                'client_email': client_email,
                'client_address': client_address,
                'loyalty_lvl': loyalty_lvl,
                'registration_date': registration_date,
            })

        if registration_date:
            try:
                reg_date = date.fromisoformat(registration_date)
                if reg_date > date.today():
                    messages.error(request, 'Дата регистрации не может быть в будущем.')
                    return render(request, 'clients/client_add.html', {
                        'client_name': client_name,
                        'client_phone': client_phone,
                        'client_email': client_email,
                        'client_address': client_address,
                        'loyalty_lvl': loyalty_lvl,
                        'registration_date': registration_date,
                    })
            except ValueError:
                messages.error(request, 'Неверный формат даты.')
                return render(request, 'clients/client_add.html', {
                    'client_name': client_name,
                    'client_phone': client_phone,
                    'client_email': client_email,
                    'client_address': client_address,
                    'loyalty_lvl': loyalty_lvl,
                    'registration_date': registration_date,
                })

        Clients.objects.create(
            client_name=client_name,
            client_phone=client_phone,
            client_email=client_email,
            client_address=client_address,
            loyalty_lvl=loyalty_lvl,
            registration_date=registration_date
        )

        return redirect('clients')

    return render(request, 'clients/client_add.html')


def client_edit(request, client_id):
    # Редактирование клиента
    client = get_object_or_404(Clients, client_id=client_id)

    if request.method == 'POST':
        name = request.POST.get('client_name')
        phone = request.POST.get('client_phone')
        email = request.POST.get('client_email')
        address = request.POST.get('client_address')
        loyalty_lvl = request.POST.get('loyalty_lvl')
        registration_date = request.POST.get('registration_date')

        if not name or not registration_date:
            messages.error(request, 'Имя клиента и дата регистрации обязательны.')
        else:
            # Здесь поля оставлены как у тебя, чтобы код продолжал работать
            client.name = name
            client.phone = phone
            client.email = email
            client.address = address
            client.loyalty_lvl = loyalty_lvl
            client.registration_date = registration_date

            client.save()

            messages.success(request, f'Информация о клиенте №{client_id} успешно обновлена.')
            return redirect('clients')

    return render(request, 'clients/client_edit.html', {
        'client': client,
        'client_id': client.client_id,
    })


def client_delete(request, client_id):
    # Удаление клиента
    client = get_object_or_404(Clients, client_id=client_id)

    if request.method == 'POST':
        client_name = client.client_name
        client.delete()
        messages.success(request, f'Клиент "{client_name}" успешно удалён.')

    return redirect('clients')


def certs_list(request):
    # Страница с сертификатами
    return render(request, 'docs/certs.html')


def download_pdf(request, filename):
    # Загрузка PDF файла из MEDIA_ROOT
    file_path = os.path.join(settings.MEDIA_ROOT, filename)

    if os.path.exists(file_path):
        return FileResponse(open(file_path, 'rb'), as_attachment=True, filename=filename)

    raise Http404("Файл не найден")


def suppliers_list(request):
    # Список поставщиков
    suppliers_list = Suppliers.objects.all().order_by('supplier_id')
    paginator = Paginator(suppliers_list, 5)

    page_obj = paginator.get_page(request.GET.get('page', 1))

    return render(request, "suppliers/suppliers.html", {"page_obj": page_obj})


def product_list(request):
    # Список товаров
    product_list = Products.objects.all().order_by('product_id')
    paginator = Paginator(product_list, 5)

    page_obj = paginator.get_page(request.GET.get('page', 1))

    return render(request, "products/products_list.html", {"page_obj": page_obj})


def product_add(request):
    # Добавление нового товара
    suppliers = Suppliers.objects.all().order_by('name')

    if request.method == 'POST':
        product_name = request.POST.get('product_name', '').strip()
        product_price = request.POST.get('product_price', '').strip()
        product_material = request.POST.get('product_material', '').strip()
        supplier_id = request.POST.get('supplier_id')
        product_weight = request.POST.get('product_weight', '').strip()
        product_color = request.POST.get('product_color', '').strip()
        date_added = request.POST.get('date_added', '').strip()

        errors = []

        if not product_name:
            errors.append('Название товара обязательно.')

        if not product_price:
            errors.append('Цена товара обязательна.')
        else:
            try:
                product_price = float(product_price)
                if product_price < 0:
                    errors.append('Цена не может быть отрицательной.')
            except ValueError:
                errors.append('Цена должна быть числом.')

        if date_added:
            try:
                parsed_date = date.fromisoformat(date_added)
                if parsed_date > date.today():
                    errors.append('Дата добавления не может быть в будущем.')
            except ValueError:
                errors.append('Неверный формат даты.')
        else:
            parsed_date = None

        if product_weight:
            try:
                product_weight = float(product_weight)
                if product_weight <= 0:
                    errors.append('Вес должен быть положительным числом.')
            except ValueError:
                errors.append('Вес должен быть числом.')
        else:
            product_weight = None

        supplier = None
        if supplier_id:
            try:
                supplier = Suppliers.objects.get(supplier_id=supplier_id)
            except Suppliers.DoesNotExist:
                errors.append('Выбранный поставщик не найден.')

        if errors:
            for err in errors:
                messages.error(request, err)

            return render(request, 'products/product_add.html', {
                'product_name': product_name,
                'product_price': request.POST.get('product_price'),
                'product_material': product_material,
                'supplier_id': supplier_id,
                'product_weight': request.POST.get('product_weight'),
                'product_color': product_color,
                'date_added': date_added,
                'suppliers': suppliers,
            })

        Products.objects.create(
            product_name=product_name,
            product_price=product_price,
            product_material=product_material or None,
            supplier=supplier,
            product_weight=product_weight,
            product_color=product_color or None,
            date_added=parsed_date
        )

        messages.success(request, f'Товар "{product_name}" успешно добавлен.')
        return redirect('products')

    return render(request, 'products/product_add.html', {'suppliers': suppliers})


def product_edit(request, product_id):
    # Редактирование товара
    product = get_object_or_404(Products, product_id=product_id)
    suppliers = Suppliers.objects.all().order_by('name')

    if request.method == 'POST':
        product_name = request.POST.get('product_name', '').strip()
        product_price = request.POST.get('product_price', '').strip()
        product_material = request.POST.get('product_material', '').strip()
        supplier_id = request.POST.get('supplier_id')
        product_weight = request.POST.get('product_weight', '').strip()
        product_color = request.POST.get('product_color', '').strip()
        date_added = request.POST.get('date_added', '').strip()

        errors = []

        if not product_name:
            errors.append('Название товара обязательно.')

        if not product_price:
            errors.append('Цена товара обязательна.')
        else:
            try:
                product_price = float(product_price)
                if product_price < 0:
                    errors.append('Цена не может быть отрицательной.')
            except ValueError:
                errors.append('Цена должна быть числом.')

        if date_added:
            try:
                parsed_date = date.fromisoformat(date_added)
                if parsed_date > date.today():
                    errors.append('Дата добавления не может быть в будущем.')
            except ValueError:
                errors.append('Неверный формат даты.')
        else:
            parsed_date = None

        if product_weight:
            try:
                product_weight = float(product_weight)
                if product_weight <= 0:
                    errors.append('Вес должен быть положительным числом.')
            except ValueError:
                errors.append('Вес должен быть числом.')
        else:
            product_weight = None

        supplier = None
        if supplier_id:
            try:
                supplier = Suppliers.objects.get(supplier_id=supplier_id)
            except Suppliers.DoesNotExist:
                errors.append('Выбранный поставщик не найден.')

        if errors:
            for err in errors:
                messages.error(request, err)

            return render(request, 'products/product_edit.html', {
                'product': product,
                'product_name': product_name,
                'product_price': request.POST.get('product_price'),
                'product_material': product_material,
                'supplier_id': supplier_id,
                'product_weight': request.POST.get('product_weight'),
                'product_color': product_color,
                'date_added': date_added,
                'suppliers': suppliers,
            })

        product.product_name = product_name
        product.product_price = product_price
        product.product_material = product_material or None
        product.supplier = supplier
        product.product_weight = product_weight
        product.product_color = product_color or None
        product.date_added = parsed_date
        product.save()

        messages.success(request, f'Товар "{product_name}" успешно обновлён.')
        return redirect('products')

    return render(request, 'products/product_edit.html', {
        'product': product,
        'suppliers': suppliers,
        'supplier_id': product.supplier.supplier_id if product.supplier else '',
        'date_added': product.date_added.isoformat() if product.date_added else '',
    })


def product_delete(request, product_id):
    # Удаление товара
    product = get_object_or_404(Products, product_id=product_id)

    if request.method == 'POST':
        product_name = product.product_name
        product.delete()
        messages.success(request, f'Товар "{product_name}" успешно удалён.')

    return redirect('products')


def supplier_add(request):
    # Добавление нового поставщика
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()

        if not name:
            messages.error(request, 'Наименование поставщика обязательно!')
            return render(request, 'suppliers/supplier_add.html', {'name': name})

        if Suppliers.objects.filter(name=name).exists():
            messages.error(request, 'Поставщик с таким наименованием уже существует.')
            return render(request, 'suppliers/supplier_add.html', {'name': name})

        last_supplier = Suppliers.objects.order_by('-supplier_id').first()
        next_id = (last_supplier.supplier_id + 1) if last_supplier else 1

        Suppliers.objects.create(
            supplier_id=next_id,
            name=name
        )

        messages.success(request, f'Поставщик "{name}" успешно добавлен.')
        return redirect('suppliers')

    return render(request, 'suppliers/supplier_add.html')


def supplier_edit(request, supplier_id):
    # Редактирование поставщика
    supplier = get_object_or_404(Suppliers, supplier_id=supplier_id)

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()

        if not name:
            messages.error(request, 'Наименование поставщика обязательно!')
        else:
            supplier.name = name
            supplier.save()
            messages.success(request, f'Поставщик №{supplier_id} успешно обновлён.')
            return redirect('suppliers')

    return render(request, 'suppliers/supplier_edit.html', {'supplier': supplier})


def supplier_delete(request, supplier_id):
    # Удаление поставщика
    supplier = get_object_or_404(Suppliers, supplier_id=supplier_id)

    if request.method == 'POST':
        name = supplier.name
        supplier.delete()
        messages.success(request, f'Поставщик "{name}" успешно удалён.')

    return redirect('suppliers')

def invoice_form(request):
    if request.method == "POST":
        order_id_str = request.POST.get("order_id", "").strip()
        if not order_id_str.isdigit():
            return render(request, "docs/invoices.html", {
                "error": "Номер заказа должен быть целым числом"
            })

        order_id = int(order_id_str)
        try:
            order = Orders.objects.select_related('client').get(order_id=order_id)
        except Orders.DoesNotExist:
            return render(request, "docs/invoices.html", {
                "error": f"Заказ №{order_id} не найден"
            })

        # === Гарантируем 1 накладную на заказ + правильный номер ===
        with transaction.atomic():
            # Пробуем получить существующую
            invoice = Invoice.objects.filter(order=order).first()
            if invoice:
                # Накладная уже есть — используем её номер
                invoice_number = invoice.invoice_number
            else:
                # Создаём новую с правильным номером
                last_num = Invoice.objects.aggregate(Max('invoice_number'))['invoice_number__max']
                invoice_number = (last_num or 0) + 1
                invoice = Invoice.objects.create(
                    order=order,
                    invoice_number=invoice_number
                )

        # === Дальнейшая логика без изменений ===
        pdf_filename = f"nakladnaya_{invoice_number}.pdf"
        os.makedirs(os.path.join(settings.MEDIA_ROOT, 'invoices'), exist_ok=True)
        pdf_path = os.path.join(settings.MEDIA_ROOT, 'invoices', pdf_filename)

        if os.path.exists(pdf_path):
            with open(pdf_path, 'rb') as f:
                response = HttpResponse(f.read(), content_type='application/pdf')
                response['Content-Disposition'] = f'attachment; filename="{pdf_filename}"'
                return response

        # Собираем данные
        items_data = []
        for item in OrderItem.objects.filter(order=order).select_related('product'):
            total = item.product.product_price * item.quantity
            items_data.append({
                'product_name': item.product.product_name,
                'color': item.product.product_color or "—",
                'price': item.product.product_price,
                'quantity': item.quantity,
                'total': total,
            })

        order_total = float(order.order_total or 0)
        nds_amount = order_total * 0.18 / 1.18 if order_total > 0 else 0

        html = render_to_string("docs/invoice_template.html", {
            "invoice": invoice,
            "order": order,
            "items": items_data,
            "order_total": order_total,
            "nds_amount": nds_amount,
        })

        pdf = HTML(string=html).write_pdf()

        with open(pdf_path, 'wb') as f:
            f.write(pdf)

        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{pdf_filename}"'
        return response

    return render(request, "docs/invoices.html")

def giveTakeActs(request):
    return render(request, "docs/take-give.html")