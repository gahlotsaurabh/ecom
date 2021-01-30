from django.contrib import admin
from .models import (
    Category, CartItem, Cart, Product, ProductDetail, Image
)


admin.site.register(Cart)
admin.site.register(Category)
admin.site.register(CartItem)
admin.site.register(Product)
admin.site.register(ProductDetail)
admin.site.register(Image)
