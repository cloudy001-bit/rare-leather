# from django.contrib import admin

# Register your models here.

from django.contrib import admin
from .models import Category, Product, ProductImage

class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('title', 'min_size', 'max_size', 'extra_fee_threshold', 'extra_fee_amount', 'price_ngn', 'available', 'created_at')
    list_filter = ('available', 'category')
    search_fields = ('title', 'description')
    inlines = [ProductImageInline]
    prepopulated_fields = {'slug': ('title',)}

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('name',)}

