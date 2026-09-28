from django.db import models


class BlockType(models.TextChoices):
    BLOCK = "BLOCK", "Block"
    MUTE = "MUTE", "Mute"


class UserBlock(models.Model):
    userId = models.CharField(max_length=36, db_index=True)
    blockedId = models.CharField(max_length=36, db_index=True)
    type = models.CharField(
        max_length=10,
        choices=BlockType.choices,
        default=BlockType.BLOCK,
        db_index=True,
    )
    reason = models.CharField(max_length=200, blank=True, default="")
    createdAt = models.DateTimeField(auto_now_add=True)
    updatedAt = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "user_blocks"
        constraints = [
            models.UniqueConstraint(
                fields=["userId", "blockedId", "type"],
                name="unique_user_block",
            )
        ]
        indexes = [
            models.Index(fields=["userId", "type"]),
            models.Index(fields=["blockedId", "type"]),
        ]

    def __str__(self):
        return f"{self.userId} {self.type}/{self.blockedId}"