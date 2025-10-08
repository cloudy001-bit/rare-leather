# from django.db import models

# Create your models here.

from django.db import models
from django.utils.text import slugify
from imagekitio import ImageKitStorage

# Create an ImageKit storage instance
imagekit_storage = ImageKitStorage()

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Product(models.Model):
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='products')
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField(blank=True)
    price_ngn = models.PositiveIntegerField(help_text="Price in Naira")
    
    min_size = models.PositiveSmallIntegerField(default=38, help_text="Minimum available shoe size")
    max_size = models.PositiveSmallIntegerField(default=45, help_text="Maximum available shoe size")

    # 🆕 Extra fee logic
    extra_fee_threshold = models.PositiveSmallIntegerField(
        default=45,
        help_text="Sizes above this value attract an extra fee"
    )
    extra_fee_amount = models.PositiveIntegerField(
        default=0,
        help_text="Extra fee (in Naira) for sizes above the threshold"
    )
    
    available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def get_price_for_size(self, size):
        """Return total price depending on the selected size."""
        if size > self.extra_fee_threshold:
            return self.price_ngn + self.extra_fee_amount
        return self.price_ngn

    def __str__(self):
        return f"{self.title} ({self.min_size}-{self.max_size})"


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='products/', storage=imagekit_storage)
    alt_text = models.CharField(max_length=150, blank=True)

    def __str__(self):
        return f"Image for {self.product.title}"
