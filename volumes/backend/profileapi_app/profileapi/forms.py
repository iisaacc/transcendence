from django.http import JsonResponse
from django import forms
from profileapi.models import Profile
from django.core.exceptions import ValidationError
import json
import os
import logging
logger = logging.getLogger(__name__)

class InviteFriendForm(forms.ModelForm):
    friendName = forms.CharField(
          max_length=16, 
          widget=forms.TextInput(attrs={
              'type': 'text',
              'class': 'form-control',
              'id': 'login-name'
            }),
          label="Friend's Name",
          required=True,
          )
    class Meta:
          model = Profile  # Specify the model if needed
          fields = ['friendName']

    def clean_friendName(self):
          friend_name = self.cleaned_data.get('friendName')
          print('must check database if friend_name: ', friend_name)
          try:
            profile = Profile.objects.get(username=friend_name)
            print('User ID:', profile.user_id)
            print('City:', profile.city)
            print('Country:', profile.country)
            print('Played Games:', profile.played_games)
            print('Wins:', profile.wins)
            print('Defeats:', profile.defeats)
            print('Friends:', profile.friends.all())
          except Profile.DoesNotExist:
            print('Profile not found')
            raise ValidationError("This username does not exist.")
          # if not Profile.objects.filter(username=friend_name).exists():
          #     raise ValidationError("This username does not exist.")
          return friend_name

class EditProfileForm(forms.ModelForm):

  country = forms.CharField(
        max_length=16, 
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'id': 'editProfileCountry'
          }),
        label='Country', 
        required=False,
        )
  city = forms.CharField(
        max_length=16, 
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'id': 'editProfileCity'
          }),
        label='City', 
        required=False,
        )

  display_name = forms.CharField(
        max_length=16, 
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'id': 'editProfileDisplayName'
          }),
        label='City', 
        required=False,
        )

  user_id = forms.IntegerField(
        widget=forms.HiddenInput(),
        required=False,
        )

  preferred_language = forms.ChoiceField(
        choices=[('en', 'English'), ('fr', 'French'), ('es', 'Spanish')],
        initial='en',
        label='Language',
        required=False,
        )

  class Meta:
        model = Profile  # Specify the model if needed
        logger.debug(f"model: {model}")
        fields = ['country', 'city', 'user_id', 'display_name', 'preferred_language']
        logger.debug(f"fields: {fields}")

  def clean(self):
        cleaned_data = super().clean() # call the clean method of the parent class
        display_name = cleaned_data.get('display_name')
        country = cleaned_data.get('country')
        logger.debug(f'country: {country}')
        city = cleaned_data.get('city')
        logger.debug(f'city: {city}')
        user_id = cleaned_data.get('user_id')
        logger.debug(f'user_id: {user_id}')
        preferred_language = cleaned_data.get('preferred_language')
        logger.debug(f'preferred_language: {preferred_language}')
  
        try:
          profile = Profile.objects.get(user_id=user_id)
          print('User ID:', profile.user_id)
          if country:
            profile.country = country
          if city:
            profile.city = city
          if display_name:
            profile.display_name = display_name
          if preferred_language:
             profile.preferred_language = preferred_language
          profile.save()
          logger.debug('forms.py > Profile updated')
        except Profile.DoesNotExist:
          print('Profile not found')
          raise ValidationError("This user_id does not exist.")
        return cleaned_data
