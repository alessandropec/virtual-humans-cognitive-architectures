"""Every relative frontend module must be served as JavaScript."""
import re
import sys
from pathlib import Path
from urllib.parse import urljoin
from fastapi.testclient import TestClient
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'app'))
import server
client = TestClient(server.app)
pending = ['/app.js']
seen = set()
while pending:
    url = pending.pop()
    if url in seen:
        continue
    seen.add(url)
    response = client.get(url)
    assert response.status_code == 200, (url, response.status_code)
    assert 'javascript' in response.headers['content-type'], (url, response.headers)
    for relative in re.findall(r"from\s+['\"]([^'\"]+)['\"]", response.text):
        if relative.startswith('.'):
            pending.append(urljoin(url, relative))
print(f'PASS {len(seen)} frontend modules served as JavaScript')
