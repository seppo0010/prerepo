import sys
from uuid import uuid1

from flask import Flask, render_template, redirect, url_for, request

from prerepo.server.serialize import serialize
from prerepo.server.models import File
from prerepo.server.exceptions import NotFoundException

app = Flask(__name__)


def render(uid):
    return render_template('index.html', uid=uid)


@app.route('/<uid>')
def index_hash(uid=None):
    if ':' in uid:
        return '', 400
    return render(uid)


@app.route('/')
def index():
    return redirect(url_for('index_hash', uid=str(uuid1())))


def resource_response(data, md5, mime, isfile):
    return {'response': {'data': data, 'isfile': isfile, 'mime': mime},
        'headers': {'Content-MD5': md5, 'ETag': md5}}


@app.route('/api/<uid>/<path:path>', methods=('GET', 'POST', 'PUT', 'DELETE',
            'HEAD'))
def api(path=None, uid=None):
    try:
        response = {}
        f = File(uid=uid, redisconf=app.config.get('redis', {}))
        path = '/' + path
        if request.method == 'GET':
            # TODO check for If-None-Match
            response = resource_response(*f.get(path))
        elif request.method == 'POST':
            if request.form.get('isfile', False):
                data = request.form.get('data', '').encode('utf8')
                r = f.createfile(path, data)
                response = resource_response(*r)
            else:
                f.createdir(path)
        elif request.method == 'PUT':  # renaming
            response = f.rename(path, request.form.get('target'))
            response = resource_response(*response)
        elif request.method == 'DELETE':
            response = f.delete(path)
            response = {'response': response}
        elif request.method == 'HEAD':
            md5 = f.gethash(path)
            response = {'response': None, 'status': 204,
                'headers': {'Content-MD5': md5, 'ETag': md5}}
        return serialize(response)
    except NotFoundException:
        return '', 404

if __name__ == '__main__':
    app.run(debug='DEBUG' in sys.argv)
