"""Check that a running Redroom Maps deployment answers as expected.

Usage:
    python scripts/smoke_test.py
    python scripts/smoke_test.py --base-url https://example.com
"""

import argparse
import json
import sys
import time
import urllib.error
import urllib.request


CHECKS = [
    ('GET', '/ping', 200, None),
    ('GET', '/map/version', 200, None),
    ('GET', '/data/version', 200, None),
    ('GET', '/map/colors', 200, 'json'),
    ('GET', '/country/all', 200, 'json'),
    ('GET', '/tag/all', 200, 'json'),
    ('GET', '/video/years?begin=1800&end=1900', 200, 'json'),
    ('GET', '/map/geometry/2025', 200, None),
    ('GET', '/map/geometry/-3000', 200, None),
    ('GET', '/map/world/2025', 200, None),
]


def check(base_url: str, method: str, path: str, expected: int, kind):
    url = f'{base_url}{path}'
    request = urllib.request.Request(url, method=method)
    request.add_header('Accept', 'application/json, text/plain, */*')
    started = time.perf_counter()

    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            status = response.status
            body = b'' if method == 'HEAD' else response.read()
    except urllib.error.HTTPError as error:
        status = error.code
        body = error.read()
    except Exception as error:  # noqa: BLE001 - report any network failure
        return False, f'{method} {path}: {error.__class__.__name__}: {error}'

    elapsed_ms = (time.perf_counter() - started) * 1000

    if status != expected:
        return False, f'{method} {path}: expected {expected}, got {status}'

    if kind == 'json' and body:
        try:
            json.loads(body)
        except json.JSONDecodeError as error:
            return False, f'{method} {path}: invalid JSON ({error})'

    if path in ('/map/version', '/data/version') and not body.strip():
        return False, f'{method} {path}: empty version'

    return True, f'{method} {path}: {status} in {elapsed_ms:.0f} ms'


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        '--base-url',
        default='http://127.0.0.1:8080',
        help='site origin without a trailing slash',
    )
    args = parser.parse_args()
    base_url = args.base_url.rstrip('/')

    failures = 0

    for method, path, expected, kind in CHECKS:
        ok, message = check(base_url, method, path, expected, kind)
        print(('PASS ' if ok else 'FAIL ') + message)

        if not ok:
            failures += 1

    print(f'\n{failures} failure(s)' if failures else '\nAll checks passed')
    return 1 if failures else 0


if __name__ == '__main__':
    sys.exit(main())
