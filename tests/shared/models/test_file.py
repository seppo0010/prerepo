class BaseTestFile(object):
    def test_create_file(self):
        path = '/hello world'
        data = 'my hello world'
        self.assertIs(self.redis.get(':'.join((self.uid, path))), None)
        self.f.createfile(path, data)
        self.assertEqual(self.redis.get(':'.join((self.uid, path, 'content'))),
                data)
        self.assertEqual(self.redis.get(':'.join((self.uid, path, 'type'))),
                'f')

    def test_create_dir(self):
        path = '/hello world/test'
        self.assertIs(self.redis.get(':'.join((self.uid, path))), None)
        self.f.createdir(path)
        self.assertEqual(self.redis.get(':'.join((self.uid, path, 'type'))),
                'd')
        self.assertIn('hello world', self.redis.smembers(':'.join((self.uid,
                            '/', 'content'))))
        self.assertEqual(len(self.redis.smembers(':'.join((self.uid,
                                '/hello world', 'content')))), 1)

    def test_list_dir(self):
        files = ('hello', 'world', 'this', 'is', 'a', 'test')
        for f in files:
            self.f.createfile('/' + f, '')
        self.assertEqual(self.redis.smembers(':'.join((self.uid, '/',
                            'content'))), set(files))
        self.assertEqual(self.redis.get(':'.join((self.uid, '/', 'type'))),
                'd')
        self.assertIsNot(self.redis.get(':'.join((self.uid, '/', 'hash'))),
                None)

    def test_get_file(self):
        path = '/hello world'
        data = 'my hello world'
        h = 'fake'
        self.redis.set(':'.join((self.uid, path, 'hash')), h)
        self.redis.set(':'.join((self.uid, path, 'type')), 'f')
        self.redis.set(':'.join((self.uid, path, 'content')), data)
        self.redis.set(':'.join((self.uid, path, 'mime')), 'text/plain')
        self.assertEqual(self.f.get(path), (data, h, 'text/plain', True))

    def test_rename(self):
        src, target = '/hello world', '/hello'
        data = 'my hello world'
        h = 'fake'
        self.redis.set(':'.join((self.uid, src, 'hash')), h)
        self.redis.set(':'.join((self.uid, src, 'type')), 'f')
        self.redis.set(':'.join((self.uid, src, 'content')), data)
        self.f.rename(src, target)
        self.assertEqual(self.redis.get(':'.join((self.uid, target, 'hash'))),
                h)
        self.assertEqual(self.redis.get(':'.join((self.uid, target, 'type'))),
                'f')
        self.assertEqual(self.redis.get(':'.join((self.uid, target, 'content'))
                                       ), data)
        self.assertIs(self.redis.get(':'.join((self.uid, src, 'hash'))), None)
        self.assertIs(self.redis.get(':'.join((self.uid, src, 'type'))), None)
        self.assertIs(self.redis.get(':'.join((self.uid, src))), None)

    def test_delete_file(self):
        path = '/hello world'
        data = 'my hello world'
        h = 'fake'
        self.redis.set(':'.join((self.uid, path, 'hash')), h)
        self.redis.set(':'.join((self.uid, path, 'type')), 'f')
        self.redis.set(':'.join((self.uid, path, 'content')), data)
        self.f.delete(path)
        self.assertIs(self.redis.get(':'.join((self.uid, path, 'hash'))), None)
        self.assertIs(self.redis.get(':'.join((self.uid, path, 'type'))), None)
        self.assertIs(self.redis.get(':'.join((self.uid, path, 'content'))),
                None)

    def test_get_hash(self):
        path = '/hello world'
        data = 'my hello world'
        h = 'fake'
        self.redis.set(':'.join((self.uid, path, 'hash')), h)
        self.redis.set(':'.join((self.uid, path, 'type')), 'f')
        self.redis.set(':'.join((self.uid, path)), data)
        self.assertEqual(self.f.gethash(path), h)

    def test_list_files(self):
        files = ('hello', 'world', 'this', 'is', 'a', 'test')
        for f in files:
            self.f.createfile('/' + f, '')
        self.assertEqual(set(self.f.get('/')[0]), set(files))
