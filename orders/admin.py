from django.contrib import admin
from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    can_delete = False  # Disable delete button
    readonly_fields = ('product', 'size', 'quantity', 'price', 'get_total')

    def get_queryset(self, request):
        """Only show items for paid orders."""
        qs = super().get_queryset(request)
        return qs.filter(order__payment_status='paid')

    def has_add_permission(self, request, obj=None):
        """Prevent adding new items from admin."""
        return False

    def has_change_permission(self, request, obj=None):
        """Prevent editing order items."""
        return False

    def get_total(self, obj):
        """Calculate total price for each item (readonly)."""
        return obj.quantity * obj.price
    get_total.short_description = 'Total'


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'user',
        'full_name',
        'email',
        'phone',
        'address',
        'city',
        'total_price',
        'payment_status',
        'status',
        'created_at',
    )
    list_filter = ('payment_status', 'status', 'created_at')
    search_fields = ('user__username', 'email', 'full_name', 'reference')
    inlines = [OrderItemInline]

    fields = (
        'user',
        'full_name',
        'email',
        'phone',
        'address',
        'city',
        'reference',
        'total_price',
        'payment_status',
        'status',
        'created_at',
    )

    def get_readonly_fields(self, request, obj=None):
        readonly = [
            'user',
            'full_name',
            'email',
            'phone',
            'address',
            'city',
            'reference',
            'total_price',
            'created_at',
        ]
        return readonly


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'product', 'quantity', 'price', 'get_total')
    readonly_fields = ('order', 'product', 'size', 'quantity', 'price', 'get_total')
    can_delete = False

    def get_queryset(self, request):
        """Only show order items belonging to paid orders."""
        qs = super().get_queryset(request)
        return qs.filter(order__payment_status='paid')

    def has_add_permission(self, request):
        """Disable adding items manually."""
        return False

    def has_change_permission(self, request, obj=None):
        """Disable editing existing order items."""
        return False

    def get_total(self, obj):
        """Calculate total per item."""
        return obj.quantity * obj.price
    get_total.short_description = 'Total'
