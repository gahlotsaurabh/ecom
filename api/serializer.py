from rest_framework import serializers
from .models import (
    CartItem, Cart, Category, ProductDetail, Product, Image
)


class DynamicFieldsModelSerializer(serializers.ModelSerializer):
    """
    A ModelSerializer that takes an additional `fields/exclude` argument that
    controls which fields should be displayed.
    """

    def __init__(self, *args, **kwargs):
        # Don't pass the 'fields' arg up to the superclass
        fields = kwargs.pop('fields', None)
        exclude = kwargs.pop('exclude', None)
        # Instantiate the superclass normally
        super(DynamicFieldsModelSerializer, self).__init__(*args, **kwargs)

        if fields is not None:
            # Drop any fields that are not specified in the `fields` argument.
            allowed = set(fields)
            existing = set(self.fields)
            for field_name in existing - allowed:
                self.fields.pop(field_name)

        if exclude:
            # Drop fields that are specified in the `exclude` argument.
            excluded = set(exclude)
            for field_name in excluded:
                try:
                    self.fields.pop(field_name)
                except KeyError:
                    pass


class ProductDetailSerializer(DynamicFieldsModelSerializer):

    class Meta:
        model = ProductDetail
        fields = ('__all__')


class CategorySerializer(DynamicFieldsModelSerializer):

    class Meta:
        model = Category
        fields = ('__all__')


class ImageSerializer(DynamicFieldsModelSerializer):

    class Meta:
        model = Image
        fields = ('__all__')


class ProductSerializerCreate(DynamicFieldsModelSerializer):

    class Meta:
        model = Product
        fields = ('__all__')


class ProductSerializer(DynamicFieldsModelSerializer):
    details = ProductDetailSerializer(
        many=True, read_only=True, fields=('id', 'size', 'price', 'quantity')
    )
    category = CategorySerializer(
        many=False, read_only=True, fields=('id', '_type', 'name')
    )
    product_image = ImageSerializer(
        many=True, read_only=True, fields=('id', 'image')
    )

    class Meta:
        model = Product
        fields = (
            'id', 'name', 'description', 'category', 'details', 'product_image'
        )


class CartItemSerializer(DynamicFieldsModelSerializer):
    product = ProductSerializer(
        read_only=True, fields=(
            'id', 'img', 'name', 'category', 'avg_price'
        )
    )
    product_detail = ProductDetailSerializer(
        read_only=True, fields=('id', 'price', 'quantity')
    )

    class Meta:
        model = CartItem
        fields = ('__all__')


class CartSerializer(DynamicFieldsModelSerializer):
    cart_item = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = ('__all__')

    def get_cart_item(self, obj):
        return CartItemSerializer(CartItem.objects.filter(
            is_wishlist_item=False, cart=obj.id
        ), many=True, read_only=True, fields=(
            'id', 'size', 'quantity', 'product', "product_detail")
        ).data
