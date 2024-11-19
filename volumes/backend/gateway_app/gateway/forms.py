from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
import re

def validate_username(value):
    if not re.match(r'^[\w-]+$', value):
        raise ValidationError(
            _('Alphanumeric characters, underscores and hyphens only.'),
            params={'value': value},
        )

def validate_city(value):
    # Letters (including letters with accents) and spaces only
    if not re.match(r'^[\u0041-\u005A\u0061-\u007A\u00C0-\u00D6\u00D8-\u00F6\u00F8-\u00FF\u0100-\u017F\u0180-\u024F\s]+$', value):
        raise ValidationError(
            _('Letters and spaces only.'),
            params={'value': value},
        )

class LogInFormFrontend(forms.Form):
  username = forms.CharField(
        max_length=16, 
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'id': 'loginUsername'
          }),
        label=_('Username'), 
        required=True,
        validators=[validate_username],
  )
  password = forms.CharField(
        widget=forms.PasswordInput(attrs={
          'class': 'form-control',
          'id': 'loginPassword'
          }), 
        label=_('Password'), 
        required=True
  )

class SignUpFormFrontend(forms.Form):
  username = forms.CharField(
        max_length=16, 
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'id': 'signupUsername'
          }),
        label=_('Username'), 
        required=True,
        validators=[validate_username],
        )
  password = forms.CharField(
        widget=forms.PasswordInput(attrs={
          'class': 'form-control',
          'id': 'signupPassword'
          }), 
        label=_('Password'), 
        required=True
        )
  confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
          'class': 'form-control',
          'id': 'signupConfirmPassword'
          }), 
        label=_('Confirm password'), 
        required=True
        )

class InviteFriendFormFrontend(forms.Form):
  friendName = forms.CharField(
        max_length=16, 
        widget=forms.TextInput(attrs={
						'type': 'text',
            'class': 'form-control',
            'id': 'usernameInput'
          }),
        label=_("Friend's Name"),
        required=True,
        validators=[validate_username],
        )

class EditProfileFormFrontend(forms.Form):
  avatar = forms.ImageField(
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'id': 'editProfileAvatar'
          }),
        label=_('Upload avatar'),
        required=False,
        )
  username = forms.CharField(
        max_length=16, 
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'id': 'editProfileUsername'
          }),
        label=_('Username'), 
        required=False,
        validators=[validate_username],
        )
  display_name = forms.CharField(
        max_length=16, 
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'id': 'editProfileDisplayName'
          }),
        label=_('Display name'),
        required=False,
        validators=[validate_username],
        )
  country = forms.CharField(
        max_length=16, 
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'id': 'editProfileCountry'
          }),
        label=_('Country'), 
        required=False,
        validators=[validate_city],
        )
  city = forms.CharField(
        max_length=16, 
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'id': 'editProfileCity'
          }),
        label=_('City'), 
        required=False,
        validators=[validate_city],
        )

  preferred_language = forms.ChoiceField(
      choices=[('en', 'English'), ('fr', 'French'), ('es', 'Spanish')],
      initial='en',
      label=_('Language'),
      required=False,
      widget=forms.Select(attrs={
            'class': 'form-control',
            'id': 'editProfilePreferredLanguage'
        })
      )

  new_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
          'class': 'form-control',
          'id': 'editProfilePassword'
          }), 
        label=_('New password'), 
        required=False
        )
  confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
          'class': 'form-control',
          'id': 'editProfileConfirmPassword'
          }), 
        label=_('Confirm new password'), 
        required=False
        )

