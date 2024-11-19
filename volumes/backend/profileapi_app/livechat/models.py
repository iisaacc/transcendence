from django.db import models
from profileapi.models import Profile

class Message(models.Model):
    send_user = models.ForeignKey(Profile, related_name='sent_messages', on_delete=models.CASCADE, default=1)
    dest_user = models.ForeignKey(Profile, related_name='received_messages', on_delete=models.CASCADE, default=1)
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    read = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username}: {self.message[:20]}"