from django import forms
from django.contrib.auth.models import User

from registration import models
from django.contrib.auth.forms import UserCreationForm


class SignUpForm(UserCreationForm):
    class Meta:
        model = User
        fields = ["first_name", "last_name", "email", "username"]


class BMCRegistrationForm(forms.ModelForm):
    class Meta:
        model = models.BMCRegistration
        fields = "__all__"
        labels = {
            "physical_fitness": "Describe your current physical fitness and level of activity",
            "medical_conditions": "Check this box if you have any medical conditions",
            "medical_condition_description": "If you checked the box, explain your medical conditions",
            "allergy_conditions": "Check this box if you have any allergies",
            "allergy_condition_description": "If you checked the box, explain your allergies",
            "medications": "Check this box if you are taking any medications",
            "medications_descriptions": "If you checked the box, what medications are you taking?",
            "medical_insurance": "Check this box if you have medical insurance "
                                 "(medical insurance is required to take this course)",
            "relation_of_policy_holder": "Relation of policy holder to you",
            "signature": "Enter your initials here to certify that the information is "
                         "true and correct to your knowledge"
        }
