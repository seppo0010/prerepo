import logging
from unittest import TestCase
import threading

import redis

from prerepo.client.models import File
from prerepo.server.main import app

from tests.shared.models.test_file import BaseTestFile

logging.disable(logging.INFO)

appthread = None


class TestFile(BaseTestFile, TestCase):
    def setUp(self):
        global appthread
        self.redis = redis.Redis(host='localhost', port=16379)
        self.uid = 'myuid'
        self.f = File(uid=self.uid, server='http://localhost:5001/')
        self.f.redis = self.redis
        self.redis.flushdb()
        if appthread is None:
            def runserver():
                app.config.update({'redis': {'host': 'localhost',
                        'port': 16379}})
                self.app = app.run(port=5001, debug=True, use_reloader=False)

            appthread = threading.Thread(target=runserver)
            appthread.daemon = True
            appthread.start()
