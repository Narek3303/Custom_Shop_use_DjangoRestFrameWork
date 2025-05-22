from django import forms
from .models import Product, Image
from django.contrib import admin
from django.utils.html import format_html


class ImageAdminForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = '__all__'

    images = forms.ModelMultipleChoiceField(
        queryset=Image.objects.all(),
        widget=admin.widgets.FilteredSelectMultiple('Images', False)
    )



class ImageWidget(forms.SelectMultiple):
    def render(self, name, value, attrs=None, renderer=None):
        output = []
        for img in Image.objects.all():
            output.append(f'<label><input type="checkbox" name="{name}" value="{img.id}">'
                          f'<img src="{img.image.url}" style="max-width:50px; max-height:50px;"> </label>')
        return format_html(" ".join(output))


class ProductAdminForm(forms.ModelForm):
    image = forms.ModelMultipleChoiceField(queryset=Image.objects.all(), widget=ImageWidget)

    class Meta:
        model = Product
        fields = '__all__'




