import os
import sys
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework.permissions import AllowAny
from rest_framework.decorators import action
from rest_framework import status
from .models import (
    Category, Cart, CartItem, ProductDetail, Product, Image
)
from rest_framework.viewsets import ModelViewSet
from .serializer import (
    CategorySerializer, CartSerializer, ProductSerializerCreate,
    ProductDetailSerializer, ProductSerializer, ImageSerializer
)
from .renderers import Response


schema_view = get_schema_view(
    openapi.Info(
        title="Ecom API",
        default_version='v1',
        description="Test description",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="contact@snippets.local"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(AllowAny,),
)


class ProductViewset(ModelViewSet):
    """
    """
    queryset = Product.objects.all()

    def get_serializer_class(self):
        if self.action == 'create':
            return ProductSerializerCreate
        else:
            return ProductSerializer


class CategoryViewset(ModelViewSet):
    """
    type = {
        (UPPERWEAR),
        (BOTTOMWEAR),
        (FOOTWEAR)
    }
    """
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class CartViewset(ModelViewSet):
    """
    payload(patch)= {
        "action": "add/remove/delete"
        "product_detail": product_detail_id,
        "product": product_id
    }
    add/remove action is used to add or remove one quantity of product into the
    cart 
    delete action to remove product completly from cart.
    """
    queryset = Cart.objects.all()
    serializer_class = CartSerializer

    def list(self, request, pk=None):
        status_ = status.HTTP_500_INTERNAL_SERVER_ERROR
        message = "Internal server error"
        data = []
        try:
            serializer = self.serializer_class(
                self.queryset.filter(user=self.request.user),
                many=True, fields=('id', 'cart_item')
            )
            status_ = status.HTTP_200_OK
            message = ""
            data = serializer.data
            data[0]["cart_total"] = self.queryset.filter(
                user=self.request.user).first().cart_total if \
                self.queryset.filter(user=self.request.user).exists() \
                else 0
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno)
            print(str(e))
        return Response(data, data_status=status_, message=message)

    def partial_update(self, request, pk=None):
        status_ = status.HTTP_500_INTERNAL_SERVER_ERROR
        message = "Internal server error"
        data = []
        try:
            instance = self.get_object()
            if not request.data.get('product') and \
                not request.data.get('product_detail') and \
                    not request.data.get('action'):
                status_ = status.HTTP_400_BAD_REQUEST
                message = 'Required product_detail, product and action.'
                return Response(
                    data,
                    data_status=status_,
                    message=message
                )
            if Product.objects.filter(id=request.data.get('product')).exists():
                product = Product.objects.filter(
                    id=request.data.get('product')
                ).first()
                if ProductDetail.objects.filter(
                    id=request.data.get('product_detail'), product=product,
                    quantity__gt=0
                ).exists():
                    product_detail = ProductDetail.objects.filter(
                        id=request.data.get('product_detail'), product=product
                    ).first()
                else:
                    return Response(
                        data,
                        data_status=status_,
                        message="Not in stock"
                    )
            else:
                return Response(
                    data,
                    data_status=status_,
                    message=message
                )
            if CartItem.objects.filter(
                product=product, cart=instance,
                is_wishlist_item=False, product_detail=product_detail.id
            ).exists():
                cart_item = CartItem.objects.filter(
                    product=product,
                    cart=instance,
                    is_wishlist_item=False,
                    product_detail=product_detail.id
                ).first()
            else:
                q = request.data.get('quantity') if\
                    request.data.get('action') == "add_quantity" else 1
                cart_item, _ = CartItem.objects.get_or_create(
                    product=product, cart=instance, is_wishlist_item=False,
                    size=product_detail.size, product_detail=product_detail,
                    quantity=q
                )
                status_ = status.HTTP_400_BAD_REQUEST
                message = 'Bag item created unexpectedly'
                if _:
                    serializer = self.get_serializer(
                        self.get_object(), fields=(
                            'id', 'cart_item', "product_detail")
                    )
                    data.append(serializer.data)
                    data[0]["cart_total"] = self.queryset.filter(
                        user=self.request.user).first().cart_total if \
                        self.queryset.filter(user=self.request.user).exists() \
                        else 0
                    status_ = status.HTTP_200_OK
                    message = 'Bag Updated'
                return Response(
                    data,
                    data_status=status_,
                    message=message
                )
            cartItems = instance.item.filter(
                cart_items__is_wishlist_item=False,
                cart_items__size=product_detail.size
            )
            if product_detail is None or product not in cartItems:
                message = "Bad request"
                status_ = status.HTTP_400_BAD_REQUEST
                return Response(data, data_status=status_, message=message)

            if request.data.get('action') == 'add':
                if product_detail.quantity >= cart_item.quantity + 1:
                    cart_item.quantity += 1
                    cart_item.save()
                    serializer = self.get_serializer(
                        self.get_object(), fields=(
                            'id', 'cart_item', "product_detail")
                    )
                    data.append(serializer.data)
                    data[0]["cart_total"] = self.queryset.filter(
                        user=self.request.user).first().cart_total if \
                        self.queryset.filter(user=self.request.user).exists() \
                        else 0
                    return Response(
                        data,
                        data_status=status.HTTP_200_OK,
                        message='Cart Updated (product added)'
                    )
                serializer = self.get_serializer(
                    self.get_object(), fields=(
                        'id', 'cart_item', "product_detail")
                )
                data.append(serializer.data)
                data[0]["cart_total"] = self.queryset.filter(
                    user=self.request.user).first().cart_total if \
                    self.queryset.filter(user=self.request.user).exists() \
                    else 0
                return Response(
                    data,
                    data_status=status.HTTP_400_BAD_REQUEST,
                    message='Quantity in bag reached stock quantity'
                )
            # to remove products in cart
            if request.data.get('action') == "remove":
                if product in cartItems:
                    if cart_item and cart_item.quantity > 1:
                        cart_item.quantity -= 1
                        cart_item.save()
                    else:
                        cart_item.delete()
                    status_ = status.HTTP_200_OK
                    message = "Cart Updated(product removed)"

            if request.data.get('action') == "delete":
                if product in cartItems:
                    cart_item.delete()
                    status_ = status.HTTP_200_OK
                    message = "Bag Updated(product deleted)"

            serializer = self.get_serializer(
                self.get_object(), fields=('id', 'cart_item', "product_detail")
            )
            data.append(serializer.data)
            data[0]["cart_total"] = self.queryset.filter(
                user=self.request.user).first().cart_total if \
                self.queryset.filter(user=self.request.user).exists() \
                else 0
            return Response(data, data_status=status_, message=message)
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno)
            print(str(e))


class ImageViewset(ModelViewSet):
    """
    """
    queryset = Image.objects.all()
    serializer_class = ImageSerializer
