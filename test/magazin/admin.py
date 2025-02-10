from django.contrib import admin
from .models import Category, Product, Order, OrderItem, Review
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, View
from django.db.models import Count
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import post_migrate
from django.dispatch import receiver
from django.contrib.admin import AdminSite

admin.site.site_header = "Panou de Administrare Site"
admin.site.site_title = "Admin Site"
admin.site.index_title = "Bine ai venit in panoul de administrare"


class CustomAdminSite(AdminSite):
    site_header = "Panou Moderatori"
    site_title = "Administrare Moderatori"
    index_title = "Gestionare Utilizatori"

custom_admin_site = CustomAdminSite(name='custom_admin')


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)
    fieldsets = (
        ('Category Details', {
            'fields': ('name', 'description')
        }),
    )

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'stock', 'category', 'view_count') 
    list_filter = ('category',)
    fieldsets = (
        ('Product Details', {
            'fields': ('name', 'description', 'price', 'stock', 'category')
        }),
        ('Additional Info', {
            'fields': ('image',)
        }),
    )

    def view_count(self, obj):
        return View.objects.filter(product=obj).count()
    view_count.short_description = 'Views'  
    

    

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'order_date', 'status', 'total_price')
    search_fields = ('id', 'user__name')
    list_filter = ('status', 'order_date')
    fieldsets = (
        ('Order Details', {
            'fields': ('user', 'order_date', 'status', 'total_price')
        }),
    )

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'product', 'quantity', 'subtotal')
    search_fields = ('order__id', 'product__name')
    list_filter = ('order',)

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('product', 'user', 'rating', 'date')
    search_fields = ('product__name', 'user__name')
    list_filter = ('rating', 'date')
    fieldsets = (
        ('Review Details', {
            'fields': ('product', 'user', 'rating', 'comment')
        }),
    )
    
@admin.register(View)
class ViewAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'viewed_at')
    list_filter = ('product', 'user', 'viewed_at')


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    model = CustomUser
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'email', 'phone_number', 'address', 'date_of_birth', 'profile_picture', 'bio')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important Dates', {'fields': ('last_login', 'date_joined')}),
        ('Email Confirmation', {'fields': ('cod', 'email_confirmat')}),
        ('Moderator Permissions', {'fields': ('blocat',)}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2', 'first_name', 'last_name', 'email', 'phone_number', 'address', 'date_of_birth', 'profile_picture', 'bio', 'cod', 'email_confirmat'),
        }),
    )
    
    # Câmpuri afișate în listă
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'email_confirmat', 'blocat')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('username',)
    
    def get_fieldsets(self, request, obj=None):
        if request.user.groups.filter(name='Moderatori').exists():
            return (
                (None, {'fields': ('first_name', 'last_name', 'email', 'blocat')}),  # Doar aceste câmpuri sunt editabile
            )
        return super().get_fieldsets(request, obj)
    
custom_admin_site.register(CustomUser, CustomUserAdmin)



