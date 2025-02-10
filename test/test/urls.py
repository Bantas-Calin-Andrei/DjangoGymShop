from django.contrib import admin
from django.urls import path, include
from magazin import views
from django.conf.urls import handler403
from magazin.views import custom_403_view

urlpatterns = [
    path('', views.home, name='home'),
    path('admin/', admin.site.urls),
    path('magazin/', include('magazin.urls')),
]


handler403 = 'magazin.views.custom_403_view'