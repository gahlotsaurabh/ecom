from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User


class BaseContent(models.Model):
    """
        Captures BaseContent as created On and modified On and active field.
        common field accessed for the following classes.
    """
    created_on = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)
    active = models.BooleanField(default=True)

    class Meta:
        abstract = True

    def __str__(self):
        return self.id


CATEGORY_TYPE = [
    ("UPPERWEAR", 'UPPERWEAR'),
    ("BOTTOMWEAR", 'BOTTOMWEAR'),
    ("FOOTWEAR", 'FOOTWEAR')
]


class Category(BaseContent):
    name = models.CharField(_('Category Name'), max_length=250)
    _type = models.CharField(
        choices=CATEGORY_TYPE, default="UPPERWEAR", max_length=250
    )

    def __str__(self):
        return "%s - %s" % (self.name, self.id)


class Product(BaseContent):
    name = models.CharField(_('Product Name'), max_length=1000)
    description = models.TextField(_('Description'), blank=True, null=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)

    def __str__(self):
        return "%s - %s" % (self.name, self.id)


SIZE_OPTION = [
    ("S", 'S'),
    ("M", 'M'),
    ("L", 'L'),
    ("XL", 'XL'),
    ("XXL", 'XXL'),
    ("XXXL", 'XXXL'),
]


class ProductDetail(BaseContent):
    size = models.CharField(
        choices=SIZE_OPTION, default="S", max_length=250
    )
    quantity = models.IntegerField(_('Quantity for particular size'))
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, db_index=True,
        related_name="details"
    )
    price = models.IntegerField(_('Product Price'), )

    class Meta:
        unique_together = (("product", "size",),)

    def __str__(self):
        return "%s - %s - %s" % (self.size, self.quantity, self.id)


class Image(BaseContent):
    image = models.ImageField(upload_to='product_img')
    order = models.IntegerField(help_text=_(
        'To order multiple image for single product')
    )
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, db_index=True,
        related_name="product_image"
    )

    def __str__(self):
        return "%s - %s" % (self._type, self.image)


class Cart(BaseContent):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    item = models.ManyToManyField(Product, blank=True, through='CartItem')

    def __str__(self):
        return "%s - %s" % (self.user, self.id)

    @property
    def cart_total(self):
        total = 0
        for i in CartItem.objects.filter(cart=self, is_wishlist_item=False):
            if ProductDetail.objects.filter(
                    product=i.product, size=i.size, quantity__gt=0
            ).exists():
                pro_d = ProductDetail.objects.filter(
                    product=i.product, size=i.size, quantity__gt=0).first()
                if pro_d is not None and pro_d.quantity-i.quantity >= 0:
                    total = total + (pro_d.price * i.quantity)
            else:
                i.delete()
        return total


class CartItem(BaseContent):
    cart = models.ForeignKey(
        Cart, on_delete=models.CASCADE
    )
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name='cart_items'
    )
    product_detail = models.ForeignKey(
        ProductDetail, on_delete=models.CASCADE,
        related_name='cart_product_detail'
    )
    is_wishlist_item = models.BooleanField(default=True)
    quantity = models.IntegerField(_('Quantity'), help_text=_(
        'quantity for particular size.'), default=1
    )
    size = models.CharField(choices=SIZE_OPTION, default="S", max_length=250)

    class Meta:
        unique_together = (("product", "is_wishlist_item", "cart"),)

    def __str__(self):
        return "%s - %s" % (self.id, self.cart)
