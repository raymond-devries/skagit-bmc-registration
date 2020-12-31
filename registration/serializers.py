from rest_framework import serializers

from registration import models


class CourseDateSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.CourseDate
        fields = ["name", "start", "end"]


class CourseSerializer(serializers.ModelSerializer):
    coursedate_set = CourseDateSerializer(many=True)

    class Meta:
        model = models.Course
        fields = ["id", "specifics", "capacity", "coursedate_set"]


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
            "requirement",
            "course_set",
        ]


class CartCourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Course
        fields = ["id", "specifics"]


class CartItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.CartItem
        fields = ["id", "course"]


class CartItemListSerializer(CartItemSerializer):
    course = CartCourseSerializer()
