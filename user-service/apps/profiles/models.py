from django.db import models


class UserProfile(models.Model):
    userId = models.CharField(max_length=36, unique=True, db_index=True)
    displayName = models.CharField(max_length=30, blank=True, db_index=True)
    bio = models.TextField(max_length=500, blank=True)
    avatar = models.ImageField(upload_to="avatars/", blank=True, null=True)
    country = models.CharField(max_length=2, blank=True)
    title = models.CharField(max_length=10, blank=True, default="")
    createdAt = models.DateTimeField(auto_now_add=True)
    updatedAt = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "user_profiles"
        verbose_name = "User Profile"
        verbose_name_plural = "User Profiles"

    def __str__(self):
        return self.displayName or self.userId
