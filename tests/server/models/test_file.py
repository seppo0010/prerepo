from unittest import TestCase

import redis

from prerepo.server.models import File

from tests.shared.models.test_file import BaseTestFile


class TestFile(BaseTestFile, TestCase):
    def setUp(self):
        self.redis = redis.Redis(host='localhost', port=16379)
        self.uid = 'myuid'
        self.f = File(uid=self.uid)
        self.f.redis = self.redis
        self.redis.flushdb()
