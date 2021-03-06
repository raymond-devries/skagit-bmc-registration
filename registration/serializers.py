from rest_framework import serializers

from registration import models


class CourseDateSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.CourseDate
        fields = ["name", "start", "end"]


class WaitListSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.WaitList
        fields = ["id", "course"]


class CourseSerializer(serializers.ModelSerializer):
    coursedate_set = CourseDateSerializer(many=True)
    user_on_wait_list = serializers.SerializerMethodField("_user_on_wait_list")

    class Meta:
        model = models.Course
        fields = [
            "id",
            "specifics",
            "capacity",
            "spots_left",
            "is_full",
            "user_on_wait_list",
            "coursedate_set",
        ]

    def _user_on_wait_list(self, obj):
        user = self.context.get("user")
        return WaitListSerializer(obj.user_on_wait_list(user)).data


class RequirementSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.CourseType
        fields = ["name"]


class CourseTypeSerializer(serializers.ModelSerializer):
    eligible = serializers.BooleanField()
    course_set = CourseSerializer(many=True)
    requirement = RequirementSerializer()

    class Meta:
        model = models.CourseType
        fields = [
            "eligible",
            "name",
            "abbreviation",
            "description",
            "visible",
            "cost",
            "cost_human",
            "requirement",
            "course_set",
        ]


class CartCourseTypeSerializer(serializers.ModelSerializer):
    requirement = RequirementSerializer()

    class Meta:
        model = models.CourseType
        fields = ["name", "abbreviation", "cost", "requirement"]


class CartCourseSerializer(serializers.ModelSerializer):
    type = CartCourseTypeSerializer()
    coursedate_set = CourseDateSerializer(many=True)

    class Meta:
        model = models.Course
        fields = ["specifics", "spots_left", "coursedate_set", "type"]


class CartItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.CartItem
        fields = ["id", "course"]


class CartItemListSerializer(CartItemSerializer):
    course = CartCourseSerializer()


class DiscountSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Discount
        fields = ["discount", "number_of_courses"]


class CartCostSerializer(serializers.ModelSerializer):
    discount = DiscountSerializer()

    class Meta:
        model = models.UserCart
        fields = ["cost", "discount"]
