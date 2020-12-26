from rest_framework import permissions, viewsets

from registration import models, serializers


class ListClasses(viewsets.ReadOnlyModelViewSet):
    cart = models.UserCart.objects.get(id=1)
    queryset = cart.eligible_courses
    serializer_class = serializers.CourseTypeSerializer
