from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver
from main.models import Log  # User modelini settings dan olish uchun
from django.contrib.auth import get_user_model

User = get_user_model()  # main.User modelini dinamik ravishda olish

@receiver(user_logged_in)
def log_user_login(sender, user, request, **kwargs):
    Log.objects.create(user=user, action="Tizimga kirish")

@receiver(user_logged_out)
def log_user_logout(sender, user, request, **kwargs):
    Log.objects.create(user=user, action="Tizimdan chiqish")