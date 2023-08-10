from testing.testcases import TestCase
from inbox.services import NotificationService
from notifications.models import Notification


class NotificationServiceTests(TestCase):

    def setUp(self):
        self.jesse = self.create_user('jesse')
        self.eliza = self.create_user('eliza')
        self.jesse_tweet = self.create_tweet(self.jesse)

    def test_send_comment_notification(self):
        # do not dispatch notification if tweet user == comment user
        comment = self.create_comment(self.jesse, self.jesse_tweet)
        NotificationService.send_comment_notification(comment)
        self.assertEqual(Notification.objects.count(), 0)

        # dispatch notification if tweet user != comment user
        comment = self.create_comment(self.eliza, self.jesse_tweet)
        NotificationService.send_comment_notification(comment)
        self.assertEqual(Notification.objects.count(), 1)

    def test_send_like_notification(self):
        # do not dispatch notification if tweet user == like user
        like = self.create_like(self.jesse, self.jesse_tweet)
        NotificationService.send_like_notification(like)
        self.assertEqual(Notification.objects.count(), 0)

        # dispatch notification if tweet user != comment user
        like = self.create_comment(self.eliza, self.jesse_tweet)
        NotificationService.send_comment_notification(like)
        self.assertEqual(Notification.objects.count(), 1)
