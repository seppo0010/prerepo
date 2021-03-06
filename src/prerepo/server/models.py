import hashlib
import os
import redis

import magic

from .exceptions import NotFoundException


class File(object):
    def __init__(self, uid=None, redisconf=None, *args, **kwargs):
        super(File, self).__init__(*args, **kwargs)
        self.uid = uid
        self.redis = redis.Redis(**(redisconf or {}))

    def get_key_type(self, path):
        return self.uid + ':' + path + ':type'

    def get_key(self, path):
        return self.uid + ':' + path + ':content'

    def get_hash_key(self, path):
        return self.uid + ':' + path + ':hash'

    def get_mime_key(self, path):
        return self.uid + ':' + path + ':mime'

    def hashdata(self, data):
        return hashlib.md5(data).hexdigest()

    def get(self, path):
        t = self.redis.get(self.get_key_type(path))
        if t is None:
            raise NotFoundException()

        if t == 'f':
            with self.redis.pipeline(transaction=False) as pipe:
                pipe.get(self.get_key(path))
                pipe.get(self.get_hash_key(path))
                pipe.get(self.get_mime_key(path))
                data, h, m = pipe.execute()
        else:
            with self.redis.pipeline(transaction=False) as pipe:
                pipe.smembers(self.get_key(path))
                pipe.get(self.get_hash_key(path))
                elements, h = pipe.execute()

            m = 'directory'
            elements = list(elements)
            with self.redis.pipeline(transaction=False) as pipe:
                for e in elements:
                    pipe.get(self.get_mime_key(os.path.join(path, e)))
                    pipe.get(self.get_hash_key(os.path.join(path, e)))
                response = list(pipe.execute())

            data = []
            for e in elements:
                obj = {'name': e}
                obj['mime'] = response.pop(0)
                obj['hash'] = response.pop(0)
                data.append(obj)
        return data, h, m, t == 'f'

    def gethash(self, path):
        return self.redis.get(self.get_hash_key(path))

    def createfile(self, path, data):
        hashdata = self.hashdata(data)
        m = self.get_mime_key(path)
        if self.gethash(path) != hashdata:
            k, h, t = (self.get_key(path), self.get_hash_key(path),
                    self.get_key_type(path))
            parent, filename = os.path.dirname(path), os.path.basename(path)
            self.createdir(parent)

            with magic.Magic(flags=magic.MAGIC_MIME_TYPE) as mag:
                mime = mag.id_buffer(data)

            with self.redis.pipeline(transaction=True) as pipe:
                while 1:
                    try:
                        pipe.watch(k, h, t)
                        pipe.multi()
                        pipe.sadd(self.get_key(parent), filename)
                        pipe.set(k, data)
                        pipe.set(h, hashdata)
                        pipe.set(t, 'f')
                        pipe.set(m, mime)
                        pipe.execute()
                        break
                    except redis.WatchError:
                        continue
        else:
            mime = self.redis.get(m)
        return data, hashdata, mime, True

    def createdir(self, path):
        while 1:
            parent = os.path.dirname(path)
            basename = os.path.basename(path)
            parent_key = self.get_key(parent)
            path_type = self.get_key_type(path)
            parent_hash = self.get_hash_key(parent)
            with self.redis.pipeline(transaction=True) as pipe:
                while 1:
                    try:
                        pipe.watch(parent_key, path_type)
                        pipe.multi()
                        if basename != '':
                            pipe.sadd(parent_key, basename)
                        pipe.set(path_type, 'd')
                        pipe.execute()
                        break
                    except redis.WatchError:
                        continue

            with self.redis.pipeline(transaction=True) as pipe:
                while 1:
                    try:
                        pipe.watch(parent_hash)
                        members = pipe.smembers(parent_key)
                        pipe.multi()
                        pipe.set(parent_hash, self.hashdata('/'.join(members)))
                        pipe.execute()
                        break
                    except redis.WatchError:
                        continue

            if path == '/':
                break

            path = parent

    def rename(self, source, target):
        k, h, t = (self.get_key(source), self.get_hash_key(source),
                self.get_key_type(source))
        k2, h2, t2 = (self.get_key(target), self.get_hash_key(target),
                self.get_key_type(target))
        with self.redis.pipeline(transaction=True) as pipe:
            while 1:
                try:
                    pipe.watch(k, k2, h, h2, t, t2)
                    pipe.multi()
                    pipe.rename(k, k2)
                    pipe.rename(h, h2)
                    pipe.rename(t, t2)
                    pipe.execute()
                    break
                except redis.WatchError:
                    continue
        return self.get(target)

    def delete(self, path):
        k, h, t = (self.get_key(path), self.get_hash_key(path),
                self.get_key_type(path))
        with self.redis.pipeline(transaction=True) as pipe:
            while 1:
                try:
                    pipe.watch(k, h, t)
                    pipe.multi()
                    pipe.delete(k, h, t)
                    response = pipe.execute()
                    break
                except redis.WatchError:
                    continue
        return response[0] == '1'
