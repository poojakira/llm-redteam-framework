import asyncio

from redteam.api.body_limit import RequestBodyLimit
from redteam.live.endpoint_scanner import _NoRedirect


def test_chunked_overflow_is_rejected_before_app():
    reached = []
    output = []
    chunks = iter([{'type': 'http.request', 'body': b'ab', 'more_body': True},
                   {'type': 'http.request', 'body': b'cd', 'more_body': False}])

    async def app(scope, receive, send):
        reached.append(True)

    async def receive():
        return next(chunks)

    async def send(message):
        output.append(message)

    asyncio.run(RequestBodyLimit(app, 3)({'type': 'http'}, receive, send))
    assert not reached
    assert output[0]['status'] == 413


def test_credentialed_endpoint_redirect_is_rejected():
    import pytest

    with pytest.raises(ValueError, match='redirects'):
        _NoRedirect().redirect_request(None, None, 307, '', {}, 'http://127.0.0.1')
