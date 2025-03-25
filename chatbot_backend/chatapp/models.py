from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

User = get_user_model()

class Chat(models.Model):
    title = models.TextField(max_length=200)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="conversations")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Conversation {self.id} with {self.user.username}"


class Message(models.Model):
    SENDER_CHOICES = [
        ('user', 'User'),
        ('bot', 'Chatbot'),
    ]

    chat = models.ForeignKey(Chat, on_delete=models.CASCADE, related_name='messages')
    sender = models.CharField(max_length=10, choices=SENDER_CHOICES)
    text = models.CharField(max_length=10000)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.timestamp}: {self.sender} - {self.receiver}"


# class ScientificArticle(models.Model):
#     title = models.CharField(max_length=200)
#     article_url = models.URLField(
#         max_length=500, blank=True, null=True, help_text="Official link to the article"
#     )


# class HealthRecommendation(models.Model):
#     patient = models.ForeignKey(User, on_delete=models.CASCADE, related_name="received_recommendations")
#     doctor = models.ForeignKey(User, on_delete=models.CASCADE, related_name="given_recommendations")
#     content = models.TextField()
#     created_at = models.DateTimeField(auto_now_add=True)

#     def save(self, *args, **kwargs):
#         if self.patient.role != 'patient':
#             raise ValidationError({"patient": "Selected user is not a valid patient."})
#         if self.doctor.role != 'doctor':
#             raise ValidationError({"doctor": "Selected user is not a valid doctor."})
        
#         super().save(*args, **kwargs)
