from django.test import TestCase
from django.contrib.auth.models import User
from unittest.mock import patch
from ..models import Product, Order, OrderItem
class OrderItemSignalTestCase(TestCase):
    """
    Tests the 'decrement_stock' signal which fires on post_save of OrderItem.
    """

    def setUp(self):
        # Create a user for orders
        self.user = User.objects.create_user(username='testuser', password='testpass')

        # Create a product with stock
        self.product = Product.objects.create(
            name='Test Product',
            description='A product for testing',
            price=100.00,
            stock=10
        )

        # Create an order to associate with OrderItem
        self.order = Order.objects.create(user=self.user, status='pending')

    def test_decrement_stock(self):
        """
        Ensure that creating an OrderItem decrements the Product's stock.
        """
        # Initial stock
        self.assertEqual(self.product.stock, 10, "Initial stock should be 10")

        # Create an OrderItem that should trigger the signal
        order_item = OrderItem.objects.create(
            order=self.order,
            product=self.product,
            quantity=3
        )
        order_item.save()

        # Reload product from DB to check if stock decremented
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 7, "Product stock should decrement by 3")


class OrderSignalTestCase(TestCase):
    """
    Tests the 'order_completed_actions' signal which fires on post_save of Order
    if status changes to 'completed'.
    """

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.order = Order.objects.create(user=self.user, status='pending')

    @patch('builtins.print')
    def test_order_completed_actions(self, mock_print):
        """
        Ensure that setting the Order's status to 'completed' triggers the appropriate signal logic.
        In our example, we just print a message. In a real app, this might send an email, update loyalty points, etc.
        """
        # Initially, status is 'pending'. No signal is triggered yet.
        self.order.status = 'completed'
        self.order.save()

        # The signal should detect the status change and print a message
        mock_print.assert_any_call(f"Order #{self.order.pk} is now completed. Sending invoice email...")
