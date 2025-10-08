import uuid
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from .models import Order, OrderItem
from catalog.models import Product
from cart.cart import Cart
from payments.models import Payment


@login_required
def checkout_view(request):
    """Handle checkout and redirect to payment initialization."""
    cart = Cart(request)

    if not cart or len(cart) == 0:
        messages.warning(request, "Your cart is empty.")
        return redirect('catalog:product_list')

    user = request.user
    full_name = user.full_name
    email = user.email

    if request.method == 'POST':
        phone = request.POST.get('phone')
        address = request.POST.get('address')
        city = request.POST.get('city')

        if not all([address, city]):
            messages.error(request, "Please fill in all required fields.")
            return render(request, 'orders/checkout.html', {
                'cart': cart,
                'user_full_name': full_name,
                'user_email': email,
            })

        # Create order
        order = Order.objects.create(
            user=user,
            full_name=full_name,
            email=email,
            phone=phone,
            address=address,
            city=city,
            total_price=cart.get_total_price(),
            status='pending',
            payment_status='unpaid'
        )

        for item in cart:
            OrderItem.objects.create(
                order=order,
                product=item['product'],
                size=item.get('size'),
                quantity=item['quantity'],
                price=item['price_ngn']
            )

        # Clear cart after order
        cart.clear()

        return redirect('payments:initialize_payment', order_id=order.id)

    return render(request, 'orders/checkout.html', {
        'cart': cart,
        'user_full_name': full_name,
        'delivery_fee': cart.get_delivery_fee(),
        'user_email': email,
    })


@login_required
def order_confirmation_view(request, order_id):
    """Display order confirmation."""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'orders/order_confirmation.html', {'order': order})


@login_required
def cancel_order_view(request, order_id):
    """Allow user to cancel unpaid/failed orders."""
    order = get_object_or_404(Order, id=order_id, user=request.user)

    if order.payment_status == 'paid' or order.status in ['processing', 'completed']:
        messages.error(request, "You cannot cancel an order that has been paid or processed.")
        return redirect('orders:order_confirmation', order_id=order.id)

    order.status = 'cancelled'
    order.payment_status = 'failed'
    order.save()

    messages.success(request, "Order cancelled successfully.")
    return redirect('accounts:dashboard')
