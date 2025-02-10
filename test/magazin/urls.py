from django.urls import path
from . import views
from django.contrib.auth import views as auth_views


urlpatterns = [
    path('products/', views.product_list, name='product_list'),
    path('contact/', views.contact, name='contact'),
    path('add_product/', views.add_product, name='add_product'),
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('profile/', views.profile, name='profile'),
    path('change_password/', views.change_password, name='change_password'),
    path('confirma_mail/<str:cod>/', views.confirma_mail, name='confirma_mail'),
    path('view/<int:product_id>/', views.register_view, name='register_view'),
    path('promotions/', views.create_promotion, name='create_promotion'),
    path('products/<int:product_id>/', views.product_detail, name='product_detail'),
    path('activate_offer/', views.activate_offer, name='activate_offer'),
    path('offer/', views.offer_page, name='offer_page'),
]



