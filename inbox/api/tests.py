from notifications.models import Notification
from testing.testcases import TestCase

COMMENT_URL = '/api/comments/'
LIKE_URL = '/api/likes/'
NOTIFICATION_URL = '/api/notifications/'


class NotificationTests(TestCase):

    def setUp(self):
        super(NotificationTests, self).setUp()
        self.jesse, self.jesse_client = self.create_user_and_client('jesse')
        self.eliza, self.eliza_client = self.create_user_and_client('dong')
        self.eliza_tweet = self.create_tweet(self.eliza)

    def test_comment_create_api_trigger_notification(self):
        self.assertEqual(Notification.objects.count(), 0)
        self.jesse_client.post(COMMENT_URL, {
            'tweet_id': self.eliza_tweet.id,
            'content': 'a ha',
        })
        self.assertEqual(Notification.objects.count(), 1)

    def test_like_create_api_trigger_notification(self):
        self.assertEqual(Notification.objects.count(), 0)
        self.jesse_client.post(LIKE_URL, {
            'content_type': 'tweet',
            'object_id': self.eliza_tweet.id,
        })
        self.assertEqual(Notification.objects.count(), 1)


class NotificationApiTests(TestCase):

    def setUp(self):
        self.jesse, self.jesse_client = self.create_user_and_client('jesse')
        self.eliza, self.eliza_client = self.create_user_and_client('eliza')
        self.jesse_tweet = self.create_tweet(self.jesse)

    def test_unread_count(self):
        self.eliza_client.post(LIKE_URL, {
            'content_type': 'tweet',
            'object_id': self.jesse_tweet.id,
        })

        url = '/api/notifications/unread-count/'
        response = self.jesse_client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['unread_count'], 1)

        comment = self.create_comment(self.jesse, self.jesse_tweet)
        self.eliza_client.post(LIKE_URL, {
            'content_type': 'comment',
            'object_id': comment.id,
        })
        response = self.jesse_client.get(url)
        self.assertEqual(response.data['unread_count'], 2)

    def test_mark_all_as_read(self):
        self.eliza_client.post(LIKE_URL, {
            'content_type': 'tweet',
            'object_id': self.jesse_tweet.id,
        })
        comment = self.create_comment(self.jesse, self.jesse_tweet)
        self.eliza_client.post(LIKE_URL, {
            'content_type': 'comment',
            'object_id': comment.id,
        })

        unread_url = '/api/notifications/unread-count/'
        response = self.jesse_client.get(unread_url)
        self.assertEqual(response.data['unread_count'], 2)

        mark_url = '/api/notifications/mark-all-as-read/'
        response = self.jesse_client.get(mark_url)
        self.assertEqual(response.status_code, 405)
        response = self.jesse_client.post(mark_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['marked_count'], 2)
        response = self.jesse_client.get(unread_url)
        self.assertEqual(response.data['unread_count'], 0)

    def test_list(self):
        self.eliza_client.post(LIKE_URL, {
            'content_type': 'tweet',
            'object_id': self.jesse_tweet.id,
        })
        comment = self.create_comment(self.jesse, self.jesse_tweet)
        self.eliza_client.post(LIKE_URL, {
            'content_type': 'comment',
            'object_id': comment.id,
        })

        response = self.anonymous_client.get(NOTIFICATION_URL)
        self.assertEqual(response.status_code, 403)
        response = self.eliza_client.get(NOTIFICATION_URL)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 0)
        response = self.jesse_client.get(NOTIFICATION_URL)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 2)
        notification = self.jesse.notifications.first()
        notification.unread = False
        notification.save()
        response = self.jesse_client.get(NOTIFICATION_URL)
        self.assertEqual(response.data['count'], 2)
        response = self.jesse_client.get(NOTIFICATION_URL, {'unread': True})
        self.assertEqual(response.data['count'], 1)
        response = self.jesse_client.get(NOTIFICATION_URL, {'unread': False})
        self.assertEqual(response.data['count'], 1)

    def test_update(self):
        self.eliza_client.post(LIKE_URL, {
            'content_type': 'tweet',
            'object_id': self.jesse_tweet.id,
        })
        comment = self.create_comment(self.jesse, self.jesse_tweet)
        self.eliza_client.post(LIKE_URL, {
            'content_type': 'comment',
            'object_id': comment.id,
        })
        notification = self.jesse.notifications.first()

        url = '/api/notifications/{}/'.format(notification.id)
        response = self.eliza_client.post(url, {'unread': False})
        self.assertEqual(response.status_code, 405)
        response = self.anonymous_client.put(url, {'unread': False})
        self.assertEqual(response.status_code, 403)
        response = self.eliza_client.put(url, {'unread': False})
        self.assertEqual(response.status_code, 404)
        response = self.jesse_client.put(url, {'unread': False})
        self.assertEqual(response.status_code, 200)
        unread_url = '/api/notifications/unread-count/'
        response = self.jesse_client.get(unread_url)
        self.assertEqual(response.data['unread_count'], 1)

        response = self.jesse_client.put(url, {'unread': True})
        response = self.jesse_client.get(unread_url)
        self.assertEqual(response.data['unread_count'], 2)
        response = self.jesse_client.put(url, {'verb': 'newverb'})
        self.assertEqual(response.status_code, 400)
        response = self.jesse_client.put(url, {'verb': 'newverb', 'unread': False})
        self.assertEqual(response.status_code, 200)
        notification.refresh_from_db()
        self.assertNotEqual(notification.verb, 'newverb')
