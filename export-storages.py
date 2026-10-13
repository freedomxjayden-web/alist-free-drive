"""Export mount settings to a local private file for the Render environment variable."""
import argparse
import getpass
import json
import os
from urllib.parse import urlparse
from urllib.request import Request, urlopen

parser = argparse.ArgumentParser(description='Export AList storage settings without placing your password in shell history.')
parser.add_argument('url', help='Your Space HTTPS URL')
parser.add_argument('--output', default='storages.secret.json')
args = parser.parse_args()
base = args.url.rstrip('/')
u = urlparse(base)
if not ((u.scheme == 'https' and u.hostname and u.hostname.endswith('.onrender.com')) or
        (u.scheme == 'http' and u.hostname in {'localhost', '127.0.0.1'})) or u.username or u.password or u.query or u.fragment or u.path not in {'', '/'}:
    parser.error('Use your https://NAME.onrender.com origin or a localhost development origin.')

def api(path, payload=None, token=None):
    headers = {'Content-Type': 'application/json'}
    if token:
        headers['Authorization'] = token
    req = Request(base + '/api/' + path, data=json.dumps(payload).encode() if payload is not None else None, headers=headers)
    with urlopen(req, timeout=30) as response:
        data = json.load(response)
    if data.get('code') != 200:
        raise RuntimeError('AList request failed; check login and administrator permissions.')
    return data['data']

password = getpass.getpass('AList admin password: ')
token = api('auth/login', {'username': 'admin', 'password': password})['token']
del password
storages = []
page = 1
while True:
    result = api(f'admin/storage/list?page={page}&per_page=100', token=token)
    storages.extend(result['content'])
    if len(storages) >= result['total'] or not result['content']:
        break
    page += 1
cleaned = [{k: v for k, v in item.items() if k not in {'id', 'status', 'modified', 'order'}} for item in storages]
fd = os.open(args.output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
with os.fdopen(fd, 'w') as output:
    json.dump(cleaned, output, ensure_ascii=False, separators=(',', ':'))
print(f'Exported {len(cleaned)} mount(s) to {args.output}. Paste its contents into the ALIST_STORAGES_JSON secret environment variable. Do not upload this file to the Git repository.')
