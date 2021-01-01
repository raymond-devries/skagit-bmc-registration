from rest_framework.routers import DefaultRouter

from registration import rest_views

router = DefaultRouter()
router.register(
    "eligible_courses",
    rest_views.ListEligibleCoursesView,
    basename="eligible_courses",
)
router.register("cart_item", rest_views.CartItemView, basename="cart_item")
router.register("wait_list", rest_views.WaitListView, basename="wait_list")
router.register("cart_cost", rest_views.CartCostView, basename="cart_cost")
