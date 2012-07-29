import hashlib

import requests

from prerepo.shared.exceptions import NotFoundException


class File(object):
    def __init__(self, uid=None, server=None, *args, **kwargs):
        super(File, self).__init__(*args, **kwargs)
        self.uid = str(uid)
        self.server = server or 'http://localhost:5000/'

    def get_url(self, path):
        if path[:1] == '/':
            path = path[1:]
        return self.server + 'api/' + self.uid + '/' + path

    def hashdata(self, data):
        return hashlib.md5(data).hexdigest()

    def response(self, r):
        return r.json['data'], r.headers['ETag'], r.json['isfile']

    def get(self, path):
        r = requests.get(self.get_url(path))
        if r.status_code == 404:
            raise NotFoundException()
        return self.response(r)

    def createfile(self, path, data):
        r = requests.post(self.get_url(path), data={'data': data, 'isfile': 1})
        return self.response(r)

    def createdir(self, path):
        requests.post(self.get_url(path))

    def rename(self, path, target):
        r = requests.put(self.get_url(path), data={'target': target})
        return self.response(r)

    def delete(self, path):
        r = requests.delete(self.get_url(path))
        return r.json

    def gethash(self, path):
        r = requests.head(self.get_url(path))
        return r.headers.get('ETag', None)
