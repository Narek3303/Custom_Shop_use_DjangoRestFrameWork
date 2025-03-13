from django import forms
from .models import Product, Image
from django.contrib import admin


class ImageAdminForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = '__all__'

    images = forms.ModelMultipleChoiceField(
        queryset=Image.objects.all(),
        widget=admin.widgets.FilteredSelectMultiple('Images', False)
    )