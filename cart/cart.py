from decimal import Decimal
from catalog.models import Product
from settings.models import SiteSettings  # Admin-editable delivery fee model

class Cart:
    def __init__(self, request):
        self.session = request.session
        cart = self.session.get('cart')
        if not cart:
            cart = self.session['cart'] = {}
        self.cart = cart

        # Load delivery fee from session or admin settings
        settings = SiteSettings.objects.first()
        # Use admin value if exists, else default 3500
        self.delivery_fee = Decimal(self.session.get('delivery_fee', settings.delivery_fee if settings else 3500))
        # Save back as string to session (JSON-serializable)
        self.session['delivery_fee'] = str(self.delivery_fee)

    def _generate_key(self, product, size):
        """Create unique key per product + size combination."""
        return f"{product.id}_{size}" if size else str(product.id)

    def add(self, product, quantity=1, size=None, override_quantity=False, price=None):
        key = self._generate_key(product, size)

        # Convert price to Decimal; fallback to product price
        final_price = Decimal(price) if price is not None else Decimal(product.price_ngn)

        # Add extra fee for large sizes if applicable
        if size and hasattr(product, "large_size_threshold") and hasattr(product, "large_size_extra_fee"):
            try:
                if int(size) > int(product.large_size_threshold):
                    final_price += Decimal(product.large_size_extra_fee)
            except (ValueError, TypeError):
                pass

        if key not in self.cart:
            self.cart[key] = {
                'quantity': 0,
                'price_ngn': str(final_price),  # store as string to avoid JSON serialization issues
                'size': size,
                'product_id': product.id
            }

        if override_quantity:
            self.cart[key]['quantity'] = quantity
        else:
            self.cart[key]['quantity'] += quantity

        # Always ensure price and size are up-to-date
        self.cart[key]['price_ngn'] = str(final_price)
        self.cart[key]['size'] = size

        self.save()

    def save(self):
        self.session.modified = True

    def remove(self, product, size=None):
        key = self._generate_key(product, size)
        if size:
            if key in self.cart:
                del self.cart[key]
        else:
            keys_to_remove = [k for k in self.cart.keys() if k.startswith(f"{product.id}_") or k == str(product.id)]
            for k in keys_to_remove:
                del self.cart[k]
        self.save()

    def __iter__(self):
        product_ids = [item['product_id'] for item in self.cart.values()]
        products = Product.objects.filter(id__in=product_ids)
        product_map = {str(p.id): p for p in products}

        for key, item in self.cart.items():
            product = product_map.get(str(item['product_id']))
            if product:
                # Make a copy so we don't modify the session
                item_copy = item.copy()
                item_copy['product'] = product
                item_copy['total_price'] = Decimal(item_copy['price_ngn']) * item_copy['quantity']
                yield item_copy

    def __len__(self):
        return sum(item['quantity'] for item in self.cart.values())

    def get_total_price(self):
        """Total price including delivery fee."""
        total = sum(Decimal(item['price_ngn']) * item['quantity'] for item in self.cart.values())
        return total + self.delivery_fee

    def get_delivery_fee(self):
        """Return current delivery fee."""
        return self.delivery_fee

    def clear(self):
        self.session['cart'] = {}
        # Keep delivery fee in session
        self.session['delivery_fee'] = str(self.delivery_fee)
        self.save()
