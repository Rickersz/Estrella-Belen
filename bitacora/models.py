from django.db import models
from django.conf import settings


class AccessLog(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    email = models.EmailField(null=True, blank=True)
    ip_address = models.CharField(max_length=45, blank=True)
    action = models.CharField(max_length=50, blank=True)
    path = models.CharField(max_length=255, blank=True)
    user_agent = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        who = self.user.email if self.user else (self.email or 'Anon')
        return f"{self.action} - {who} @ {self.ip_address}"
