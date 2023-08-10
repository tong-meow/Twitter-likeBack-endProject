from accounts.models import UserProfile
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient
from testing.testcases import TestCase


LOGIN_URL = '/api/accounts/login/'
LOGOUT_URL = '/api/accounts/logout/'
SIGNUP_URL = '/api/accounts/signup/'
LOGIN_STATUS_URL = '/api/accounts/login_status/'
USER_PROFILE_DETAIL_URL = '/api/profiles/{}/'


class AccountApiTests(TestCase):

    def setUp(self):
        # every time 'test function' is executed, this function will be executed
        self.client = APIClient()
        self.user = self.create_user(
            username='admin',
            email='admin@twitter.com',
            password='correct password',
        )

    def test_login(self):
        # must be post instead of get
        response = self.client.get(LOGIN_URL, {
            'username': self.user.username,
            'password': 'correct password',
        })
        # if log in fails, http status code returns 405 = METHOD_NOT_ALLOWED
        self.assertEqual(response.status_code, 405)

        # wrong password
        response = self.client.post(LOGIN_URL, {
            'username': self.user.username,
            'password': 'wrong password',
        })
        self.assertEqual(response.status_code, 400)

        # check if logged in
        response = self.client.get(LOGIN_STATUS_URL)
        self.assertEqual(response.data['has_logged_in'], False)
        # use the correct password
        response = self.client.post(LOGIN_URL, {
            'username': self.user.username,
            'password': 'correct password',
        })
        self.assertEqual(response.status_code, 200)
        self.assertNotEqual(response.data['user'], None)
        self.assertEqual(response.data['user']['id'], self.user.id)
        # check if the user already logged in
        response = self.client.get(LOGIN_STATUS_URL)
        self.assertEqual(response.data['has_logged_in'], True)

    def test_logout(self):
        self.client.post(LOGIN_URL, {
            'username': self.user.username,
            'password': 'correct password',
        })
        # check if the user already logged in
        response = self.client.get(LOGIN_STATUS_URL)
        self.assertEqual(response.data['has_logged_in'], True)

        # must use post
        response = self.client.get(LOGOUT_URL)
        self.assertEqual(response.status_code, 405)

        # log out successfully
        response = self.client.post(LOGOUT_URL)
        self.assertEqual(response.status_code, 200)

        # check if the user already logged out
        response = self.client.get(LOGIN_STATUS_URL)
        self.assertEqual(response.data['has_logged_in'], False)

    def test_signup(self):
        data = {
            'username': 'someone',
            'email': 'someone@twitter.com',
            'password': 'any password',
        }

        response = self.client.get(SIGNUP_URL, data)
        self.assertEqual(response.status_code, 405)

        # test wrong e-mail
        response = self.client.post(SIGNUP_URL, {
            'username': 'someone',
            'email': 'not a correct email',
            'password': 'any password'
        })
        # print(response.data)
        self.assertEqual(response.status_code, 400)

        # test short password
        response = self.client.post(SIGNUP_URL, {
            'username': 'someone',
            'email': 'someone@twitter.com',
            'password': '123',
        })
        # print(response.data)
        self.assertEqual(response.status_code, 400)

        # test long user name
        response = self.client.post(SIGNUP_URL, {
            'username': 'username is tooooooooooooooooo loooooooong',
            'email': 'someone@twitter.com',
            'password': 'any password',
        })
        # print(response.data)
        self.assertEqual(response.status_code, 400)

        # register successfully
        response = self.client.post(SIGNUP_URL, data)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['user']['username'], 'someone')

        # check if user profile is made successfully
        created_user_id = response.data['user']['id']
        profile = UserProfile.objects.filter(user_id=created_user_id).first()
        self.assertNotEqual(profile, None)

        # check if logged in the user automatically
        response = self.client.get(LOGIN_STATUS_URL)
        self.assertEqual(response.data['has_logged_in'], True)


class UserProfileAPITests(TestCase):

    def test_update(self):
        jesse, jesse_client = self.create_user_and_client('jesse')
        p = jesse.profile
        p.nickname = 'old nickname'
        p.save()
        url = USER_PROFILE_DETAIL_URL.format(p.id)

        # test can only be updated by user himself.
        _, eliza_client = self.create_user_and_client('eliza')
        response = eliza_client.put(url, {
            'nickname': 'a new nickname',
        })
        self.assertEqual(response.status_code, 403)
        p.refresh_from_db()
        self.assertEqual(p.nickname, 'old nickname')

        # update nickname
        response = jesse_client.put(url, {
            'nickname': 'a new nickname',
        })
        self.assertEqual(response.status_code, 200)
        p.refresh_from_db()
        self.assertEqual(p.nickname, 'a new nickname')

        # update avatar
        response = jesse_client.put(url, {
            'avatar': SimpleUploadedFile(
                name='my-avatar.jpg',
                content=str.encode('a fake image'),
                content_type='image/jpeg',
            ),
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual('my-avatar' in response.data['avatar'], True)
        p.refresh_from_db()
        self.assertIsNotNone(p.avatar)