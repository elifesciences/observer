from django.test import Client
from .base import BaseCase

class One(BaseCase):
    def setUp(self):
        self.c = Client()

    def test_landing_page(self):
        resp = self.c.get("/")
        self.assertEqual(resp.status_code, 200)
