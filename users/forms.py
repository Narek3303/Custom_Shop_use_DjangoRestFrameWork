from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserChangeForm
from django.utils.translation import gettext_lazy as _




class EmailUserCreationForm(forms.ModelForm):
    """
    A form that creates a user, with no privileges, from the given email and
    password.
    """
    password1 = forms.CharField(label=_('gaxtnabar'),
                                widget=forms.PasswordInput)
    password2 = forms.CharField(label=_('gaxtnabari verifikacum'),
                                widget=forms.PasswordInput,
                                help_text=_('Enter the same password as '
                                'above, for verification.'))