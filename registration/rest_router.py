from django.urls import path
from rest_framework.routers import DefaultRouter

from registration import rest_views

router = DefaultRouter()
router.register(
    "eligible-courses",
    rest_views.ListEligibleCoursesView,
    basename="eligible_courses",
)
router.register("cart-item", rest_views.CartItemView, basename="cart_item")
router.register("wait-list", rest_views.WaitListView, basename="wait_list")
router.register("cart-cost", rest_views.CartCostView, basename="cart_cost")

urlpatterns = [
    path(
        "create-checkout-session/",
        rest_views.create_checkout_session,
        name="checkout_session",
    ),
    path("stripe-webhook/", rest_views.stripe_checkout_webhook, name="stripe_webhook"),
    path("add-courses/", rest_views.AddCoursesView.as_view(), name="add_courses"),
]
