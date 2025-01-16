# E-Commerce API with Order Tracking (DRF + Signals + Middleware)

## Key Focus
- Building a feature-rich E-commerce backend: **products**, **carts**, **orders**, and **payments**.
- Employing **signals** to handle order-related events (e.g., stock updates).
- Creating a **custom middleware** for logging or analytics.

## What You’ll Learn

### Advanced DRF Techniques: [Pre-done]
1. **More complex serializers** (nested or hyperlinked).
2. **Custom permission classes** for admin and non-admin roles.
3. Using **generic vs. function-based vs. class-based views** in DRF.

### Signals
- **Decrementing product stock** automatically when an order is placed.
- **Sending invoice emails** after an order is confirmed.
- **Triggering loyalty points updates** for a user when an order is completed.

### Middlewares
- **Creating a custom middleware** to log every request that hits the API, storing details such as:
    - User agent
    - IP address
    - User ID
    - (in a database or a logging service)
- Optionally adding a **custom security middleware** to check for specific headers or tokens.

## Possible Extensions [To be done later]
- Integrate a **payment gateway simulation** (e.g., mock Stripe or PayPal) to learn about external API calls in DRF.
- Implement **advanced search/filter functionality** (using `django-filter` or DRF filters) for products.
