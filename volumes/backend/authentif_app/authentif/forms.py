from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserChangeForm
from .models import User
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _
import logging
logger = logging.getLogger(__name__)


class SignUpForm(forms.ModelForm):
    confirm_password = forms.CharField(widget=forms.PasswordInput, required=False)

    class Meta:
        model = User
        fields = ['username', 'password', 'id_42']

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")
        id_42 = cleaned_data.get("id_42")

        # If id_42 is provided, no need for password
        if not id_42:
            if not password or not confirm_password:
                raise forms.ValidationError(_("Password and confirmation are required"))
            if password != confirm_password:
                raise forms.ValidationError(_("Passwords do not match"))

        # If id_42 is set, we don't need a password, vice versa
        if id_42 and password:
            raise forms.ValidationError(_("Cannot set both password and id_42"))

        return cleaned_data



class LogInForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control', 'id': 'loginUsername'
    }))
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-control', 'id': 'loginPassword'
    }))

class LogInForm42(AuthenticationForm):
    id = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control', 'id': 'loginId'
    }))

class EditProfileForm(UserChangeForm):

    # current_password = forms.CharField(widget=forms.PasswordInput(attrs={
    #     'class': 'form-control', 'id': 'currentPassword'
    # }), label='Current Password')
    new_username = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control', 'id': 'newUsername'
    }), label=_('New Username'), required=False)

    new_password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-control', 'id': 'newPassword'
    }), label=_('New Password'), required=False)

    confirm_password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-control', 'id': 'signupConfirmPassword'
    }), label=_('Confirm Password'), required=False)

    avatar = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control', 'id': 'avatar'
    }), label=_('Avatar'), required=False) 

    def __init__(self, *args, **kwargs):
        logger.debug("EditProfileForm > __init__")
        super(EditProfileForm, self).__init__(*args, **kwargs)
        logger.debug(f"self.fields: {self.fields}")
        del self.fields['password']
        logger.debug("Password field deleted")

    class Meta:
        logger.debug("EditProfileForm > Meta")
        model = User
        logger.debug(f"model: {model}")
        fields = ('username', 'avatar')
        logger.debug(f"fields: {fields}")



    def clean(self):
        logger.debug("EditProfileForm > clean")
        logger.debug(f"new_password: {self.cleaned_data.get('new_password')}")
        logger.debug(f"confirm_password: {self.cleaned_data.get('confirm_password')}")
        logger.debug(f"new_username: {self.cleaned_data.get('username')}")
        cleaned_data = super().clean()
        new_password = cleaned_data.get('new_password')
        confirm_password = cleaned_data.get('confirm_password')
        new_username = cleaned_data.get('username')
        avatar = cleaned_data.get('avatar')
        logger.debug(f'avatar: {avatar}')

        # Change avatar
        if avatar:
            self.instance.avatar = avatar

        # Validate current password
        if new_password and confirm_password:
            logger.debug("EditProfileForm > clean > if password and confirm_password")
            if new_password != confirm_password:
                logger.debug("EditProfileForm > clean > if password != confirm_password")
                raise ValidationError(_("Passwords do not match"))
            else:
              self.instance.set_password(new_password)
              if new_username:
                self.instance.username = new_username
        logger.debug("EditProfileForm > clean > return cleaned_data")
        return cleaned_data
