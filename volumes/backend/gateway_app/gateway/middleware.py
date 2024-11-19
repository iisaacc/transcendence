import os
from django.http import JsonResponse
from django.conf import settings
from django.utils import translation
# from profileapi.models import Profile

# class LanguagePreferenceMiddleware:
#     # This constructor is called only once to create an instance of the middleware, when the Web server starts
#     def __init__(self, get_response):
#         self.get_response = get_response
    
#     def __call__(self, request):
#       if request.user.is_authenticated:
#         language = request.profile.preferred_language
#         translation.activate(profile.preferred_language)
#         request.LANGUAGE_CODE = translation.get_language()