from rest_framework import permissions, viewsets

from registration import models, serializers


class ListEligibleCourses(viewsets.ReadOnlyModelViewSet):
    serializer_class = serializers.CourseTypeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return models.UserCart.objects.get(user=user).eligible_courses
