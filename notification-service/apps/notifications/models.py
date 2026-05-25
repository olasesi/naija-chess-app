from django.db import models


class Notification(models.Model):
    class Type(models.TextChoices):
        GAME_INVITE = "game_invite", "Game Invite"
        FRIEND_REQUEST = "friend_request", "Friend Request"
        GAME_RESULT = "game_result", "Game Result"
        TOURNAMENT_UPDATE = "tournament_update", "Tournament Update"
        CHAT_MESSAGE = "chat_message", "Chat Message"
        SYSTEM = "system", "System"
        PROMOTION = "promotion", "Promotion"

    recipient_id = models.CharField(max_length=255, db_index=True)
    type = models.CharField(max_length=50, choices=Type.choices)
    title = models.CharField(max_length=255)
    body = models.TextField()
    data = models.JSONField(default=dict, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "notifications"
        indexes = [
            models.Index(fields=["recipient_id", "-created_at"]),
            models.Index(fields=["recipient_id", "read_at"]),
        ]
        ordering = ["-created_at"]

    def __str__(self):
        return f"[{self.type}] {self.title} -> {self.recipient_id}"


class PushDevice(models.Model):
    class Platform(models.TextChoices):
        WEB = "web", "Web"
        IOS = "ios", "iOS"
        ANDROID = "android", "Android"

    user_id = models.CharField(max_length=255, db_index=True)
    token = models.CharField(max_length=512, unique=True)
    platform = models.CharField(max_length=20, choices=Platform.choices)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "push_devices"
        indexes = [
            models.Index(fields=["user_id", "is_active"]),
        ]

    def __str__(self):
        return f"{self.platform} device for {self.user_id}"
