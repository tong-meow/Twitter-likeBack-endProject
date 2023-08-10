from comments.models import Comment
from django.utils import timezone
from rest_framework.test import APIClient
from testing.testcases import TestCase


COMMENT_URL = '/api/comments/'
TWEET_LIST_API = '/api/tweets/'
TWEET_DETAIL_API = '/api/tweets/{}/'
NEWSFEED_LIST_API = '/api/newsfeeds/'


class CommentApiTests(TestCase):

    def setUp(self):
        self.jesse = self.create_user('jesse')
        self.jesse_client = APIClient()
        self.jesse_client.force_authenticate(self.jesse)
        self.eliza = self.create_user('eliza')
        self.eliza_client = APIClient()
        self.eliza_client.force_authenticate(self.eliza)

        self.tweet = self.create_tweet(self.jesse)

    def test_create(self):
        # cannot create comment with anonymous status
        response = self.anonymous_client.post(COMMENT_URL)
        self.assertEqual(response.status_code, 403)

        # cannot create comment without parameters (tweet_id and content)
        response = self.jesse_client.post(COMMENT_URL)
        self.assertEqual(response.status_code, 400)

        # cannot create comment with only tweet_id
        response = self.jesse_client.post(COMMENT_URL, {'tweet_id': self.tweet.id})
        self.assertEqual(response.status_code, 400)

        # cannot create comment with only content
        response = self.jesse_client.post(COMMENT_URL, {'content': '1'})
        self.assertEqual(response.status_code, 400)

        # cannot create comment if the comment is too long
        response = self.jesse_client.post(COMMENT_URL, {
            'tweet_id': self.tweet.id,
            'content': '1' * 141,
        })
        self.assertEqual(response.status_code, 400)
        self.assertEqual('content' in response.data['errors'], True)

        # create comment only if having both tweet_id and content
        response = self.jesse_client.post(COMMENT_URL, {
            'tweet_id': self.tweet.id,
            'content': '1',
        })
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['user']['id'], self.jesse.id)
        self.assertEqual(response.data['tweet_id'], self.tweet.id)
        self.assertEqual(response.data['content'], '1')

    def test_destroy(self):
        comment = self.create_comment(self.jesse, self.tweet)
        url = '{}{}/'.format(COMMENT_URL, comment.id)

        # cannot delete comment with anonymous status
        response = self.anonymous_client.delete(url)
        self.assertEqual(response.status_code, 403)

        # cannot delete comment with another account
        response = self.eliza_client.delete(url)
        self.assertEqual(response.status_code, 403)

        # delete comment only if the current account sent this comment
        count = Comment.objects.count()
        response = self.jesse_client.delete(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Comment.objects.count(), count - 1)

    def test_update(self):
        comment = self.create_comment(self.jesse, self.tweet, 'original')
        another_tweet = self.create_tweet(self.eliza)
        url = '{}{}/'.format(COMMENT_URL, comment.id)

        # cannot update with anonymous status
        response = self.anonymous_client.put(url, {'content': 'new'})
        self.assertEqual(response.status_code, 403)
        # cannot update comment with another account
        response = self.eliza_client.put(url, {'content': 'new'})
        self.assertEqual(response.status_code, 403)
        comment.refresh_from_db()
        self.assertNotEqual(comment.content, 'new')
        # only update the content of comment
        before_updated_at = comment.updated_at
        before_created_at = comment.created_at
        now = timezone.now()
        response = self.jesse_client.put(url, {
            'content': 'new',
            'user_id': self.eliza.id,
            'tweet_id': another_tweet.id,
            'created_at': now,
        })
        self.assertEqual(response.status_code, 200)
        comment.refresh_from_db()
        self.assertEqual(comment.content, 'new')
        self.assertEqual(comment.user, self.jesse)
        self.assertEqual(comment.tweet, self.tweet)
        self.assertEqual(comment.created_at, before_created_at)
        self.assertNotEqual(comment.created_at, now)
        self.assertNotEqual(comment.updated_at, before_updated_at)

    def test_list(self):
        # must have tweet_id
        response = self.anonymous_client.get(COMMENT_URL)
        self.assertEqual(response.status_code, 400)

        response = self.anonymous_client.get(COMMENT_URL, {
            'tweet_id': self.tweet.id,
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['comments']), 0)

        # comments ordered by created time
        self.create_comment(self.jesse, self.tweet, '1')
        self.create_comment(self.eliza, self.tweet, '2')
        self.create_comment(self.eliza, self.create_tweet(self.eliza), '3')
        response = self.anonymous_client.get(COMMENT_URL, {
            'tweet_id': self.tweet.id,
        })
        self.assertEqual(len(response.data['comments']), 2)
        self.assertEqual(response.data['comments'][0]['content'], '1')
        self.assertEqual(response.data['comments'][1]['content'], '2')

        # only tweet_id is filtered
        response = self.anonymous_client.get(COMMENT_URL, {
            'tweet_id': self.tweet.id,
            'user_id': self.jesse.id,
        })
        self.assertEqual(len(response.data['comments']), 2)

    def test_comments_count(self):
        # test tweet detail api
        tweet = self.create_tweet(self.jesse)
        url = TWEET_DETAIL_API.format(tweet.id)
        response = self.eliza_client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['comments_count'], 0)

        # test tweet list api
        self.create_comment(self.jesse, tweet)
        response = self.eliza_client.get(TWEET_LIST_API, {'user_id': self.jesse.id})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['tweets'][0]['comments_count'], 1)

        # test newsfeeds list api
        self.create_comment(self.eliza, tweet)
        self.create_newsfeed(self.eliza, tweet)
        response = self.eliza_client.get(NEWSFEED_LIST_API)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['newsfeeds'][0]['tweet']['comments_count'], 2)
