// Every sheet in the app. A sheet is a short choice, one value to adjust, a
// confirmation, or the facts about one row. Anything larger is a page.

const findItem = title => [...Object.values(LIBRARY).flat(), ...VIDEOS].find(i => i.title === title) || { kind: 'video', title, file: title, size: '' };

/** Rows that start playback, with the output named in the words of each one. */
function playRows(S, title, verb = 'Play') {
  const up = piUp(S), busy = S.sessions['Pi screen'], phoneBusy = S.sessions['This phone'];
  return row({ icon: 'screen', accent: up, title: `${verb} on Pi screen`, off: !up,
      sub: !up ? 'The Pi is offline' : busy ? `Replaces ${busy.title}` : S.defaults.startVolume === 0 ? 'Starts muted' : `Starts at ${S.defaults.startVolume}%`,
      act: 'play', arg: `Pi screen|${title}` }) +
    row({ icon: 'device', title: `${verb} on this phone`, sub: phoneBusy ? `Replaces ${phoneBusy.title}` : 'Speaker, headphones or a wired screen', act: 'play', arg: `This phone|${title}` });
}

const SHEETS = {

  item(S, title) {
    const it = findItem(title), plays = ['video', 'audio'].includes(it.kind), shows = it.kind === 'image';
    const first = plays ? section('Play', group(playRows(S, title) + row({ icon: 'expand', title: 'Open in VLC', sub: 'Hands the file to VLC on this phone', act: 'toast', arg: 'Opened in VLC' })))
      : shows ? section('Show', group(row({ icon: 'screen', accent: piUp(S), title: 'Show on Pi screen', off: !piUp(S), sub: piUp(S) ? '' : 'The Pi is offline', act: 'play', arg: `Pi screen|${title}` }) +
          row({ icon: 'image', title: 'Set as the Pi cover', off: !piUp(S), act: 'toast', arg: `${title} is the cover` }))) : '';
    return sheet({ title, sub: [it.length, it.size].filter(Boolean).join(' · '), body: first + section(plays || shows ? 'Also' : 'Do', group(
      row({ icon: 'download', title: 'Download to this phone', act: 'toast', arg: `Downloading ${title}` }) +
      row({ icon: 'chat', title: 'Send to a conversation', act: 'sheet', arg: `to-chat|${title}`, opens: true }) +
      row({ icon: 'share', title: 'Send to a device', act: 'attach-go', arg: `${it.kind}|${title}` }) +
      row({ icon: 'upload', title: 'Share with another app', act: 'toast', arg: 'Opened the Android share menu' }) +
      row({ icon: 'info', title: 'File details', act: 'sheet', arg: `details|${title}`, opens: true }))) });
  },

  details(S, title) {
    const it = findItem(title);
    return sheet({ title, sub: 'File details', body: facts([['File name', it.file || title], ['Kind', it.kind], it.length && ['Length', it.length], it.size && ['Size', it.size], ['Drive', S.source], ['Folder', it.folder || S.folder || 'Top level']]) });
  },

  folder(S, name) {
    const f = (LIBRARY[''] || []).find(i => i.title === name) || { count: 0 };
    return sheet({ title: name, sub: `Folder, ${plural(f.count, 'item')}`, body: group(
      row({ icon: 'folder', title: 'Open', act: 'folder', arg: name }) +
      row({ icon: 'download', title: 'Download to this phone', sub: 'Everything inside it', act: 'toast', arg: `Downloading ${name}` }) +
      row({ icon: 'share', title: 'Send to a device', act: 'attach-go', arg: `folder|${name}` })) });
  },

  resume(S, index) {
    const h = HISTORY[index], up = piUp(S), other = h.output === 'Pi screen' ? 'This phone' : 'Pi screen';
    const can = o => o === 'This phone' || up;
    const say = o => o === 'Pi screen' ? 'Pi screen' : 'this phone';
    return sheet({ title: h.title, sub: `${h.source} · ${left(h)}`, body: group(
      row({ icon: 'play', accent: can(h.output), title: `Resume on ${say(h.output)}`, sub: can(h.output) ? `From ${clock(h.at)}` : 'The Pi is offline', off: !can(h.output), act: 'play', arg: `${h.output}|${h.title}|${h.at}|${h.total}|${h.source}` }) +
      row({ icon: 'rewind', title: `Start over on ${say(h.output)}`, off: !can(h.output), act: 'play', arg: `${h.output}|${h.title}|0|${h.total}|${h.source}` }) +
      row({ icon: other === 'Pi screen' ? 'screen' : 'device', title: `Resume on ${say(other)}`, sub: can(other) ? `From ${clock(h.at)}` : 'The Pi is offline', off: !can(other), act: 'play', arg: `${other}|${h.title}|${h.at}|${h.total}|${h.source}` })) });
  },

  replace(S, arg) {
    const [output, title] = arg.split('|'), now = S.sessions[output];
    return sheet({ title: `Replace what is playing on ${output === 'Pi screen' ? 'the Pi screen' : 'this phone'}?`, sub: `${now.title} stops and ${title} starts.`,
      body: '', acts: btn(`Keep ${now.title}`, 'back', 'close-sheet') + btn(`Play ${title}`, 'play', 'play-now', arg, 'primary') });
  },

  move(S, from) {
    const s = S.sessions[from], to = from === 'Pi screen' ? 'This phone' : 'Pi screen', up = piUp(S) || to === 'This phone';
    return sheet({ title: `Move to ${to === 'Pi screen' ? 'the Pi screen' : 'this phone'}`, sub: `${s.title} carries on from ${clock(s.at)}.`,
      body: up ? '' : notice('bad', 'The Pi is offline.'), acts: btn('Stay here', 'back', 'close-sheet') + btn('Move', to === 'Pi screen' ? 'screen' : 'device', 'move', from, 'primary', up ? '' : 'disabled') });
  },

  source(S) {
    const gone = S.drive !== 'ok', up = piUp(S);
    return sheet({ title: 'Choose a source', body: group(
      row({ icon: 'files', title: 'Pi USB', status: up ? ['good', 'Connected'] : ['idle', 'Pi offline'], picked: S.source === 'Pi USB', off: !up, act: 'pick-source', arg: 'Pi USB' }) +
      row({ icon: 'files', title: 'Elements', status: !up ? ['idle', 'Pi offline'] : gone ? ['idle', 'Disconnected'] : ['good', 'Connected'], picked: S.source === 'Elements', off: !up || gone, act: 'pick-source', arg: 'Elements' }) +
      row({ icon: 'device', title: 'This phone', sub: 'Files stored here', picked: S.source === 'This phone', act: 'pick-source', arg: 'This phone' })) });
  },

  recipient(S) {
    return sheet({ title: 'Send to', body: group(DEVICES.filter(d => !d.self).sort((a, b) => b.online - a.online).map(d =>
      row({ icon: deviceIcon(d), title: d.name, status: d.hub && !piUp(S) ? ['idle', 'Offline'] : deviceStatus(d), picked: d.name === S.recipient, act: 'pick-recipient', arg: d.name })).join('')) });
  },

  device(S, name) {
    const d = device(S, name), up = d.hub ? piUp(S) : d.online;
    const kind = { pi: 'Raspberry Pi', laptop: 'Laptop', desktop: 'Desktop', device: 'Phone or tablet' }[d.kind];
    return sheet({ title: d.name, sub: up ? 'Online' : 'Offline',
      body: facts([['Kind', kind], ['Address', d.address], !up && ['Last seen', d.seen || 'Today'], d.hub && ['Runs', 'Media, assistant, camera, notes']]) +
        group(row({ icon: 'send', accent: up, title: `Send to ${d.name}`, off: !up, sub: up ? '' : 'It is offline', act: 'pick-recipient-go', arg: d.name }) +
          (d.hub ? row({ icon: 'tools', title: 'Check the Pi', act: 'go', arg: 'tools', opens: true }) : row({ icon: 'trash', danger: true, title: 'Forget this device', act: 'toast', arg: `${d.name} forgotten` }))) });
  },

  attach() {
    return sheet({ title: 'Attach a file', sub: 'From this phone', body: group(
      [['IMG 4410.jpg', 'Image', 'Photo, 1.8 MB'], ['VID 2026-09-26.mp4', 'Video', 'Video, 64 MB'], ['quote.pdf', 'File', 'Document, 220 kB']].map(([t, k, s]) =>
        row({ icon: KIND_ICON[k], title: t, sub: s, act: 'attach', arg: `${k}|${t}` })).join('')) });
  },

  clipboard(S) {
    return sheet({ title: 'On the clipboard', sub: S.clip.sub, body: `<div class="card">${esc(S.clip.body)}</div>`,
      acts: btn('Put it in the message', 'clipboard', 'use-clip', '') + btn(`Send to ${S.recipient}`, 'send', 'send-clip', '', 'primary', device(S, S.recipient).online ? '' : 'disabled') });
  },

  sent(S, index) {
    const t = S.sent[index];
    return sheet({ title: t.title, sub: t.ok ? 'Delivered' : 'Not delivered', body: facts([['Kind', t.kind], ['To', t.to], ['When', `${t.when}, ${t.time || 'now'}`]]),
      acts: t.ok ? btn('Send again', 'refresh', 'resend', index) : btn('Send again', 'refresh', 'resend', index, 'primary') });
  },

  received(S, index) {
    const r = S.received[index], plays = r.kind === 'Video', shows = r.kind === 'Image';
    return sheet({ title: r.title, sub: `From ${r.from} · ${day(r.when)}, ${r.time}`, body: (r.body ? `<div class="card">${esc(r.body)}</div>` : '') + group(
      (plays ? playRows(S, r.title) : '') +
      (shows ? row({ icon: 'screen', title: 'Show on Pi screen', off: !piUp(S), act: 'play', arg: `Pi screen|${r.title}` }) : '') +
      (r.body ? row({ icon: 'copy', title: 'Copy the text', act: 'toast', arg: 'Copied' }) : row({ icon: 'download', title: 'Save on this phone', act: 'toast', arg: `Saved ${r.title}` })) +
      row({ icon: 'chat', title: 'Send to a conversation', act: 'sheet', arg: `to-chat|${r.title}`, opens: true }) +
      row({ icon: r.body ? 'note' : 'pin', title: r.body ? 'Save as a note' : 'Save as a pin', act: 'toast', arg: r.body ? 'Saved to Notes' : 'Saved to Pins' }) +
      row({ icon: 'upload', title: 'Share with another app', act: 'toast', arg: 'Opened the Android share menu' })) });
  },

  'to-chat'(S, title) {
    return sheet({ title: 'Send to a conversation', sub: title || 'Shared item', body: group(
      S.threads.filter(t => !t.archived).map(t => row({ icon: 'chat', title: t.title, sub: t.when, act: 'attach-chat', arg: `${t.id}|${title || 'Shared item'}` })).join('') +
      row({ icon: 'plus', title: 'A new conversation', act: 'attach-chat', arg: `new|${title || 'Shared item'}` })) });
  },

  volume(S, output) {
    const s = S.sessions[output];
    return sheet({ title: 'Volume', sub: output === 'Pi screen' ? 'Pi screen' : 'This phone',
      body: `<div class="labelled"><span data-live="volume">${s.volume === 0 ? 'Muted' : s.volume + '%'}</span><input class="range" type="range" min="0" max="100" step="5" value="${s.volume}" data-in="volume" data-arg="${esc(output)}" aria-label="Volume"><div class="range-ends"><span>Muted</span><span>100%</span></div></div>` });
  },

  speed(S, output) {
    const s = S.sessions[output];
    return sheet({ title: 'Speed', sub: output === 'Pi screen' ? 'Pi screen' : 'This phone',
      body: `<div class="labelled"><span data-live="speed">${s.speed}×</span><input class="range" type="range" min="0.5" max="2" step="0.25" value="${s.speed}" data-in="speed" data-arg="${esc(output)}" aria-label="Speed"><div class="range-ends"><span>0.5×</span><span>2×</span></div></div>` });
  },

  skip(S, output) {
    const now = output === 'default' ? S.defaults.skip : S.sessions[output].skip;
    return sheet({ title: 'Skip length', sub: 'For both Back and Forward', body: group([5, 10, 15, 30, 60].map(n => row({ icon: 'skip', title: `${n} seconds`, picked: n === now, act: 'set-skip', arg: `${output}|${n}` })).join('')) });
  },

  'start-volume'(S) {
    const v = S.defaults.startVolume;
    return sheet({ title: 'Starting volume', sub: 'On the Pi screen',
      body: `<div class="labelled"><span data-live="startVolume">${v === 0 ? 'Muted' : v + '%'}</span><input class="range" type="range" min="0" max="100" step="5" value="${v}" data-in="startVolume" aria-label="Starting volume"><div class="range-ends"><span>Muted</span><span>100%</span></div></div>` });
  },

  youtube(S) {
    return sheet({ title: 'A YouTube link', sub: 'Plays on the Pi screen',
      body: field({ id: 'ytLink', hint: 'Paste the link', value: S.ytLink, icon: 'link' }) + `<p class="note-line">${icon('share', 14)}From the YouTube app, use Share and choose csync.</p>`,
      acts: btn('Play on Pi screen', 'screen', 'play-link', '', 'primary', S.ytLink.trim() ? '' : 'disabled') });
  },

  'chat-add'(S) {
    return sheet({ title: 'Add to this message', body: group(
      row({ icon: 'photo', title: 'An image', sub: 'The assistant can look at it', act: 'attach-chat-file', arg: 'Image|IMG 4410.jpg' }) +
      row({ icon: 'file', title: 'A file', sub: 'Kept on the Pi', act: 'attach-chat-file', arg: 'File|quote.pdf' }) +
      row({ icon: 'speed', title: 'Model', value: `${S.model} ${S.effort.toLowerCase()}`, act: 'sheet', arg: 'model|chat', opens: true })) });
  },

  model(S, scope) {
    const d = S.modelDraft || { model: scope === 'default' ? S.defaultModel : S.model, effort: scope === 'default' ? S.defaultEffort : S.effort };
    const owner = MODELS.find(m => m.models.includes(d.model)) || MODELS[0];
    const lists = MODELS.map(m => section(m.available ? m.provider : `${m.provider}, not set up on this Pi`, group(m.models.map(name =>
      row({ icon: 'chat', title: name, picked: name === d.model, off: !m.available, act: 'draft-model', arg: `${scope}|${name}` })).join('')))).join('');
    return sheet({ title: scope === 'default' ? 'Model for new conversations' : 'Model for this conversation', body: lists +
      labelled(`Thinking, for ${d.model}`, seg(owner.efforts.map((e, i) => [e, `think-${i}`]), d.effort, `draft-effort-${scope}`, 'Thinking')),
      acts: btn('Save', 'check', 'save-model', scope, scope === 'chat' && S.draft.trim() ? '' : 'primary') + (scope === 'chat' && S.draft.trim() ? btn('Save and send', 'send', 'save-model-send', scope, 'primary') : '') });
  },

  fork(S, index) {
    const t = thread(S), upTo = t.messages.slice(0, Number(index) + 1).filter(m => !m.thinking);
    return sheet({ title: 'Fork from here', sub: `${plural(upTo.length, 'message')} carry over`,
      body: `<div class="msgs">${upTo.map(m => `<div class="msg${m.me ? ' me' : ''}">${markdown(m.text)}</div>`).join('')}</div>` +
        group(row({ icon: 'speed', title: 'Model', value: `${S.model} ${S.effort.toLowerCase()}`, act: 'sheet', arg: 'model|chat', opens: true })),
      acts: btn('Create the fork', 'fork', 'fork', index, 'primary') });
  },

  result(S, arg) {
    const [i, j] = arg.split('|').map(Number), r = thread(S).messages[i].results[j], s = S.sessions['Pi screen'];
    const body = r.kind === 'image' ? `<div class="picture live">${icon('photo', 36)}</div>` + facts([['Size', '1920 by 1080'], ['Taken', 'Today, 09:12']])
      : r.kind === 'file' ? `<div class="card">${markdown('Pi USB has 123 videos. Elements has 418 items and was last connected on Monday.')}</div>` + facts([['Kind', 'Text'], ['Size', '4 kB']])
      : r.kind === 'facts' ? facts([['Output', 'Pi screen'], ['State', s ? sessionWords(s) : 'Stopped'], ['Volume', s ? (s.volume === 0 ? 'Muted' : s.volume + '%') : 'Muted'], ['Position', s ? clock(s.at) : '0:00']])
      : group(playRows(S, r.title));
    return sheet({ title: r.title, sub: 'From the assistant', body,
      acts: r.kind === 'media' ? '' : btn('Copy', 'copy', 'toast', 'Copied') + (r.kind === 'facts' ? '' : btn('Save on this phone', 'download', 'toast', 'Saved', 'primary')) });
  },

  capture(S, id) {
    const c = S.captures.flatMap(d => d.items.map(i => ({ ...i, day: d.day }))).find(i => i.id === id), title = c.kind === 'Photo' ? 'Photo' : `Recording, ${c.length}`;
    return sheet({ title, sub: `${c.day}, ${c.when} · ${c.size}`, body: `<div class="picture live">${icon(c.kind === 'Photo' ? 'photo' : 'video', 36)}</div>` + group(
      row({ icon: 'screen', title: 'Show on Pi screen', off: !piUp(S), act: 'play', arg: `Pi screen|${title}` }) +
      row({ icon: 'download', title: 'Save on this phone', act: 'toast', arg: 'Saved' }) +
      row({ icon: 'share', title: 'Send to a device', act: 'attach-go', arg: `${c.kind === 'Photo' ? 'Image' : 'Video'}|${title}` }) +
      row({ icon: 'chat', title: 'Send to a conversation', act: 'sheet', arg: `to-chat|${title}`, opens: true }) +
      row({ icon: 'upload', title: 'Share with another app', act: 'toast', arg: 'Opened the Android share menu' }) +
      row({ icon: 'trash', danger: true, title: 'Delete', act: 'sheet', arg: `delete-capture|${id}` })) });
  },

  'delete-capture'(S, id) {
    return sheet({ title: 'Delete this capture?', sub: 'It is removed from the Pi.', body: '', acts: btn('Keep it', 'back', 'close-sheet') + btn('Delete', 'trash', 'delete-capture', id, 'danger') });
  },

  'share-note'(S) { return SHEETS.shareThing(S, S.notes.find(n => n.id === S.noteId).title, 'note'); },
  'share-pin'(S) { return SHEETS.shareThing(S, S.pins.find(p => p.id === S.pinId).title, 'pin'); },
  shareThing(S, title, what) {
    return sheet({ title: `Send this ${what}`, sub: title, body: group(
      row({ icon: 'share', title: 'To a device', sub: `Now ${S.recipient}`, act: 'attach-go', arg: `File|${title}` }) +
      row({ icon: 'chat', title: 'To a conversation', act: 'sheet', arg: `to-chat|${title}`, opens: true }) +
      row({ icon: 'upload', title: 'Share with another app', act: 'toast', arg: 'Opened the Android share menu' })) });
  },

  'delete-note'(S) {
    return sheet({ title: 'Delete this note?', sub: S.notes.find(n => n.id === S.noteId).title, body: '', acts: btn('Keep it', 'back', 'close-sheet') + btn('Delete', 'trash', 'delete-note', '', 'danger') });
  },
  'delete-pin'(S) {
    return sheet({ title: 'Delete this pin?', sub: S.pins.find(p => p.id === S.pinId).title, body: '', acts: btn('Keep it', 'back', 'close-sheet') + btn('Delete', 'trash', 'delete-pin', '', 'danger') });
  },

  custom(S) {
    return sheet({ title: 'Your own colour', body: `<input type="color" data-in="custom" value="${S.custom || '#8B5CF6'}" aria-label="Colour" style="width:100%;height:56px;border:0;background:none">`,
      acts: btn('Use this colour', 'check', 'use-custom', '', 'primary') });
  },

  power(S) {
    const low = S.power === 'low';
    return sheet({ title: 'Power', sub: !piUp(S) ? 'Offline' : low ? 'Low power' : 'Steady',
      body: (low ? notice('warn', 'The Pi is getting less power than it needs. Use the official power supply, or a powered hub for the drives.') : '') +
        facts([['Now', low ? 'Below 4.63 V' : '5.1 V'], ['Since it started', low ? 'Low 14 times' : 'Never low'], ['Slowed by heat', 'No'], low && ['Affects', 'Pi screen playback, drives']]),
      acts: btn('Check again', 'refresh', 'recheck', '', 'primary') });
  },

  service(S, id) {
    const up = piUp(S), name = { media: 'Media', assistant: 'Assistant', camera: 'Camera' }[id];
    const more = { media: [['Screen', up ? 'Connected' : 'Unknown'], ['Drives', S.drive === 'ok' ? '2 connected' : '1 of 2 connected']],
      assistant: [['Model', S.defaultModel], ['Tools', '13']], camera: [['Watching now', '0'], ['Captures', '28']] }[id];
    return sheet({ title: name, sub: up ? 'Ready' : 'Offline', body: facts([['Answered', up ? 'Just now' : 'Not since 14:02'], ...more]) });
  },

  update(S) {
    return sheet({ title: 'Update to 2.35', sub: 'From your Raspberry Pi', body: facts([['Installed', '2.34'], ['On the Pi', '2.35'], ['Size', '9.4 MB']]),
      acts: btn('Not now', 'back', 'close-sheet') + btn('Install', 'download', 'install', '', 'primary') });
  },

  app(S, name) {
    const a = BUSY_APPS.find(x => x.name === name);
    return sheet({ title: a.name, body: facts([['Memory', a.memory], ['Processor', a.cpu], ['Running for', '3 h 12 min']]) +
      group(row({ icon: 'stop', danger: true, title: `Stop ${a.name}`, sub: 'Unsaved work in it is lost', act: 'sheet', arg: `stop-app|${name}`, off: name === 'csync' })) });
  },

  'stop-app'(S, name) {
    return sheet({ title: `Stop ${name}?`, sub: 'Unsaved work in it is lost.', body: '', acts: btn('Leave it running', 'back', 'close-sheet') + btn(`Stop ${name}`, 'stop', 'toast', `${name} stopped`, 'danger') });
  }
};

function renderSheet(S) {
  if (!S.sheet) return '';
  const make = SHEETS[S.sheet.type];
  return make ? make(S, S.sheet.arg) : '';
}
