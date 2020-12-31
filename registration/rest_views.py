from rest_framework import mixins, permissions, viewsets

from registration import models, serializers


class ListEligibleCoursesView(viewsets.ReadOnlyModelViewSet):
    serializer_class = serializers.CourseTypeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return models.UserCart.objects.get(user=user).eligible_courses


class CartItemView(
    mixins.ListModelMixin,
    mixins.DestroyModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return models.UserCart.objects.get(user=user).cartitem_set.all()

    def perform_create(self, serializer):
        serializer.save(cart=models.UserCart.objects.get(user=self.request.user))

    def get_serializer_class(self):
        if self.action == "list":
            return serializers.CartItemListSerializer
        return serializers.CartItemSerializer
