from django.db import models
from django.contrib.auth.models import User
from django.conf import settings


class ApplicationStatus(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    is_closed = models.BooleanField(default=True)
    last_closed = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"User: {self.user.username}, Application Closed: {self.is_closed} at {self.last_closed}"
