from django.db import models


class FriendStatus(models.TextChoices):
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    BLOCKED = "BLOCKED"


class Friend(models.Model):
    userId = models.CharField(max_length=36, db_index=True)
    friendId = models.CharField(max_length=36, db_index=True)
    status = models.CharField(
        max_length=10,
        choices=FriendStatus.choices,
        default=FriendStatus.PENDING,
        db_index=True,
    )
    createdAt = models.DateTimeField(auto_now_add=True)
    updatedAt = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "user_friends"
        constraints = [
            models.UniqueConstraint(
                fields=["userId", "friendId"],
                name="unique_friendship",
            )
        ]
        indexes = [
            models.Index(fields=["userId", "status"]),
            models.Index(fields=["friendId", "status"]),
        ]

    def __str__(self):
        return f"{self.userId} -> {self.friendId} ({self.status})"
