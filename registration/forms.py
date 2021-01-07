from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from registration import models


class SignUpForm(UserCreationForm):
    first_name = forms.CharField(max_length=50)
    last_name = forms.CharField(max_length=50)
    email = forms.EmailField(max_length=50)

    class Meta:
        model = User
        fields = [
            "username",
            "first_name",
            "last_name",
            "email",
        ]


class RegistrationForm(forms.ModelForm):
    class Meta:
        model = models.RegistrationForm
        exclude = ["user"]
        labels = {
            "pronouns": "Pronouns (He/him), (She/her), (They/them), etc.",
            "physical_fitness": "Describe your current physical fitness and level of activity",
            "medical_condition_description": "If you have any medical conditions please describe them below",
            "allergy_condition_description": "If you have any allergies please describe them below",
            "medications_descriptions": "If you are taking any medications please describe them below",
            "medical_insurance": "Check this box if you have medical insurance "
            "(medical insurance is required to take this course)",
            "relation_of_policy_holder": "Relation of policy holder to you",
            "signature": "Enter your initials here to certify that the information is "
            "true and correct to your knowledge",
        }
        widgets = {
            "date_of_birth": forms.DateInput(attrs={"type": "date"}),
            "todays_date": forms.DateInput(attrs={"type": "date"}),
        }
