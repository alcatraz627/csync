"""Clarify time-bound release and Pi power wording in the two live notes."""
import json
from pathlib import Path
from urllib.request import Request, urlopen

base = 'http://100.65.188.9:8792'
secret = (Path.home()/'.config/csync/mesh.token').read_text().strip()
ids = ('507509ca-bcf5-423d-830e-36be58e8bf62',
       '058033af-9bd2-4ab1-a3c4-a2953b6a6a5c')

def request(path, method='GET', body=None):
    data = json.dumps(body).encode() if body is not None else None
    headers = {'X-Csync-Token': secret}
    if data is not None: headers['Content-Type'] = 'application/json'
    with urlopen(Request(base+path, data=data, headers=headers, method=method), timeout=20) as response:
        return json.load(response)

notes = [request('/v1/notes/'+id)['note'] for id in ids]
if [n['revision'] for n in notes] != [21,17]:
    raise RuntimeError('Pi note revisions changed; inspect before editing')
replacements = [(
    ('The 2.30→2.31 in-app installer run is pending the shared emulator handoff; the physical phone remains unchecked.',
     'At staging time, the 2.30→2.31 in-app run was pending; the completed emulator result is recorded below. The physical phone remains unchecked.'),
    ('it currently reports an observed Pi undervoltage warning.',
     'at the 10:07 IST check it reported a Pi undervoltage warning.'),
),(
    ('The Pi currently reports undervoltage in Tools.',
     'At the 10:07 IST check, the Pi reported undervoltage in Tools.'),
)]
for id,note,changes in zip(ids,notes,replacements):
    body=note['body']
    for old,new in changes:
        if body.count(old)!=1: raise RuntimeError('Wording changed; inspect note '+id)
        body=body.replace(old,new,1)
    saved=request('/v1/notes/'+id,'PUT',{'title':note['title'],'body':body,
                                      'expectedRevision':note['revision']})['note']
    print(id,saved['revision'])
