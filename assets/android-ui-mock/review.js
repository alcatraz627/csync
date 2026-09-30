// The review page around the phone: the map, the states, the facts about the
// current screen, and the wall of every screen. None of this is part of the app.

const STATES = [
  ['Playing on Pi screen', s => Boolean(s.sessions['Pi screen']), s => toggleSession(s, 'Pi screen', 'A Matter of Life and Death', 3120, 6240, 'Elements')],
  ['Playing on this phone', s => Boolean(s.sessions['This phone']), s => toggleSession(s, 'This phone', "Blackadder's Christmas Carol", 610, 2580, 'Pi USB')],
  ['Pi offline', s => s.pi === 'offline', s => { s.pi = s.pi === 'offline' ? 'online' : 'offline'; }],
  ['Checking the Pi', s => s.pi === 'checking', s => { s.pi = s.pi === 'checking' ? 'online' : 'checking'; }],
  ['Power is low', s => s.power === 'low', s => { s.power = s.power === 'low' ? 'ok' : 'low'; }],
  ['Drive missing', s => s.drive !== 'ok', s => { s.drive = s.drive === 'ok' ? 'missing' : 'ok'; }],
  ['Sending fails', s => s.sendFails, s => { s.sendFails = !s.sendFails; }],
  ['Recipient offline', s => s.recipient === 'work-macbook', s => { s.recipient = s.recipient === 'work-macbook' ? 'studio-mac' : 'work-macbook'; }],
  ['Camera connecting', s => s.camera === 'connecting', s => { s.camera = s.camera === 'connecting' ? 'live' : 'connecting'; }],
  ['Shizuku running', s => s.shizuku, s => { s.shizuku = !s.shizuku; }],
  ['No update waiting', s => !s.update, s => { s.update = !s.update; }],
  ['Clipboard holds an image', s => s.clip.kind === 'Image', s => { s.clip = s.clip.kind === 'Image' ? { kind: 'Text', sub: 'Text, 46 characters', body: 'HDMI 2 is the Pi. HDMI 1 is the laptop dock.' } : { kind: 'Image', sub: 'Image, 1.2 MB', body: '' }; }],
  ['Android media notification', s => s.shade, s => { s.shade = !s.shade; }]
];

const sampleSession = (output, title, at, total, source) => ({ title, source, at, total, paused: false, busy: false, error: '', volume: output === 'Pi screen' ? 0 : 35, speed: 1, rotate: 0, loop: 'Off', favorite: false, skip: 10, pending: {} });
function toggleSession(s, output, title, at, total, source) {
  s.sessions[output] = s.sessions[output] ? null : sampleSession(output, title, at, total, source);
}

// Sheets that can be opened from each place, for the rail and the wall.
const PLACE_SHEETS = {
  home: ['resume|0', 'device|Raspberry Pi', 'device|work-macbook'],
  search: [],
  media: ['item|Walk in the hills', 'item|Desk at sunset', 'item|Projector manual', 'folder|Films', 'details|Walk in the hills', 'view|image|Desk at sunset', 'to-device|video|Walk in the hills', 'to-chat|video|Walk in the hills', 'to-note|video|Walk in the hills', 'share-out|Walk in the hills', 'source', 'resume|1'],
  'pi-screen': ['youtube', 'cast|screen', 'cast|app', 'slideshow', 'show-note', 'volume|Pi screen', 'speed|Pi screen', 'skip|Pi screen', 'move|Pi screen', 'replace|Pi screen|Walk in the hills'],
  'phone-player': ['move|This phone'],
  covers: [],
  share: ['recipient', 'attach', 'clipboard', 'sent|0'],
  received: ['received|0', 'received|1', 'received|2'],
  incoming: ['to-device|link|F-Droid 2.0, the biggest update in years'],
  chat: ['model|default'],
  conversation: ['chat-add', 'model|chat', 'export-chat', 'fork|2', 'result|2|1', 'result|2|0', 'result|4|0'],
  more: [], camera: [],
  captures: ['capture|c1', 'capture|c2', 'delete-capture|c1'],
  notes: [], note: ['share-note', 'note-item|0', 'note-add', 'drop-note-item|0', 'delete-note'], pin: ['share-pin', 'delete-pin'],
  tools: ['power', 'service|media', 'update'],
  process: ['app|Chrome', 'stop-app|Chrome'],
  widgets: ['widget|xkcd', 'widget|Media remote', 'widget|Send to Pi screen'], settings: [], connection: ['device|studio-mac', 'forget|studio-mac'],
  playback: ['start-volume', 'skip|default'],
  assistant: ['model|default'],
  appearance: ['custom'], guide: ['tools'], help: [], showcase: []
};
const NEEDS_SESSION = { 'pi-screen': 'Pi screen', 'phone-player': 'This phone' };

const sheetName = spec => {
  const [type, ...rest] = spec.split('|');
  const names = { item: 'Item', folder: 'Folder', details: 'File details', source: 'Choose a source', resume: 'Resume', device: 'Device', recipient: 'Send to', attach: 'Attach a file', clipboard: 'Clipboard', sent: 'A sent item', received: 'A received item', 'to-chat': 'Send to a conversation', youtube: 'YouTube link', volume: 'Volume', speed: 'Speed', skip: 'Skip length', move: 'Move output', replace: 'Replace playback', 'chat-add': 'Add to message', model: 'Model and thinking', fork: 'Fork', result: 'Assistant result', capture: 'Capture', 'delete-capture': 'Delete capture', 'share-note': 'Send note', 'delete-note': 'Delete note', 'share-pin': 'Send pin', 'delete-pin': 'Delete pin', power: 'Power', service: 'Service', update: 'Update', app: 'App', 'stop-app': 'Stop app', 'start-volume': 'Starting volume', custom: 'Own colour', 'to-device': 'Send to a device', tools: 'Assistant tools', widget: 'Widget', forget: 'Forget device', view: 'Open an item', 'to-note': 'Add to a note', 'share-out': 'Android share menu', cast: 'Show this phone', slideshow: 'Slideshow', 'show-note': 'Show a note', 'export-chat': 'Save the conversation', 'note-item': 'Item in a note', 'note-add': 'Add to a note, from the note', 'drop-note-item': 'Take out of a note' };
  const detail = rest.filter(r => !/^\d+$/.test(r) && !['Pi screen', 'This phone', 'default', 'chat', 'video', 'image', 'link', 'text', 'doc', 'screen'].includes(r))[0];
  return names[type] + (detail ? `: ${detail}` : rest[0] && ['default', 'chat'].includes(rest[0]) ? `, ${rest[0]}` : '');
};

// What is different from build 2.34 on each place. Shown beside the phone.
const CHANGES = {
  home: ['No hero card. A plain line states how the Pi is (G-07, H-01, H-02).', 'The Media tile counts the same videos the Videos view lists.', 'Three sections that collapse: Pick up, Capabilities, Devices (H-07).', 'Capabilities, not "Do something" (H-04). Tiles that work come first (H-06).', 'Devices shows real names with the right icon. There is no fixed "Mac".', 'Resume names the output it plays on.'],
  search: ['Path reads Home / Search.', 'Notes and pins are searchable. Results open the item itself.'],
  media: ['A bar place: no Back arrow, no "Home /".', 'Every item offers the same actions here as in Received, Captures and incoming shares.', 'Search covers every kind of file and folder in the source.', 'Tapping a file opens one sheet with every action, and Play names its output.', 'Titles are readable names. The file name is in File details.', 'Search appears from the bar icon, so the list starts higher (M-14).', 'Folder rows carry a download button (M-09).'],
  'pi-screen': ['Pi display and the full player are one page.', 'When idle it shows the cover and the ways to play, never disabled controls.', 'Pause or Resume is the one filled control. Stop is red.', 'Rotate and Loop show "applying" for two seconds (P-08).'],
  covers: ['New. Thumbnails, a gradient ring on the chosen one, framing kept per image (C-02 to C-06).'],
  'phone-player': ['The same player as the Pi screen, for this phone.', 'Full screen is a mode of this page.'],
  share: ['The recipient row opens the device list, and so does the top bar icon (SH-11).', 'One Send button for text and attachment.', 'An offline recipient disables Send and says why.', 'A failed send keeps the attachment (SH-13).'],
  received: ['A child page of Share with its own path and Back.'],
  incoming: ['The same action list as everywhere else, chosen by the kind of item (N-09).', 'Playback options are editable before it starts (SH-08).', 'Back returns to the app you shared from.'],
  chat: ['A bar place: no Back arrow.', 'Tools uses the same names as the assistant guide.', 'Empty states say what belongs there.'],
  conversation: ['Favorite and Archive sit on the title row (CH-17).', 'Your messages use a tint, not a solid accent block.', 'Model and thinking need Save (CH-13).', 'Tap a message for Copy, Regenerate or Edit, and Fork, as one tight strip.', 'Each tool result is a card drawn for its kind, and a media card carries Pause and Stop.', 'One message box holds the text, attachments, the model and Send. It grows, and opens taller.', 'The top bar saves the conversation as Markdown or as an image.'],
  showcase: ['New. Every part the app is built from, drawn by the part itself.'],
  more: ['Notes lives here with the other places that are not in the bar.', 'Tools shows its state on the row.'],
  camera: ['Captures and Show on Pi screen are named rows under the shutter.', 'Connecting shows a moving placeholder, not an empty box.'],
  captures: ['Grouped by day. Title is the kind, the line under it is time and size.'],
  notes: ['Notes and Pins are two views of one place.', 'Dates instead of revision numbers.'],
  note: ['Rich edits the formatted note. Plain edits the Markdown. Both save the same note.', 'Share and Delete are icons in the top bar.'],
  pin: ['Link or text, title, tags and a reason (N-06).'],
  tools: ['The heading states the worst current state.', 'No planned features listed. No second door into Media.', 'The update is here, where the owner looks for it (PI-07).'],
  process: ['Without Shizuku the page says so and shows no empty tiles (T-06).', 'Stopping an app asks first (T-03).'],
  widgets: ['Each widget and tile opens a detail with Add or Remove (T-07).', 'Native shows a row only once that widget is built (T-06).'],
  settings: ['Four rows, each showing its current value.'],
  connection: ['Devices first, connection details after, Save at the end.', 'Plain names for the fields, each with one line of help.'],
  playback: ['New. Defaults that the player and incoming shares start from.'],
  assistant: ['Model and thinking are chosen in one sheet, the same one Chat uses.', 'A provider the Pi cannot run is visibly unavailable (SE-18).'],
  appearance: ['Colour circles only, with a check on the chosen one (SE-05, SE-17).', 'One segmented control style, the same as everywhere else.'],
  guide: ['Examples of what to ask, in the same words the app uses.'],
  help: ['Where things live, and the version.']
};

const reviewState = { wall: false, system: false };

function renderRail() {
  const depth = id => pathTo(id).length - 1;
  document.querySelector('#tree').innerHTML = PLACES.map(p => `<button type="button" class="d${depth(p.id)}${S.place === p.id ? ' on' : ''}" data-go="${p.id}">${icon(p.icon, 15)}${esc(p.label)}</button>`).join('');
  document.querySelector('#states').innerHTML = STATES.map(([name, isOn], i) => `<button type="button" class="${isOn(S) ? 'on' : ''}" data-state="${i}" aria-pressed="${isOn(S)}">${esc(name)}</button>`).join('');
  const sheets = PLACE_SHEETS[S.place] || [];
  document.querySelector('#sheets').innerHTML = sheets.length ? sheets.map(spec => `<button type="button" data-sheet="${esc(spec)}">${esc(sheetName(spec))}</button>`).join('') : '<span style="color:var(--dim);font-size:12.5px">This screen opens no sheet.</span>';
}

function renderInspector() {
  const p = PLACE[S.place], target = backTarget(S.place);
  const built = { yes: 'Built in 2.34', partly: 'Partly built in 2.34', no: 'Not built yet' }[p.built];
  document.querySelector('#inspect').innerHTML = `<h2>This screen</h2><dl class="facts"><dt>Lives at</dt><dd>${pathTo(S.place).map(id => esc(PLACE[id].label)).join(' / ')}</dd><dt>Back opens</dt><dd>${target ? esc(PLACE[target].label) : 'Leaves the app'}</dd><dt>Bar shows</dt><dd>${esc(PLACE[barOf(S.place)].label)}</dd>${p.views ? `<dt>Views</dt><dd>${p.views.join(', ')}</dd>` : ''}<dt>Native app</dt><dd><span class="built ${p.built}"><i></i>${built}</span></dd></dl>` +
    `<h2>What changed from 2.34</h2><ul>${(CHANGES[S.place] || []).map(c => `<li>${esc(c)}</li>`).join('')}</ul>` +
    `<h2>Asks this screen answers</h2><div>${(p.asks || []).map(a => `<span class="ask">${a}</span>`).join('')}</div>`;
}

function renderTop() {
  for (const b of document.querySelectorAll('[data-theme-set]')) b.classList.toggle('on', b.dataset.themeSet === S.theme);
  for (const b of document.querySelectorAll('[data-size-set]')) b.classList.toggle('on', b.dataset.sizeSet === S.size);
  for (const b of document.querySelectorAll('[data-tabs-set]')) b.classList.toggle('on', b.dataset.tabsSet === S.tabs);
  document.querySelector('#system-toggle').classList.toggle('on', reviewState.system);
  document.querySelector('#wall-toggle').classList.toggle('on', reviewState.wall);
  document.querySelector('#wall-toggle').textContent = reviewState.wall ? 'Back to one screen' : 'Show every screen';
}

/** Every screen and sheet as its own frame, from a clean state plus one change. */
function frames() {
  const list = [];
  const add = (group, label, place, change = () => {}, end = false) => list.push({ group, label, place, change, end });
  const session = (output, extra = {}) => s => { s.sessions[output] = { ...sampleSession(output, output === 'Pi screen' ? 'A Matter of Life and Death' : "Blackadder's Christmas Carol", 3120, 6240, 'Elements'), ...extra }; };

  for (const p of PLACES) {
    const group = PLACE[barOf(p.id)].label, needs = NEEDS_SESSION[p.id];
    add(group, p.label + (needs ? ', playing' : ''), p.id, needs ? session(needs) : undefined);
    if (p.id === 'pi-screen') add(group, 'Pi screen, idle', p.id);
    for (const v of (p.views || []).slice(1)) add(group, `${p.label}, ${v}`, p.id, s => { s.view[p.id] = v; if (p.id === 'search') s.searchQuery = 'a'; });
    if (p.id === 'search') add(group, 'Search, results', p.id, s => { s.searchQuery = 'walk'; });
    for (const spec of PLACE_SHEETS[p.id] || []) {
      const [type, ...rest] = spec.split('|');
      add(group, `Sheet: ${sheetName(spec)}`, p.id, s => {
        if (needs) session(needs)(s);
        if (type === 'replace') session('Pi screen')(s);
        if (p.id === 'process') s.shizuku = true;
        s.sheet = { type, arg: rest.join('|') };
      });
    }
  }
  add('Home', 'Home, power is low', 'home', s => { s.power = 'low'; });
  add('Home', 'Home, Pi offline', 'home', s => { s.pi = 'offline'; });
  add('Home', 'Home, sections closed', 'home', s => { s.folded = { pickup: true, caps: true, devices: true }; });
  add('Media', 'Media, inside a folder', 'media', s => { s.folder = 'Shows'; });
  add('Media', 'Media, searching', 'media', s => { s.mediaSearch = true; s.mediaQuery = 'a'; });
  add('Media', 'Media, drive missing', 'media', s => { s.drive = 'missing'; s.source = 'Elements'; });
  add('Media', 'Media, Pi offline', 'media', s => { s.pi = 'offline'; });
  add('Media', 'Pi screen, waiting to apply', 'pi-screen', session('Pi screen', { pending: { rotate: 90, loop: 'On' } }));
  add('Media', 'Pi screen, command failed', 'pi-screen', session('Pi screen', { error: 'The Pi did not answer, so nothing changed.' }));
  add('Media', 'Mini player, one output', 'media', session('Pi screen'));
  add('Media', 'Mini player, two outputs', 'media', s => { session('Pi screen')(s); session('This phone')(s); });
  add('Media', 'Player panel', 'media', s => { session('Pi screen')(s); s.panel = 'Pi screen'; });
  add('Media', 'Full screen on this phone', 'phone-player', s => { session('This phone')(s); s.full = true; });
  add('Media', 'Android media notification', 'media', s => { session('Pi screen')(s); s.shade = true; });
  add('Share', 'Share, recipient offline', 'share', s => { s.recipient = 'work-macbook'; s.shareText = 'Running late'; });
  add('Share', 'Share, send failed', 'share', s => { s.attachment = { kind: 'Image', title: 'IMG 4410.jpg' }; s.failed = 'IMG 4410.jpg'; s.sent.unshift({ title: 'IMG 4410.jpg', kind: 'Image', to: 'studio-mac', when: 'Just now', ok: false }); });
  add('Share', 'Share, nothing sent yet', 'share', s => { s.sent = []; });
  add('Share', 'Sheet: Clipboard, an image', 'share', s => { s.clip = { kind: 'Image', sub: 'Image, 1.2 MB', body: '' }; s.sheet = { type: 'clipboard', arg: '' }; });
  add('Share', 'Sheet: Send to a device, offline', 'media', s => { s.recipient = 'work-macbook'; s.sheet = { type: 'to-device', arg: 'video|Walk in the hills' }; });
  add('Share', 'Sheet: Item that is already playing', 'media', s => { session('Pi screen')(s); s.sheet = { type: 'item', arg: 'A Matter of Life and Death' }; });
  add('Share', 'Received, empty', 'received', s => { s.received = []; });
  add('Chat', 'Chat, searching', 'chat', s => { s.chatSearch = true; s.chatQuery = 'clip'; });
  add('Chat', 'Chat, Pi offline', 'chat', s => { s.pi = 'offline'; });
  add('Media', 'Pi screen, showing this phone', 'pi-screen', session('Pi screen', { title: "This phone's screen", source: 'This phone', live: true }));
  add('Chat', 'Conversation, message picked', 'conversation', s => { s.pickedMsg = 2; });
  add('Chat', 'Conversation, your message picked', 'conversation', s => { s.pickedMsg = 0; });
  add('Chat', 'Conversation, every kind of result', 'conversation', s => { s.threadId = 't2'; }, true);
  add('Chat', 'Conversation, result while it plays', 'conversation', session('Pi screen'));
  add('Chat', 'Conversation, title being edited', 'conversation', s => { s.editingTitle = true; });
  add('Chat', 'Conversation, long draft', 'conversation', s => { s.draft = 'Find the three shortest tutorials.\nPlay the first on the Pi screen.\nThen tell me how long the others are.'; s.draftOpen = true; });
  add('Chat', 'Conversation, with attachment', 'conversation', s => { s.chatAttachment = { kind: 'Image', title: 'IMG 4410.jpg' }; });
  add('Chat', 'Conversation, new', 'conversation', s => { s.threads.unshift({ id: 'tx', title: 'New conversation', when: 'Now', count: 0, favorite: false, archived: false, messages: [] }); s.threadId = 'tx'; });
  add('More', 'Camera, connecting', 'camera', s => { s.camera = 'connecting'; });
  add('More', 'Camera, recording', 'camera', s => { s.recording = true; });
  add('More', 'Camera, Pi offline', 'camera', s => { s.pi = 'offline'; });
  add('More', 'Note, editing', 'note', s => { s.view.note = 'Rich'; });
  add('More', 'Tools, power is low', 'tools', s => { s.power = 'low'; });
  add('More', 'Tools, end of the page', 'tools', () => {}, true);
  add('More', 'Connection, end of the page', 'connection', () => {}, true);
  add('More', 'Connection, Pi offline', 'connection', s => { s.pi = 'offline'; });
  add('More', 'Covers, framed', 'covers', s => { s.framing = { 'Desk at sunset': { fit: 'Contain', rotate: 90, crop: 'Full' } }; });
  add('More', 'Tools, Pi offline', 'tools', s => { s.pi = 'offline'; });
  add('More', 'Sheet: Power, low', 'tools', s => { s.power = 'low'; s.sheet = { type: 'power', arg: '' }; });
  add('More', 'Process monitor, Shizuku running', 'process', s => { s.shizuku = true; });
  add('More', 'Appearance, large text', 'appearance', s => { s.size = 'lg'; });
  return list;
}

function frameState(f) {
  const s = freshState();
  Object.assign(s, { theme: S.theme, size: S.size, accent: S.accent, custom: S.custom, tabs: S.tabs, place: f.place });
  f.change(s);
  return s;
}

function renderWall() {
  const wall = document.querySelector('#wall'), all = frames();
  let last = '';
  wall.innerHTML = all.map((f, i) => {
    const head = f.group !== last ? `<div class="gallery-head">${esc(f.group)}</div>` : '';
    last = f.group;
    return `${head}<div class="frame"><button type="button" data-frame="${i}" aria-label="Open ${esc(f.label)}"><div class="frame-box"><div class="phone" data-i="${i}"></div></div></button><div class="frame-cap"><b>${esc(f.label)}</b><span>${esc(pathTo(f.place).map(id => PLACE[id].label).join(' / '))}</span></div></div>`;
  }).join('');
  for (const el of wall.querySelectorAll('.phone')) {
    const s = frameState(all[el.dataset.i]);
    dress(el, s);
    if (all[el.dataset.i].end) el.dataset.end = '1';
    el.innerHTML = phoneHtml(s);
    el.style.transform = `scale(${el.parentElement.clientWidth / 390})`;
    tidy(el);
  }
}

function renderReview() {
  renderTop();
  document.querySelector('#one').hidden = reviewState.wall || reviewState.system;
  document.querySelector('#wall').hidden = !reviewState.wall;
  document.querySelector('#system').hidden = !reviewState.system;
  if (reviewState.system) return renderSystem();
  if (reviewState.wall) return renderWall();
  renderRail();
  renderInspector();
}

document.addEventListener('click', event => {
  const t = event.target.closest('[data-go],[data-state],[data-sheet],[data-theme-set],[data-size-set],[data-tabs-set],[data-frame],#wall-toggle,#system-toggle,#reset');
  if (!t || phone.contains(t)) return;
  if (t.dataset.tabsSet) { S.tabs = t.dataset.tabsSet; return render(); }
  if (t.id === 'system-toggle') { reviewState.system = !reviewState.system; reviewState.wall = false; return render(); }
  if (t.dataset.go) return go(t.dataset.go);
  if (t.dataset.state) { STATES[t.dataset.state][2](S); return render(); }
  if (t.dataset.sheet) {
    const needs = NEEDS_SESSION[S.place], [type, ...rest] = t.dataset.sheet.split('|');
    if (needs && !S.sessions[needs]) STATES[needs === 'Pi screen' ? 0 : 1][2](S);
    if (type === 'replace' && !S.sessions['Pi screen']) STATES[0][2](S);
    S.sheet = { type, arg: rest.join('|') };
    return render();
  }
  if (t.dataset.themeSet) { S.theme = t.dataset.themeSet; return render(); }
  if (t.dataset.sizeSet) { S.size = t.dataset.sizeSet; return render(); }
  if (t.dataset.frame) { const f = frames()[t.dataset.frame], keep = { theme: S.theme, size: S.size, accent: S.accent, custom: S.custom }; S = Object.assign(frameState(f), keep); reviewState.wall = false; return render(false); }
  if (t.id === 'wall-toggle') { reviewState.wall = !reviewState.wall; reviewState.system = false; return render(); }
  if (t.id === 'reset') { const keep = { theme: S.theme, size: S.size }; S = Object.assign(freshState(), keep); reviewState.wall = reviewState.system = false; return render(false); }
});
addEventListener('resize', () => { if (reviewState.wall) renderWall(); });

render(false);
