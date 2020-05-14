from django.test import TestCase
from django.contrib import auth
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status

CREATE_USER_URL = reverse('users:create')

def create_user(**kwargs):
    return auth.get_user_model().objects.create_user(**kwargs)



class PublicUserApiTest(TestCase):

    def setUp(self) -> None:
        self.client = APIClient()

    def test_create_user_success(self):
        """Test creating user with valid payload is successful"""
        payload = {
            'email': 'test@example.com',
            'password': 'pwd1234',
            'name': 'Test Example'
        }
        res = self.client.post(CREATE_USER_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        user = auth.get_user_model().objects.get(**res.data)
        self.assertTrue(user.check_password(payload['password']))
        self.assertNotIn('password', res.data)

    def test_user_exists(self):
        """Test creating a user that already exists fails"""
        payload = {
            'email': 'test@example.com',
            'password': 'pwd1234',
            'name': 'Test Example'
        }
        create_user(**payload)

        res = self.client.post(CREATE_USER_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_too_short(self):
        """Test that password must be more than 5 characters long"""
        payload = {
            'email': 'test@example.com',
            'password': 'pass',
            'name': 'Test Example'
        }

        res = self.client.post(CREATE_USER_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        user_exists = auth.get_user_model().objects.filter(
            email=payload['email']
        ).exists()
        self.assertFalse(user_exists)
