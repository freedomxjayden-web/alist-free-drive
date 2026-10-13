"""AList on an ephemeral Render web service. Credentials only come from runtime Secrets."""
import json
import os
from pathlib import Path
import signal
import sqlite3
import subprocess
import sys
import time
from urllib.request import Request, urlopen


def api(port, path, method='GET', payload=None, token=None):
    headers = {'Content-Type': 'application/json'}
    if token:
        headers['Authorization'] = token
    request = Request(f'http://127.0.0.1:{port}/api/{path}',
                      data=json.dumps(payload).encode() if payload is not None else None,
                      headers=headers, method=method)
    with urlopen(request, timeout=20) as response:
        result = json.load(response)
    if result.get('code') != 200:
        # Do not echo driver responses: they can contain OAuth credentials.
        raise RuntimeError(f'AList API failed: {path}')
    return result.get('data')


def prepare(binary, data_dir, password, port, address):
    data_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    subprocess.run([binary, 'admin', 'set', password, '--data', str(data_dir)],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    config_file = data_dir / 'config.json'
    config = json.loads(config_file.read_text())
    config['scheme']['address'] = address
    config['scheme']['http_port'] = port
    config['scheme']['https_port'] = -1
    config['tls_insecure_skip_verify'] = False
    config['max_concurrency'] = 8
    config['log']['enable'] = False
    config['site_url'] = os.environ.get('ALIST_SITE_URL', '')
    config_file.write_text(json.dumps(config, indent=2))
    config_file.chmod(0o600)
    table = config['database'].get('table_prefix', 'x_') + 'users'
    if table != 'x_users':
        raise RuntimeError('Unexpected database schema')
    with sqlite3.connect(config['database']['db_file']) as connection:
        # Only the administrator can log in on a newly provisioned Space.
        connection.execute("UPDATE x_users SET disabled = CASE WHEN username = 'admin' THEN 0 ELSE 1 END")
        connection.commit()
    return config


def restore_storages(port, password, storages):
    login = api(port, 'auth/login', 'POST', {'username': 'admin', 'password': password})
    token = login['token']
    existing = set()
    page = 1
    while True:
        current = api(port, f'admin/storage/list?page={page}&per_page=100', token=token)
        existing.update(storage['mount_path'] for storage in current['content'])
        if page * 100 >= current['total'] or not current['content']:
            break
        page += 1
    for storage in storages:
        if storage['mount_path'] in existing:
            continue
        cleaned = {key: value for key, value in storage.items()
                   if key not in {'id', 'status', 'modified', 'order'} }
        api(port, 'admin/storage/create', 'POST', cleaned, token)


def main():
    password = os.environ.pop('ALIST_ADMIN_PASSWORD', '')
    if len(password) < 16:
        raise RuntimeError('Add a Secret named ALIST_ADMIN_PASSWORD with at least 16 characters in Render Environment.')
    raw_storages = os.environ.pop('ALIST_STORAGES_JSON', '[]')
    storages = json.loads(raw_storages)
    if not isinstance(storages, list) or any(not isinstance(item, dict) or
            not isinstance(item.get('mount_path'), str) or not item.get('driver') for item in storages):
        raise RuntimeError('ALIST_STORAGES_JSON must be an array of AList storage configurations.')
    port = int(os.environ.get('ALIST_PORT', os.environ.get('PORT', '10000')))
    binary = os.environ.get('ALIST_BINARY', '/usr/local/bin/alist')
    data_dir = Path(os.environ.get('ALIST_DATA_DIR', '/tmp/alist-space')).resolve()
    prepare(binary, data_dir, password, port, os.environ.get('ALIST_BIND', '0.0.0.0'))
    process = subprocess.Popen([binary, 'server', '--data', str(data_dir)])
    def stop(signum, frame):
        process.terminate()
    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    try:
        for attempt in range(60):
            if process.poll() is not None:
                raise RuntimeError('AList exited before startup completed.')
            try:
                api(port, 'public/settings')
                break
            except Exception:
                time.sleep(0.5)
        else:
            raise RuntimeError('AList startup timed out.')
        restore_storages(port, password, storages)
        del password
        print('AList ready. Guest access disabled. Storage configuration restored.', flush=True)
        return process.wait()
    finally:
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()


if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception as error:
        # Never print secrets, full request bodies, or credential-bearing URLs.
        if isinstance(error, RuntimeError):
            print(f'Startup failed: {error}', file=sys.stderr)
        elif isinstance(error, json.JSONDecodeError):
            print('Startup failed: ALIST_STORAGES_JSON is not valid JSON.', file=sys.stderr)
        else:
            print(f'Startup failed ({type(error).__name__}). Check runtime Secrets and storage settings.', file=sys.stderr)
        sys.exit(1)
