from .tweet import Tweet
from django.contrib.auth.models import User
from django.db import models
from tweets.constants import TweetPhotoStatus, TWEET_PHOTO_STATUS_CHOICES


class TweetPhoto(models.Model):
    tweet = models.ForeignKey(Tweet, on_delete=models.SET_NULL, null=True)

    user = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)

    file = models.FileField()
    order = models.IntegerField(default=0)

    status = models.IntegerField(
        default=TweetPhotoStatus.PENDING,
        choices=TWEET_PHOTO_STATUS_CHOICES,
    )

    has_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        index_together = (
            ('user', 'created_at'),
            ('has_deleted', 'created_at'),
            ('status', 'created_at'),
            ('tweet', 'order'),
        )

    def __str__(self):
        return f'{self.tweet_id}: {self.file}'
