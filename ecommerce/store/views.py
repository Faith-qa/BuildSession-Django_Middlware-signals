from django.shortcuts import render

# Create your views here.
# store/views.py
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from .permisions import IsAdminOrReadOnly
from .models import Product, Cart, CartItem, Order, OrderItem, Payment
from .serializers import (
    ProductSerializer, CartSerializer, CartItemSerializer,
    OrderSerializer, OrderItemSerializer, PaymentSerializer
)

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAdminOrReadOnly]


class CartViewSet(viewsets.ModelViewSet):
    queryset = Cart.objects.all()
    serializer_class = CartSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Cart.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)

    def create(self, request, *args, **kwargs):
        # Typically, you'd create an order from the user's cart items
        user = request.user
        cart = get_object_or_404(Cart, user=user)
        if cart.items.count() == 0:
            return Response({"detail": "Cart is empty"}, status=status.HTTP_400_BAD_REQUEST)

        order = Order.objects.create(user=user, status='pending')
        for cart_item in cart.items.all():
            OrderItem.objects.create(
                order=order,
                product=cart_item.product,
                quantity=cart_item.quantity
            )
        cart.items.all().delete()  # clear the cart
        serializer = self.get_serializer(order)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        # In a real scenario, you might integrate a payment gateway here
        order_id = request.data.get('order')
        order = get_object_or_404(Order, id=order_id, user=request.user)
        amount = request.data.get('amount')

        if Payment.objects.filter(order=order).exists():
            return Response({"detail": "Payment already exists"}, status=status.HTTP_400_BAD_REQUEST)

        # Save payment
        payment = Payment.objects.create(order=order, amount=amount, paid=True)
        # You could update the order status or trigger signals here
        order.status = 'confirmed'
        order.save()

        serializer = self.get_serializer(payment)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
