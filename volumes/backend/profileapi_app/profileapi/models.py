from django.db import models
from django import forms

class Profile(models.Model):
    user_id = models.IntegerField(unique=True) # This is the user_id from the authentif app
    display_name = models.CharField(max_length=16, unique=True)
    city = models.CharField(max_length=16, blank=True, default='Málaga')
    country = models.CharField(max_length=16, blank=True, default='Spain')
    friends = models.ManyToManyField('self', blank=True, symmetrical=True)
    blocked_users = models.ManyToManyField('self', blank=True, symmetrical=False)
    preferred_language = models.CharField(max_length=2,choices=[('en', 'English'),('fr', 'French'),('es', 'Spanish')],default='en')

    # This method is used to display the object in the admin panel
    def __str__(self):
        return f'{self.display_name} from {self.city}, {self.country}'

class Notification(models.Model):
    sender = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='sender')
    receiver = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='receiver')
    type = models.CharField(max_length=23) # friend_request, friend_request_response, message
    message = models.CharField(max_length=256)
    date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=16, default='unread') # unread, read
    game_type = models.CharField(max_length=16, null=True, blank=True, default='')

    def __str__(self):
        return f'{self.sender.user_id} to {self.receiver.user_id}'