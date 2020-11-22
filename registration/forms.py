from django.forms import ModelForm
from registration import models


class BMCRegistrationForm(ModelForm):
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
            "relation_of_policy_holder": "Relation of policy holder to you"
        }
