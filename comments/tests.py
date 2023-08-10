from testing.testcases import TestCase


class CommentModelTests(TestCase):

    def setUp(self):
        super(CommentModelTests, self).setUp()
        self.jesse = self.create_user('jesse')
        self.tweet = self.create_tweet(self.jesse)
        self.comment = self.create_comment(self.jesse, self.tweet)

    def test_comment(self):
        self.assertNotEqual(self.comment.__str__(), None)

    def test_like_set(self):
        self.create_like(self.jesse, self.comment)
        self.assertEqual(self.comment.like_set.count(), 1)

        self.create_like(self.jesse, self.comment)
        self.assertEqual(self.comment.like_set.count(), 1)

        eliza = self.create_user('eliza')
        self.create_like(eliza, self.comment)
        self.assertEqual(self.comment.like_set.count(), 2)
