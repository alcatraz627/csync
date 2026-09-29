// State, the phone frame, and what each tap does. The review page around the
// phone is in review.js.

const clone = value => JSON.parse(JSON.stringify(value));

function freshState() {
  return {
    place: 'home', sheet: null, panel: null, toast: '', shade: false, full: false,
    view: { media: 'Files', chat: 'All', search: 'All', notes: 'Notes', note: 'Preview', incoming: 'Video' },
    theme: 'dark', size: 'sm', accent: 'coral', custom: '',
    pi: 'online', power: 'ok', drive: 'ok', sendFails: false, shizuku: false, update: true, camera: 'live',
    folded: {}, source: 'Pi USB', folder: '', mediaSearch: false, mediaQuery: '', searchQuery: '',
    sessions: { 'Pi screen': null, 'This phone': null },
    defaults: { skip: 10, startVolume: 0, resume: true, loop: 'Off' },
    recipient: 'studio-mac', shareText: '', attachment: null, failed: '', sent: clone(SENT), received: clone(RECEIVED),
    clip: { kind: 'Text', sub: 'Text, 46 characters', body: 'HDMI 2 is the Pi. HDMI 1 is the laptop dock.' }, widgets: ['xkcd'], customDraft: '',
    incomingOptions: { loop: 'Off', speed: 1, volume: 0 }, ytLink: '',
    chatSearch: false, chatQuery: '', threads: clone(THREADS), threadId: 't1', pickedMsg: null, editingTitle: false,
    draft: '', draftOpen: false, draftHeight: 200, chatAttachment: null,
    provider: 'Gemini', model: 'gemini-3.8-flash', effort: 'Medium', defaultModel: 'gemini-3.8-flash', defaultEffort: 'Medium', modelDraft: null,
    notes: clone(NOTES), pins: clone(PINS), noteId: 'n1', pinId: 'p1', notesSearch: false, noteQuery: '',
    captures: clone(CAPTURES), recording: false,
    cover: 'Desk at sunset', framing: {},
    conn: { pi: 'raspberrypi', second: '', token: 'csync-7f3a-9b21-44de', name: 'pixel-8', receive: true }, showToken: false
  };
}

let S = freshState();
const timers = {};
const OUTPUT_PAGE = { 'Pi screen': 'pi-screen', 'This phone': 'phone-player' };
const PAGE_OUTPUT = { 'pi-screen': 'Pi screen', 'phone-player': 'This phone' };
const resolvedTheme = state => state.theme === 'system' ? (matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'dark') : state.theme;

// the phone

function miniRow(s) {
  return `<div class="mini"><span class="bar-line"><i style="width:${Math.round(s.at / s.total * 100)}%"></i></span><button type="button" class="mini-open" ${on('panel', s.output)} aria-label="Open the player for ${esc(s.output)}">${status(sessionTone(s), `${sessionWords(s)} on ${s.output === 'Pi screen' ? 'Pi screen' : 'this phone'}`)}<b>${clamp(s.title, true)}</b></button>${ibtn(s.paused ? 'play' : 'pause', s.paused ? 'Resume' : 'Pause', 'p-pause', s.output, '', 19)}${ibtn('stop', 'Stop', 'p-stop', s.output, '', 18)}${ibtn('volume', 'Volume', 'sheet', `volume|${s.output}`, 'quiet', 18)}${ibtn('speed', 'Speed', 'sheet', `speed|${s.output}`, 'quiet', 18)}</div>`;
}

function panelHtml(state) {
  const s = state.panel && state.sessions[state.panel];
  if (!s) return '';
  return `<div class="panel" role="region" aria-label="Player"><div class="handle" data-drag="panel"><span></span></div><div class="panel-title"><div>${status(sessionTone(s), `${sessionWords(s)} on ${state.panel === 'Pi screen' ? 'Pi screen' : 'this phone'}`)}<b>${clamp(s.title, true)}</b></div>${ibtn('up', 'Open the full player', 'go', OUTPUT_PAGE[state.panel], 'quiet', 18)}</div>${playerControls(state, state.panel, true)}</div>`;
}

function shadeHtml(state) {
  if (!state.shade) return '';
  const list = active(state);
  return `<div class="shade" ${on('shade')}><div class="shade-card" data-hold>${list.length ? list.map(s => `<div class="panel-title">${icon('media', 20)}<div><b>${clamp(s.title, true)}</b>${status(sessionTone(s), `${sessionWords(s)} on ${s.output === 'Pi screen' ? 'Pi screen' : 'this phone'}`)}</div>${ibtn(s.paused ? 'play' : 'pause', s.paused ? 'Resume' : 'Pause', 'p-pause', s.output, '', 19)}${ibtn('stop', 'Stop', 'p-stop', s.output, '', 18)}</div>`).join('') : empty('media', 'Nothing is playing', '')}</div></div>`;
}

function fullHtml(state) {
  const s = state.sessions['This phone'];
  if (!state.full || !s) return '';
  return `<div class="full"><div class="full-art">${icon('video', 60)}</div><div class="full-ctl">${status(sessionTone(s), sessionWords(s))}<b>${clamp(s.title)}</b><div class="transport">${ibtn('rewind', `Back ${s.skip} seconds`, 'p-skip', 'This phone|-1', '', 22)}${ibtn(s.paused ? 'play' : 'pause', s.paused ? 'Resume' : 'Pause', 'p-pause', 'This phone', '', 26)}${ibtn('fastforward', `Forward ${s.skip} seconds`, 'p-skip', 'This phone|1', '', 22)}${ibtn('stop', 'Stop', 'p-stop', 'This phone', '', 22)}${ibtn('expand', 'Leave full screen', 'full', 'off', '', 22)}</div></div></div>`;
}

function phoneHtml(state) {
  const screen = SCREENS[state.place], shown = PAGE_OUTPUT[state.place];
  const minis = active(state).filter(s => s.output !== shown && s.output !== state.panel).map(miniRow).join('');
  const bar = BAR.map(id => `<button type="button" ${on('go', id)} aria-label="${PLACE[id].label}" title="${PLACE[id].label}" aria-current="${barOf(state.place) === id ? 'page' : 'false'}">${icon(PLACE[id].icon, 23)}</button>`).join('');
  return `<div class="p-status"><span>9:41</span><span><i></i><i></i></span></div>` +
    topBar(state.place, screen.actions ? screen.actions(state) : '') +
    `<div class="p-scroll" tabindex="0"><main class="p-page">${screen.body(state)}</main></div>` +
    (screen.composer ? screen.composer(state) : '') + minis +
    `<nav class="bar" aria-label="Main places">${bar}</nav><div class="gesture"></div>` +
    panelHtml(state) + renderSheet(state) + (state.toast ? `<div class="toast" role="status">${esc(state.toast)}</div>` : '') + shadeHtml(state) + fullHtml(state);
}

/** Set the colours and text size a phone frame draws with. */
function dress(el, state) {
  const dark = resolvedTheme(state) === 'dark';
  const a = ACCENTS.find(x => x.id === state.accent);
  const fill = state.accent === 'custom' && state.custom ? state.custom : a ? a.fill : ACCENTS[0].fill;
  const text = state.accent === 'custom' && state.custom ? `color-mix(in srgb, ${state.custom} 70%, ${dark ? '#fff' : '#000'})` : dark ? (a || ACCENTS[0]).onDark : (a || ACCENTS[0]).onLight;
  el.style.setProperty('--p-accent-fill', fill);
  el.style.setProperty('--p-accent', text);
  el.style.setProperty('--ts', { sm: 1, md: 1.15, lg: 1.3 }[state.size]);
  el.classList.toggle('narrow', state.size === 'lg');
}

/** Things that need the laid-out size: which long texts to fade, and when the path must shrink to icons. */
function tidy(el) {
  for (const c of el.querySelectorAll('.clamp')) {
    const over = c.classList.contains('one') ? c.scrollWidth > c.clientWidth + 1 : c.scrollHeight > c.clientHeight + 1;
    c.classList.toggle('cut', over);
  }
  for (const s of el.querySelectorAll('.seg')) {
    const chosen = s.querySelector('[aria-selected="true"]');
    if (chosen && s.scrollWidth > s.clientWidth) s.scrollLeft = chosen.offsetLeft - (s.clientWidth - chosen.clientWidth) / 2;
    s.classList.toggle('more', s.scrollLeft + s.clientWidth < s.scrollWidth - 1);
    s.classList.toggle('less', s.scrollLeft > 1);
  }
  if (el.dataset.end) { const area = el.querySelector('.p-scroll'); area.scrollTop = area.scrollHeight; }
  const crumbs = el.querySelector('.crumbs');
  if (!crumbs) return;
  for (const step of crumbs.querySelectorAll('.crumb:not(.now)')) {
    if (crumbs.scrollWidth <= crumbs.clientWidth) break;
    step.classList.add('icon-only');
  }
}

const phone = document.querySelector('#phone');

function render(keepScroll = true) {
  const scroll = keepScroll ? phone.querySelector('.p-scroll')?.scrollTop || 0 : 0;
  document.documentElement.dataset.theme = resolvedTheme(S);
  dress(phone, S);
  phone.innerHTML = phoneHtml(S);
  phone.querySelector('.p-scroll').scrollTop = scroll;
  delete phone.dataset.end;
  tidy(phone);
  if (location.hash.slice(1) !== S.place) history.replaceState(null, '', '#' + S.place);
  if (typeof renderReview === 'function') renderReview();
}

/** Re-draw while the person is typing, leaving the cursor where it was. */
function renderTyping(key) {
  const before = phone.querySelector(`[data-in="${key}"]`), start = before?.selectionStart, end = before?.selectionEnd;
  render();
  const after = phone.querySelector(`[data-in="${key}"]`);
  if (after) { after.focus(); try { after.setSelectionRange(start, end); } catch { /* colour and range inputs have no cursor */ } }
}

function toast(text) {
  S.toast = text; render();
  clearTimeout(timers.toast);
  timers.toast = setTimeout(() => { S.toast = ''; render(); }, 2600);
}

// moving around

function go(id, view) {
  if (!PLACE[id]) return;
  if (S.place === 'camera' && id !== 'camera') S.recording = false;
  Object.assign(S, { place: id, sheet: null, panel: null, pickedMsg: null, editingTitle: false, draftOpen: false, full: false, toast: '' });
  if (view) S.view[id] = view;
  render(false);
}

function back() {
  if (S.sheet) { S.sheet = null; S.modelDraft = null; return render(); }
  if (S.shade) { S.shade = false; return render(); }
  if (S.full) { S.full = false; return render(); }
  if (S.panel) { S.panel = null; return render(); }
  const target = backTarget(S.place);
  if (target) go(target); else toast(PLACE[S.place].fromOutside ? 'Back returns to the app you shared from' : 'Back from Home leaves csync');
}

// playing

function clearPending(output) {
  for (const key of Object.keys(timers)) if (key.startsWith(output + ':')) { clearTimeout(timers[key]); delete timers[key]; }
  if (S.sessions[output]) S.sessions[output].pending = {};
}

function start(output, title, at = 0, total = 0, source = '') {
  clearPending(output);
  const found = findItem(title), known = HISTORY.find(h => h.title === title);
  S.sessions[output] = { title, source: source || known?.source || S.source, at: Number(at) || 0, total: Number(total) || known?.total || (found.kind === 'image' ? 1 : 2580),
    paused: false, busy: true, error: '', volume: output === 'Pi screen' ? S.defaults.startVolume : 35, speed: 1, rotate: 0, loop: S.defaults.loop, favorite: false, skip: S.defaults.skip, pending: {} };
  if (S.place === 'incoming') Object.assign(S.sessions[output], { loop: S.incomingOptions.loop, speed: S.incomingOptions.speed, volume: S.incomingOptions.volume });
  go(OUTPUT_PAGE[output]);
  timers[output + ':load'] = setTimeout(() => { if (S.sessions[output]) { S.sessions[output].busy = false; render(); } }, 700);
}

function play(arg) {
  const [output, title, at, total, source] = arg.split('|');
  const now = S.sessions[output];
  if (now && now.title !== title) { S.sheet = { type: 'replace', arg }; return render(); }
  start(output, title, at, total, source);
}

function stop(output) {
  clearPending(output);
  S.sessions[output] = null;
  if (S.panel === output) S.panel = null;
  if (S.sheet && String(S.sheet.arg).includes(output)) S.sheet = null;
  S.full = false;
  if (S.place === 'phone-player' && output === 'This phone') return go('media');
  toast(`Stopped on ${output === 'Pi screen' ? 'the Pi screen' : 'this phone'}`);
}

/** Rotate and Loop wait two seconds after the last tap, then apply; Stop cancels the wait. */
function later(output, key, value) {
  const s = S.sessions[output];
  s.pending[key] = value;
  clearTimeout(timers[`${output}:${key}`]);
  timers[`${output}:${key}`] = setTimeout(() => {
    const live = S.sessions[output];
    if (!live) return;
    live[key] = value; delete live.pending[key]; render();
  }, 2000);
  render();
}

// what each tap does

const ACTS = {
  go: id => go(id),
  back,
  view: arg => { const [place, view] = arg.split('|'); go(place, view); },
  'view-media': v => { S.view.media = v; render(false); },
  'view-chat': v => { S.view.chat = v; render(false); },
  'view-search': v => { S.view.search = v; render(); },
  'view-notes': v => { S.view.notes = v; S.noteQuery = ''; render(false); },
  'view-note': v => { S.view.note = v; render(); },
  fold: id => { S.folded[id] = !S.folded[id]; render(); },
  toggle: key => { S[key] = !S[key]; if (!S[key]) { if (key === 'mediaSearch') S.mediaQuery = ''; if (key === 'chatSearch') S.chatQuery = ''; if (key === 'notesSearch') S.noteQuery = ''; } render(); },
  sheet: arg => { const [type, ...rest] = arg.split('|'); S.modelDraft = null; S.customDraft = ''; S.sheet = { type, arg: rest.join('|') }; render(); },
  'close-sheet': () => { S.sheet = null; S.modelDraft = null; render(); },
  toast: text => { S.sheet = null; toast(text); },
  copy: text => toast(`Copied ${text}`),
  shade: () => { S.shade = !S.shade; render(); },
  full: v => { S.full = v === 'on'; render(); },
  panel: output => { S.panel = output; render(); },

  play, 'play-now': arg => { const [output, title, at, total, source] = arg.split('|'); start(output, title, at, total, source); },
  resume: index => { const h = HISTORY[index]; play(`${h.output}|${h.title}|${h.at}|${h.total}|${h.source}`); },
  'play-link': () => { const link = S.ytLink.trim(); S.ytLink = ''; play(`Pi screen|${link.replace(/^https?:\/\//, '').slice(0, 40)}|0|600|YouTube`); },
  'show-camera': () => play('Pi screen|Pi camera, live|0|1|Pi camera'),
  move: from => { const s = S.sessions[from], to = from === 'Pi screen' ? 'This phone' : 'Pi screen'; clearPending(from); S.sessions[from] = null; start(to, s.title, s.at, s.total, s.source); },
  'p-pause': output => {
    const s = S.sessions[output];
    if (!s || s.busy) return;
    s.busy = true; s.error = ''; render();
    timers[output + ':pause'] = setTimeout(() => {
      const live = S.sessions[output];
      if (!live) return;
      live.busy = false;
      if (output === 'Pi screen' && !piUp(S)) live.error = 'The Pi did not answer, so nothing changed.'; else live.paused = !live.paused;
      render();
    }, 400);
  },
  'p-stop': stop,
  'p-skip': arg => { const [output, dir] = arg.split('|'), s = S.sessions[output]; s.at = Math.max(0, Math.min(s.total, s.at + Number(dir) * s.skip)); render(); },
  'p-favorite': output => { const s = S.sessions[output]; s.favorite = !s.favorite; render(); },
  'p-rotate': output => { const s = S.sessions[output]; later(output, 'rotate', ((s.pending.rotate ?? s.rotate) + 90) % 360); },
  'p-loop': output => { const s = S.sessions[output]; later(output, 'loop', (s.pending.loop ?? s.loop) === 'On' ? 'Off' : 'On'); },
  'set-skip': arg => { const [output, n] = arg.split('|'); if (output === 'default') S.defaults.skip = Number(n); else S.sessions[output].skip = Number(n); S.sheet = null; render(); },
  'default-loop': () => { S.defaults.loop = S.defaults.loop === 'On' ? 'Off' : 'On'; render(); },
  'toggle-resume': () => { S.defaults.resume = !S.defaults.resume; render(); },

  'pick-source': name => { Object.assign(S, { source: name, folder: '', mediaQuery: '', sheet: null }); if (S.place !== 'media') return go('media', 'Files'); if (S.view.media === 'Access') S.view.media = 'Files'; toast(`Browsing ${name === 'This phone' ? 'this phone' : name}`); },
  folder: name => { S.folder = name; S.sheet = null; render(false); },
  cover: name => { S.cover = name; toast(`${name} is the cover`); },
  'set-cover': title => { S.sheet = null; if (!COVERS.includes(title)) COVERS.push(title), COVER_ART.push(COVER_ART[0]); S.cover = title; toast(`${title} is the cover`); },
  'frame-fit': v => frame('fit', v), 'frame-crop': v => frame('crop', v),
  'frame-turn': () => frame('rotate', (((S.framing[S.cover] || {}).rotate || 0) + 90) % 360),
  'frame-clear': () => { delete S.framing[S.cover]; toast(`Framing cleared for ${S.cover}`); },

  'pick-recipient': name => { S.recipient = name; S.sheet = null; render(); },
  'pick-recipient-stay': name => { S.recipient = name; render(); },
  'send-item': arg => { const [kind, ...rest] = arg.split('|'); S.sheet = null; deliver(rest.join('|'), { image: 'Image', video: 'Video', text: 'Text', link: 'Link' }[kind] || 'File'); },
  'widget-toggle': name => { S.widgets = S.widgets.includes(name) ? S.widgets.filter(w => w !== name) : [...S.widgets, name]; S.sheet = null; toast(S.widgets.includes(name) ? `${name} added` : `${name} removed`); },
  'pick-recipient-go': name => { S.recipient = name; go('share'); },
  attach: arg => { const [kind, title] = arg.split('|'); S.attachment = { kind, title }; S.sheet = null; S.failed = ''; render(); },
  detach: () => { S.attachment = null; S.failed = ''; render(); },
  'use-clip': () => { if (S.clip.kind === 'Image') S.attachment = { kind: 'Image', title: 'Clipboard image' }; else S.shareText = S.clip.body; S.sheet = null; render(); },
  'send-clip': () => { S.sheet = null; deliver(S.clip.kind === 'Image' ? 'Clipboard image' : 'Clipboard text', S.clip.kind); },
  send: () => {
    if (S.attachment) deliver(S.attachment.title, S.attachment.kind, true);
    if (S.shareText.trim() && !S.failed) { deliver(S.shareText.trim().split('\n')[0].slice(0, 40), 'Text'); S.shareText = ''; }
    render();
  },
  resend: index => { const t = S.sent[index]; S.sheet = null; S.recipient = t.to; deliver(t.title, t.kind); },

  'open-thread': id => { S.threadId = id; S.draft = ''; go('conversation'); },
  'new-thread': () => { const id = 't' + Date.now(); S.threads.unshift({ id, title: 'New conversation', when: 'Now', count: 0, favorite: false, archived: false, messages: [] }); S.threadId = id; S.model = S.defaultModel; S.effort = S.defaultEffort; S.draft = ''; go('conversation'); },
  'edit-title': () => { S.editingTitle = true; render(); const input = phone.querySelector('[data-in="threadTitle"]'); input?.focus(); input?.select(); },
  'fav-thread': () => { const t = thread(S); t.favorite = !t.favorite; toast(t.favorite ? 'Added to favorites' : 'Removed from favorites'); },
  'arch-thread': () => { const t = thread(S); t.archived = !t.archived; toast(t.archived ? 'Archived' : 'Back in the main list'); },
  'pick-msg': i => { S.pickedMsg = S.pickedMsg === Number(i) ? null : Number(i); render(); },
  'draft-open': () => { S.draftOpen = true; render(); phone.querySelector('.draft textarea')?.focus(); },
  'attach-chat-file': arg => { const [kind, title] = arg.split('|'); S.chatAttachment = { kind, title }; S.sheet = null; render(); },
  'attach-chat': arg => { const [id, kind, ...rest] = arg.split('|'); if (id === 'new') ACTS['new-thread'](); else { S.threadId = id; go('conversation'); } S.chatAttachment = { kind: { image: 'Image', video: 'Video', text: 'Text', link: 'Link' }[kind] || 'File', title: rest.join('|') }; render(); },
  'chat-detach': () => { S.chatAttachment = null; render(); },
  'send-chat': () => {
    const text = S.draft.trim(), t = thread(S);
    if (!text && !S.chatAttachment) return toast('Write a message or add something first');
    t.messages.push({ me: true, text: [text, S.chatAttachment ? `Attached: ${S.chatAttachment.title}` : ''].filter(Boolean).join('\n\n'), when: 'Now' }, { me: false, text: 'This is a sample reply. The mock is not connected to the Pi.', when: 'Now' });
    t.count = t.messages.filter(m => !m.thinking).length; t.when = 'Now';
    Object.assign(S, { draft: '', draftOpen: false, chatAttachment: null });
    render(); const scroll = phone.querySelector('.p-scroll'); scroll.scrollTop = scroll.scrollHeight;
  },
  'draft-model': arg => { const [scope, model] = arg.split('|'); S.modelDraft = { ...currentDraft(scope), model }; const owner = MODELS.find(m => m.models.includes(model)); if (!owner.efforts.includes(S.modelDraft.effort)) S.modelDraft.effort = owner.efforts[0]; render(); },
  'draft-effort-chat': v => { S.modelDraft = { ...currentDraft('chat'), effort: v }; render(); },
  'draft-effort-default': v => { S.modelDraft = { ...currentDraft('default'), effort: v }; render(); },
  'save-model': scope => { saveModel(scope); toast('Model saved'); },
  'save-model-send': scope => { saveModel(scope); ACTS['send-chat'](); },
  provider: v => { S.provider = v; render(); },
  fork: index => { const t = thread(S), id = 't' + Date.now(); S.threads.unshift({ ...clone(t), id, title: `${t.title}, fork`, when: 'Now', messages: clone(t.messages.slice(0, Number(index) + 1)) }); S.threadId = id; S.sheet = null; go('conversation'); },

  photo: () => { S.captures[0].items.unshift({ id: 'c' + Date.now(), kind: 'Photo', when: 'Now', size: '19 kB' }); toast('Photo saved to Captures'); },
  record: () => { S.recording = !S.recording; if (!S.recording) S.captures[0].items.unshift({ id: 'c' + Date.now(), kind: 'Recording', length: '18 s', when: 'Now', size: '2.0 MB' }); toast(S.recording ? 'Recording' : 'Recording saved to Captures'); },
  'delete-capture': id => { for (const d of S.captures) d.items = d.items.filter(i => i.id !== id); S.sheet = null; toast('Deleted'); },

  'open-note': id => { S.noteId = id; S.view.note = 'Preview'; go('note'); },
  'new-note': () => { const id = 'n' + Date.now(); S.notes.unshift({ id, title: 'Untitled note', edited: 'Edited just now', body: '' }); S.noteId = id; S.view.note = 'Plain'; go('note'); },
  'save-note': () => { const n = S.notes.find(x => x.id === S.noteId), rich = phone.querySelector('[data-rich]'); if (rich) n.body = rich.innerText.trim(); n.edited = 'Edited just now'; toast('Note saved'); },
  'delete-note': () => { S.notes = S.notes.filter(n => n.id !== S.noteId); go('notes'); },
  'open-pin': id => { S.pinId = id; go('pin'); },
  'new-pin': () => { const id = 'p' + Date.now(); S.pins.unshift({ id, title: 'Untitled pin', link: '', text: '', tags: [], about: '' }); S.pinId = id; go('pin'); },
  'save-pin': () => toast('Pin saved'),
  'delete-pin': () => { S.pins = S.pins.filter(p => p.id !== S.pinId); S.view.notes = 'Pins'; go('notes'); },

  recheck: () => { S.sheet = null; toast(piUp(S) ? 'Checked just now' : 'The Pi did not answer'); },
  'shizuku-on': () => { S.shizuku = true; toast('Shizuku is running'); },
  install: () => { S.update = false; S.sheet = null; toast('Updated to 2.35'); },
  'toggle-receive': () => { S.conn.receive = !S.conn.receive; render(); },
  theme: v => { S.theme = v.toLowerCase(); render(); },
  size: v => { S.size = { Small: 'sm', Medium: 'md', Large: 'lg' }[v]; render(); },
  accent: id => { S.accent = id; render(); },
  'use-custom': () => { S.custom = S.customDraft || S.custom || '#8B5CF6'; S.customDraft = ''; S.accent = 'custom'; S.sheet = null; render(); },
  'in-loop': () => { S.incomingOptions.loop = S.incomingOptions.loop === 'On' ? 'Off' : 'On'; render(); }
};

const currentDraft = scope => S.modelDraft || { model: scope === 'default' ? S.defaultModel : S.model, effort: scope === 'default' ? S.defaultEffort : S.effort };
function saveModel(scope) {
  const d = currentDraft(scope);
  if (scope === 'default') Object.assign(S, { defaultModel: d.model, defaultEffort: d.effort }); else Object.assign(S, { model: d.model, effort: d.effort });
  S.modelDraft = null; S.sheet = null;
}
function frame(key, value) {
  S.framing[S.cover] = { fit: 'Cover', rotate: 0, crop: 'Full', ...S.framing[S.cover], [key]: value };
  toast(`Saved for ${S.cover}`);
}
function deliver(title, kind, isAttachment = false) {
  const ok = !S.sendFails;
  S.sent.unshift({ title, kind, to: S.recipient, when: 'Just now', ok });
  if (ok) { if (isAttachment) S.attachment = null; S.failed = ''; toast(`Delivered to ${S.recipient}`); }
  else { S.failed = title; toast(`Not delivered to ${S.recipient}`); }
}

// listening

phone.addEventListener('click', event => {
  const hit = event.target.closest('[data-act]');
  if (!hit || !phone.contains(hit)) return;
  if (hit.matches('.scrim, .shade') && event.target.closest('[data-hold]')) return;
  if (event.target.closest('.msg a')) return;
  if (hit.matches('.msg') && String(getSelection()).trim()) return;
  event.preventDefault();
  ACTS[hit.dataset.act]?.(hit.dataset.arg || '');
});

const SEARCHES = ['searchQuery', 'mediaQuery', 'chatQuery', 'noteQuery'];
phone.addEventListener('input', event => {
  const el = event.target.closest('[data-in]');
  if (!el) return;
  const key = el.dataset.in, value = el.value, output = el.dataset.arg;
  const say = (name, text) => { const out = phone.querySelector(`[data-live="${name}"]`); if (out) out.textContent = text; };
  if (SEARCHES.includes(key)) { S[key] = value; return renderTyping(key); }
  if (key === 'shareText' || key === 'ytLink') { S[key] = value; return renderTyping(key); }
  if (key === 'seek') { S.sessions[output].at = Number(value); phone.querySelector('.times span').textContent = clock(value); return; }
  if (key === 'volume') { S.sessions[output].volume = Number(value); return say('volume', value === '0' ? 'Muted' : value + '%'); }
  if (key === 'speed') { S.sessions[output].speed = Number(value); return say('speed', value + '×'); }
  if (key === 'startVolume') { S.defaults.startVolume = Number(value); return say('startVolume', value === '0' ? 'Muted' : value + '%'); }
  if (key === 'in-speed') { S.incomingOptions.speed = Number(value); return renderTyping(key); }
  if (key === 'in-volume') { S.incomingOptions.volume = Number(value); return renderTyping(key); }
  if (key === 'hue') { S.customDraft = hueHex(Number(value)); return renderTyping(key); }
  if (key === 'hex') { if (/^#[0-9a-f]{6}$/i.test(value.trim())) { S.customDraft = value.trim().toUpperCase(); return renderTyping(key); } return; }
  if (key === 'threadTitle') { thread(S).title = value; return; }
  if (key === 'noteTitle') { S.notes.find(n => n.id === S.noteId).title = value; return; }
  if (key === 'noteBody') { S.notes.find(n => n.id === S.noteId).body = value; const rich = phone.querySelector('#rich-preview'); if (rich) rich.innerHTML = markdown(value); return; }
  if (key.startsWith('conn.')) { S.conn[key.slice(5)] = value; return; }
  if (key.startsWith('pin')) {
    const p = S.pins.find(x => x.id === S.pinId);
    if (key === 'pinTitle') p.title = value; else if (key === 'pinAbout') p.about = value;
    else if (key === 'pinTags') p.tags = value.split(',').map(t => t.trim()).filter(Boolean);
    else if (/^https?:\/\//.test(value)) { p.link = value; p.text = ''; } else { p.text = value; p.link = ''; }
    return;
  }
  if (key === 'draft') {
    S.draft = value;
    const grew = !S.draftOpen && (value.split('\n').length > 2 || el.scrollHeight > el.clientHeight + 18);
    if (grew) { S.draftOpen = true; render(); const big = phone.querySelector('.draft textarea'); big.focus(); big.setSelectionRange(value.length, value.length); }
  }
});

phone.addEventListener('focusout', event => {
  if (!event.target.matches('[data-in="threadTitle"]')) return;
  const t = thread(S); t.title = t.title.trim() || 'Untitled conversation'; S.editingTitle = false; render();
});
phone.addEventListener('keydown', event => {
  if (event.target.matches('[data-in="threadTitle"]') && event.key === 'Enter') { event.preventDefault(); event.target.blur(); }
  if (event.target.matches('.msg') && (event.key === 'Enter' || event.key === ' ')) { event.preventDefault(); ACTS['pick-msg'](event.target.dataset.arg); }
});
addEventListener('keydown', event => { if (event.key === 'Escape' && !event.target.matches('input, textarea')) { event.preventDefault(); back(); } });

let drag = null;
phone.addEventListener('pointerdown', event => { const grip = event.target.closest('[data-drag]'); if (grip) drag = { what: grip.dataset.drag, y: event.clientY }; });
addEventListener('pointerup', event => {
  if (!drag) return;
  const moved = event.clientY - drag.y, what = drag.what;
  drag = null;
  if (what === 'sheet' && moved > 50) ACTS['close-sheet']();
  if (what === 'panel' && moved > 50) { S.panel = null; render(); }
  if (what === 'panel' && moved < -50) go(OUTPUT_PAGE[S.panel]);
  if (what === 'draft' && moved > 50) { S.draftOpen = false; render(); }
  if (what === 'draft' && moved < -25) { S.draftHeight = Math.min(430, S.draftHeight - moved); render(); }
});

addEventListener('hashchange', () => { const id = location.hash.slice(1); if (PLACE[id] && id !== S.place) go(id); });
matchMedia('(prefers-color-scheme: light)').addEventListener('change', () => { if (S.theme === 'system') render(); });

if (PLACE[location.hash.slice(1)]) S.place = location.hash.slice(1);
