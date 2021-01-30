from django.urls import path, include
from rest_framework import routers

from .views import (
    CartViewset, CategoryViewset, ProductViewset, ImageViewset
)

router = routers.DefaultRouter()

router.register(r'cart', CartViewset)
router.register(r'category', CategoryViewset)
router.register(r'product', ProductViewset)
router.register(r'image', ImageViewset)

urlpatterns = [
    path('v1/', include(router.urls)),
]
