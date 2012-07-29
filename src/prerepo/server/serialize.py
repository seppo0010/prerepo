import json

from flask import make_response


def serialize(data, *args, **kwargs):
    response = make_response(json.dumps(data.get('response', None)),
            data.get('status'))
    for k, v in data.get('headers', {}).iteritems():
        response.headers[k] = v
    return response
