from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('documents/', views.documents_view, name='documents'),
    path('invoices/', views.invoice_form, name='invoice_form'),
    path('download/<str:filename>/', views.download_pdf, name='download_pdf'),
    path("orders/", views.orders_list, name="orders"),
    path("orders/add/", views.order_add, name='order_add'),
    path("orders/edit/<int:order_id>/", views.order_edit, name='order_edit'),
    path("orders/delete/<int:order_id>/", views.order_delete, name='order_delete'),
    path("orders/items/<int:order_id>/", views.order_items_view, name='order_items'),
    path("products/", views.product_list, name="products"),
    path("products/add/", views.product_add, name='product_add'),
    path("products/edit/<int:product_id>/", views.product_edit, name='product_edit'),
    path("products/delete/<int:product_id>/", views.product_delete, name='product_delete'),
    path("clients/", views.clients_list, name="clients"),
    path("clients/add/", views.client_add, name='client_add'),
    path("clients/edit/<int:client_id>/", views.client_edit, name='client_edit'),
    path("clients/delete/<int:client_id>/", views.client_delete, name='client_delete'),
    path("suppliers/add/", views.supplier_add, name='supplier_add'),
    path("suppliers/edit/<int:supplier_id>/", views.supplier_edit, name='supplier_edit'),
    path("suppliers/delete/<int:supplier_id>/", views.supplier_delete, name='supplier_delete'),
    path("suppliers/", views.suppliers_list, name="suppliers"),
    path("certs/", views.certs_list, name="certs"),
    path("giveTake/", views.giveTakeActs, name="giveTake"),
    path('', views.home_view, name='home'),
]

