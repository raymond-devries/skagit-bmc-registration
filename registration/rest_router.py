from rest_framework.routers import DefaultRouter

from registration import rest_views

router = DefaultRouter()
router.register("eligible_courses", rest_views.ListClasses)
