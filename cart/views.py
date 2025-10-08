from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from catalog.models import Product
from .cart import Cart

@require_POST
def cart_add(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    quantity = int(request.POST.get('quantity', 1))
    size = int(request.POST.get('size', product.min_size))
    price = product.price_ngn

    if size > product.extra_fee_threshold:
        price += product.extra_fee_amount

    cart.add(product=product, quantity=quantity, price=price, size=size)
    return redirect('cart:cart_detail')

@require_POST
def cart_remove(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    cart.remove(product)
    return redirect('cart:cart_detail')

def cart_detail(request):
    cart = Cart(request)
    return render(request, 'cart/cart_detail.html', {
        'cart': cart,
        'delivery_fee': cart.get_delivery_fee(),
        'total_price': cart.get_total_price()
    })
