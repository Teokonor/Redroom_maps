from hashlib import sha256

from fastapi import Request, Response

from ..database import Database


def _etag_matches(header: str | None, etag: str) -> bool:
    if not header:
        return False

    for item in header.split(','):
        value = item.strip()
        if value == '*' or value == etag or value == f'W/{etag}':
            return True

    return False


def cached_json(
    request: Request,
    response: Response,
    *,
    key: str,
    version: str | None,
) -> Response | None:
    """Set JSON cache headers and return 304 when the client has the same data.

    A versioned request (``?v=<data_version>``) is immutable until the database
    changes. Requests without a version are revalidated with an ETag, which lets
    us return 304 before running the database query.
    """
    current_version = Database.data_version()
    key_hash = sha256(key.encode('utf-8')).hexdigest()[:16]
    etag = f'"{current_version}-{key_hash}"'

    if version == current_version:
        headers = {
            'Cache-Control': 'public, max-age=31536000, immutable',
            'ETag': etag,
        }
    else:
        headers = {
            'Cache-Control': 'no-cache',
            'ETag': etag,
        }

    if _etag_matches(request.headers.get('if-none-match'), etag):
        return Response(
            status_code=304,
            headers={
                **headers,
                'Vary': 'Accept-Encoding',
            },
        )

    for name, value in headers.items():
        response.headers[name] = value

    return None
