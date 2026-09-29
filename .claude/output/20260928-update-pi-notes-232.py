"""Mark the two live Pi notes with the 2.32 deployment boundary."""
import json
from pathlib import Path
from urllib.request import Request, urlopen

base = 'http://100.65.188.9:8792'
secret = (Path.home() / '.config/csync/mesh.token').read_text().strip()
ids = ('507509ca-bcf5-423d-830e-36be58e8bf62',
       '058033af-9bd2-4ab1-a3c4-a2953b6a6a5c')


def request(path, method='GET', body=None):
    data = json.dumps(body).encode() if body is not None else None
    headers = {'X-Csync-Token': secret}
    if data is not None:
        headers['Content-Type'] = 'application/json'
    with urlopen(Request(base + path, data=data, headers=headers, method=method), timeout=20) as response:
        return json.load(response)


notes = [request('/v1/notes/' + ident)['note'] for ident in ids]
if [note['revision'] for note in notes] != [22, 18]:
    raise RuntimeError('Pi notes changed; inspect before editing')

updates = (
    ('## Current APK deployment — 28 Sep 2026\n\n'
     '**Pi now serves csync 2.32 (versionCode 34).** The Android source was built with '
     '`assembleDebug --offline`; package metadata reports `com.csync.hub`, 2.32/code34. '
     'The Pi update endpoint returned the exact 5,904,339-byte APK with SHA-256 '
     '`65d0a585be8932fdcbf96978996de231b07923c2443832f338c2d066fe0fd830`. '
     'The prior 2.31 APK was backed up on the Pi. At the owner’s request, further '
     'feature and visual testing stopped before installing 2.32 through the app. '
     'The earlier 2.30→2.31 in-app update succeeded on the emulator; 2.31→2.32 and '
     'a physical phone remain unchecked. The screenshots attached to this note '
     'document earlier emulator checkpoints, including Home, Search, Notes, Tools, '
     'Media, Chat, and sharing. Do not treat them as 2.32 screenshots.\n\n'),
    ('## Current APK to try — 28 Sep 2026\n\n'
     'More → Tools → **Update csync from Pi** now offers 2.32/code34. The Pi serves '
     'the built APK (SHA-256 `65d0a585be8932fdcbf96978996de231b07923c2443832f338c2d066fe0fd830`). '
     'The earlier 2.30→2.31 in-app update succeeded on the emulator. At the owner’s '
     'request, further feature and visual testing stopped, so installation of 2.32 '
     'through the app and use on a physical phone are unconfirmed. The activities '
     'below are things to try, not promises that every 2.32 route passed.\n\n'),
)

for ident, note, preface in zip(ids, notes, updates):
    saved = request('/v1/notes/' + ident, 'PUT', {
        'title': note['title'],
        'body': preface + note['body'],
        'expectedRevision': note['revision'],
    })['note']
    print(ident, saved['revision'])
