// Every sheet in the app. A sheet is a short choice, one value to adjust, a
// confirmation, or the facts about one row. Anything larger is a page.

const findItem = title => [...Object.values(LIBRARY).flat(), ...VIDEOS].find(i => i.title === title) || { kind: 'video', title, file: title, size: '' };
const outputWords = output => output === 'Pi screen' ? 'Pi screen' : 'this phone';

/** Rows that start playback, with the output named in the words of each one. */
function playRows(S, title, verb = 'Play') {
  return ['Pi screen', 'This phone'].map(output => {
    const now = S.sessions[output], pi = output === 'Pi screen', symbol = pi ? 'screen' : 'device';
    if (now && now.title === title) return row({ icon: symbol, title: `${sessionWords(now)} on ${outputWords(output)}`, sub: 'Open the player', act: 'go', arg: OUTPUT_PAGE[output], opens: true });
    if (pi && !piUp(S)) return row({ icon: symbol, title: `${verb} on Pi screen`, sub: 'The Pi is offline', off: true });
    const sub = now ? `Replaces ${now.title}` : pi ? (S.defaults.startVolume === 0 ? 'Starts muted' : `Starts at ${S.defaults.startVolume}%`) : 'Speaker, headphones or a wired screen';
    return row({ icon: symbol, title: `${verb} on ${outputWords(output)}`, sub, act: 'play', arg: `${output}|${title}` });
  }).join('');
}

/**
 * What one kind of item can do. Every sheet and the From another app page draw
 * from this list, so the same item offers the same actions wherever it appears.
 * kind: video, audio, image, doc, text, link or folder.
 */
function itemActions(S, item) {
  const { kind, title } = item, up = piUp(S);
  const plays = ['video', 'audio', 'link'].includes(kind);
  const first = [
    plays && playRows(S, title),
    kind === 'video' && row({ icon: 'open', title: 'Open in VLC', sub: 'Hands the file to VLC on this phone', act: 'toast', arg: 'Opened in VLC' }),
    kind === 'image' && row({ icon: 'screen', title: 'Show on Pi screen', sub: up ? '' : 'The Pi is offline', off: !up, act: 'play', arg: `Pi screen|${title}` }),
    kind === 'image' && row({ icon: 'image', title: 'Set as the Pi cover', sub: up ? '' : 'The Pi is offline', off: !up, act: 'set-cover', arg: title }),
    kind === 'folder' && row({ icon: 'folder', title: 'Open', act: 'folder', arg: title }),
    kind === 'text' && row({ icon: 'copy', title: 'Copy the text', act: 'toast', arg: 'Copied' })
  ].filter(Boolean).join('');
  const rest = [
    !['text', 'link'].includes(kind) && row({ icon: 'download', title: 'Save on this phone', sub: kind === 'folder' ? 'Everything inside it' : '', act: 'toast', arg: `Saving ${title}` }),
    row({ icon: 'devices', title: 'Send to a device', act: 'sheet', arg: `to-device|${kind}|${title}`, opens: true }),
    kind !== 'folder' && row({ icon: 'chat', title: 'Send to a conversation', act: 'sheet', arg: `to-chat|${kind}|${title}`, opens: true }),
    ['image', 'text', 'link'].includes(kind) && item.is !== 'note' && row({ icon: 'note', title: 'Add to a note', act: 'toast', arg: 'Added to a new note' }),
    ['text', 'link'].includes(kind) && item.is !== 'pin' && row({ icon: 'pin', title: 'Save as a pin', act: 'toast', arg: 'Saved to Pins' }),
    row({ icon: 'open', title: 'Share with another app', act: 'toast', arg: 'Opened the Android share menu' }),
    item.details && row({ icon: 'info', title: 'File details', act: 'sheet', arg: `details|${title}`, opens: true }),
    item.remove && row({ icon: 'trash', danger: true, title: 'Delete', act: 'sheet', arg: item.remove, opens: true })
  ].filter(Boolean).join('');
  return { first, rest, firstLabel: plays ? 'Play' : kind === 'image' ? 'Show' : '', restLabel: first ? 'Also' : '' };
}

function actionGroups(S, item) {
  const a = itemActions(S, item);
  return (a.first ? (a.firstLabel ? section(a.firstLabel, group(a.first)) : group(a.first)) : '') + (a.restLabel ? section(a.restLabel, group(a.rest)) : group(a.rest));
}

const actionSheet = (S, item, sub, lead = '') => sheet({ title: item.title, sub, body: lead + actionGroups(S, item) });

const kindOf = name => ({ Image: 'image', Video: 'video', Text: 'text', File: 'doc', Link: 'link', YouTube: 'link', Instagram: 'link' }[name] || name);

function deviceRows(S, act) {
  return group(DEVICES.filter(d => !d.self).sort((a, b) => b.online - a.online).map(d =>
    row({ icon: deviceIcon(d), title: d.name, status: d.hub && !piUp(S) ? ['idle', 'Offline'] : deviceStatus(d), picked: d.name === S.recipient, act, arg: d.name })).join(''));
}

const slider = (name, label, value, min, max, step, shown, low, high, output = '') =>
  `<div class="labelled"><span data-live="${name}">${shown}</span><input class="range" type="range" min="${min}" max="${max}" step="${step}" value="${value}" data-in="${name}" data-arg="${esc(output)}" aria-label="${label}"><div class="range-ends"><span>${low}</span><span>${high}</span></div></div>`;

const SHEETS = {

  item(S, title) {
    const it = findItem(title);
    return actionSheet(S, { kind: it.kind, title, details: true }, [it.length, it.size].filter(Boolean).join(' · '));
  },

  details(S, title) {
    const it = findItem(title);
    return sheet({ title, sub: 'File details', body: facts([['File name', it.file || title], ['Kind', it.kind], it.length && ['Length', it.length], it.size && ['Size', it.size], ['Drive', S.source], ['Folder', it.folder || S.folder || 'Top level']]) });
  },

  folder(S, name) {
    const f = (LIBRARY[''] || []).find(i => i.title === name) || { count: 0 };
    return actionSheet(S, { kind: 'folder', title: name }, `Folder, ${plural(f.count, 'item')}`);
  },

  resume(S, index) {
    const h = HISTORY[index], up = piUp(S), other = h.output === 'Pi screen' ? 'This phone' : 'Pi screen';
    const can = o => o === 'This phone' || up;
    const why = o => can(o) ? `From ${clock(h.at)}` : 'The Pi is offline';
    return sheet({ title: h.title, sub: `${h.source} · ${left(h)}`, body: group(
      row({ icon: 'play', title: `Resume on ${outputWords(h.output)}`, sub: why(h.output), off: !can(h.output), act: 'play', arg: `${h.output}|${h.title}|${h.at}|${h.total}|${h.source}` }) +
      row({ icon: 'rewind', title: `Start over on ${outputWords(h.output)}`, sub: can(h.output) ? '' : 'The Pi is offline', off: !can(h.output), act: 'play', arg: `${h.output}|${h.title}|0|${h.total}|${h.source}` }) +
      row({ icon: other === 'Pi screen' ? 'screen' : 'device', title: `Resume on ${outputWords(other)}`, sub: why(other), off: !can(other), act: 'play', arg: `${other}|${h.title}|${h.at}|${h.total}|${h.source}` })) });
  },

  replace(S, arg) {
    const [output, title] = arg.split('|'), now = S.sessions[output];
    return sheet({ title: `Replace what is on ${output === 'Pi screen' ? 'the Pi screen' : 'this phone'}?`, sub: `${now.title} stops and ${title} starts.`,
      body: '', acts: btn('Keep playing', 'back', 'close-sheet') + btn('Replace', 'play', 'play-now', arg, 'primary') });
  },

  move(S, from) {
    const s = S.sessions[from], to = from === 'Pi screen' ? 'This phone' : 'Pi screen', up = piUp(S) || to === 'This phone';
    return sheet({ title: `Move to ${to === 'Pi screen' ? 'the Pi screen' : 'this phone'}`, sub: `${s.title} carries on from ${clock(s.at)}.`,
      body: up ? '' : notice('bad', 'The Pi is offline.'), acts: btn('Stay here', 'back', 'close-sheet') + btn('Move', to === 'Pi screen' ? 'screen' : 'device', 'move', from, 'primary', up ? '' : 'disabled') });
  },

  source(S) {
    const gone = S.drive !== 'ok', up = piUp(S);
    return sheet({ title: 'Choose a source', body: group(
      row({ icon: 'files', title: 'Pi USB', status: up ? ['good', 'Connected'] : ['idle', 'Offline'], picked: S.source === 'Pi USB', off: !up, act: 'pick-source', arg: 'Pi USB' }) +
      row({ icon: 'files', title: 'Elements', status: !up ? ['idle', 'Offline'] : gone ? ['idle', 'Disconnected'] : ['good', 'Connected'], picked: S.source === 'Elements', off: !up || gone, act: 'pick-source', arg: 'Elements' }) +
      row({ icon: 'device', title: 'This phone', sub: 'Files stored here', picked: S.source === 'This phone', act: 'pick-source', arg: 'This phone' })) });
  },

  recipient(S) { return sheet({ title: 'Send to', body: deviceRows(S, 'pick-recipient') }); },

  'to-device'(S, arg) {
    const [kind, ...rest] = arg.split('|'), title = rest.join('|'), to = device(S, S.recipient), up = to.hub ? piUp(S) : to.online;
    return sheet({ title: 'Send to a device', sub: title, body: deviceRows(S, 'pick-recipient-stay') + (up ? '' : notice('warn', `${to.name} is offline and cannot receive anything now.`)),
      acts: btn(`Send to ${to.name}`, 'send', 'send-item', `${kind}|${title}`, 'primary', up ? '' : 'disabled') });
  },

  'to-chat'(S, arg) {
    const [kind, ...rest] = arg.split('|'), title = rest.join('|') || 'Shared item';
    return sheet({ title: 'Send to a conversation', sub: 'It is added to the message you write next. Nothing is sent yet.', body: group(
      S.threads.filter(t => !t.archived).map(t => row({ icon: 'chat', title: t.title, sub: day(t.when), act: 'attach-chat', arg: `${t.id}|${kind}|${title}`, opens: true })).join('') +
      row({ icon: 'plus', title: 'A new conversation', act: 'attach-chat', arg: `new|${kind}|${title}`, opens: true })) });
  },

  device(S, name) {
    const d = device(S, name), up = d.hub ? piUp(S) : d.online;
    const kind = { pi: 'Raspberry Pi', laptop: 'Laptop', desktop: 'Desktop', device: 'Phone or tablet' }[d.kind];
    return sheet({ title: d.name, sub: up ? 'Online' : 'Offline',
      body: facts([['Kind', kind], ['Address', d.address], !up && ['Last seen', d.seen || 'Today'], d.hub && ['Runs', 'Media, assistant, camera, notes']]) +
        group(row({ icon: 'send', title: `Send to ${d.name}`, off: !up, sub: up ? '' : 'It is offline', act: 'pick-recipient-go', arg: d.name, opens: true }) +
          (d.hub ? row({ icon: 'tools', title: 'Check the Pi', act: 'go', arg: 'tools', opens: true }) : row({ icon: 'trash', danger: true, title: 'Forget this device', act: 'sheet', arg: `forget|${d.name}`, opens: true }))) });
  },

  forget(S, name) {
    return sheet({ title: `Forget ${name}?`, sub: 'It leaves your list until it is seen again.', body: '', acts: btn('Keep it', 'back', 'close-sheet') + btn('Forget', 'trash', 'toast', `${name} forgotten`, 'danger') });
  },

  attach() {
    return sheet({ title: 'Attach a file', sub: 'From this phone', body: group(
      [['IMG 4410.jpg', 'Image', 'Photo, 1.8 MB'], ['VID 2026-09-26.mp4', 'Video', 'Video, 64 MB'], ['quote.pdf', 'File', 'Document, 220 kB']].map(([t, k, s]) =>
        row({ icon: KIND_ICON[k], title: t, sub: s, act: 'attach', arg: `${k}|${t}` })).join('')) });
  },

  clipboard(S) {
    const shown = S.clip.kind === 'Image' ? `<div class="picture live">${icon('photo', 36)}</div>` : `<div class="card">${esc(S.clip.body)}</div>`;
    return sheet({ title: 'On the clipboard', sub: S.clip.sub, body: shown,
      acts: btn('Add to message', 'clipboard', 'use-clip', '') + btn('Send', 'send', 'send-clip', '', 'primary', device(S, S.recipient).online ? '' : 'disabled') });
  },

  sent(S, index) {
    const t = S.sent[index];
    return sheet({ title: t.title, sub: t.ok ? 'Delivered' : 'Not delivered', body: facts([['Kind', t.kind], ['To', t.to], ['When', `${t.when}${t.time ? ', ' + t.time : ''}`]]),
      acts: btn('Send again', 'refresh', 'resend', index, t.ok ? '' : 'primary') });
  },

  received(S, index) {
    const r = S.received[index];
    return actionSheet(S, { kind: kindOf(r.kind), title: r.title }, `From ${r.from} · ${day(r.when)}, ${r.time}`, r.body ? `<div class="card">${esc(r.body)}</div>` : '');
  },

  volume(S, output) {
    const v = S.sessions[output].volume;
    return sheet({ title: 'Volume', sub: output === 'Pi screen' ? 'Pi screen' : 'This phone', body: slider('volume', 'Volume', v, 0, 100, 5, v === 0 ? 'Muted' : v + '%', 'Muted', '100%', output) });
  },

  speed(S, output) {
    const v = S.sessions[output].speed;
    return sheet({ title: 'Speed', sub: output === 'Pi screen' ? 'Pi screen' : 'This phone', body: slider('speed', 'Speed', v, 0.5, 2, 0.25, v + '×', '0.5×', '2×', output) });
  },

  skip(S, output) {
    const now = output === 'default' ? S.defaults.skip : S.sessions[output].skip;
    return sheet({ title: 'Skip length', sub: 'For both Back and Forward', body: group([5, 10, 15, 30, 60].map(n => row({ icon: 'skip', title: `${n} seconds`, picked: n === now, act: 'set-skip', arg: `${output}|${n}` })).join('')) });
  },

  'start-volume'(S) {
    const v = S.defaults.startVolume;
    return sheet({ title: 'Starting volume', sub: 'On the Pi screen', body: slider('startVolume', 'Starting volume', v, 0, 100, 5, v === 0 ? 'Muted' : v + '%', 'Muted', '100%') });
  },

  youtube(S) {
    return sheet({ title: 'A YouTube link', sub: 'Plays on the Pi screen',
      body: field({ id: 'ytLink', hint: 'Paste the link', value: S.ytLink, icon: 'link' }) + `<p class="note-line">${icon('open', 14)}From the YouTube app, use Share and choose csync.</p>`,
      acts: btn('Play on Pi screen', 'screen', 'play-link', '', 'primary', S.ytLink.trim() ? '' : 'disabled') });
  },

  'chat-add'(S) {
    return sheet({ title: 'Add to this message', body: group(
      row({ icon: 'photo', title: 'An image', sub: 'The assistant can look at it', act: 'attach-chat-file', arg: 'Image|IMG 4410.jpg' }) +
      row({ icon: 'file', title: 'A file', sub: 'Kept on the Pi', act: 'attach-chat-file', arg: 'File|quote.pdf' }) +
      row({ icon: 'think-2', title: 'Model', value: `${S.model} ${S.effort.toLowerCase()}`, act: 'sheet', arg: 'model|chat', opens: true })) });
  },

  model(S, scope) {
    const d = S.modelDraft || { model: scope === 'default' ? S.defaultModel : S.model, effort: scope === 'default' ? S.defaultEffort : S.effort };
    const owner = MODELS.find(m => m.models.includes(d.model)) || MODELS[0];
    const lists = MODELS.map(m => section(m.available ? m.provider : `${m.provider}, not set up on this Pi`, group(m.models.map(name =>
      row({ icon: m.icon, title: name, picked: name === d.model, off: !m.available, act: 'draft-model', arg: `${scope}|${name}` })).join('')))).join('');
    const send = scope === 'chat' && S.draft.trim();
    return sheet({ title: scope === 'default' ? 'Model for new conversations' : 'Model for this conversation', body: lists +
      labelled(`Thinking, for ${d.model}`, seg(owner.efforts.map((e, i) => [e, `think-${i}`]), d.effort, `draft-effort-${scope}`, 'Thinking')),
      acts: btn('Save', 'check', 'save-model', scope, send ? '' : 'primary') + (send ? btn('Save and send', 'send', 'save-model-send', scope, 'primary') : '') });
  },

  fork(S, index) {
    const t = thread(S), upTo = t.messages.slice(0, Number(index) + 1).filter(m => !m.thinking);
    return sheet({ title: 'Fork from here', sub: `${plural(upTo.length, 'message')} carry over`,
      body: `<div class="msgs">${upTo.map(m => `<div class="msg${m.me ? ' me' : ''}">${markdown(m.text)}</div>`).join('')}</div>` +
        group(row({ icon: 'think-2', title: 'Model', value: `${S.model} ${S.effort.toLowerCase()}`, act: 'sheet', arg: 'model|chat', opens: true })),
      acts: btn('Create the fork', 'fork', 'fork', index, 'primary') });
  },

  result(S, arg) {
    const [i, j] = arg.split('|').map(Number), m = thread(S).messages[i], r = m.results[j];
    if (r.kind === 'media') return actionSheet(S, { kind: 'video', title: r.title }, `The assistant started it at ${m.when}`);
    const body = r.kind === 'image' ? `<div class="picture live">${icon('photo', 36)}</div>` + facts([['Size', '1920 by 1080'], ['Taken', `Today, ${m.when}`]])
      : r.kind === 'file' ? `<div class="card">${markdown('Pi USB has 6 videos. Elements has 418 items and was last connected on Monday.')}</div>` + facts([['Kind', 'Text'], ['Size', '4 kB']])
      : facts([['Read at', m.when], ['Output', 'Pi screen'], ['State', 'Playing'], ['Volume', 'Muted'], ['Position', '0:04']]);
    return sheet({ title: r.title, sub: 'From the assistant', body,
      acts: btn('Copy', 'copy', 'toast', 'Copied') + (r.kind === 'facts' ? '' : btn('Save on this phone', 'download', 'toast', 'Saved', 'primary')) });
  },

  tools() {
    return sheet({ title: 'What the assistant can use', body: ASSISTANT_TOOLS.map(g => section(g.group, `<div class="group defs">${g.tools.map(([name, does]) => `<p><b>${esc(name)}</b><span>: ${esc(does)}</span></p>`).join('')}</div>`)).join('') });
  },

  capture(S, id) {
    const c = S.captures.flatMap(d => d.items.map(i => ({ ...i, day: d.day }))).find(i => i.id === id), title = c.kind === 'Photo' ? 'Photo' : `Recording, ${c.length}`;
    return actionSheet(S, { kind: c.kind === 'Photo' ? 'image' : 'video', title, remove: `delete-capture|${id}` }, `${c.day}, ${c.when} · ${c.size}`, `<div class="picture live">${icon(c.kind === 'Photo' ? 'photo' : 'video', 36)}</div>`);
  },

  'delete-capture'(S, id) {
    return sheet({ title: 'Delete this capture?', sub: 'It is removed from the Pi.', body: '', acts: btn('Keep it', 'back', 'close-sheet') + btn('Delete', 'trash', 'delete-capture', id, 'danger') });
  },

  'share-note'(S) { return actionSheet(S, { kind: 'text', is: 'note', title: S.notes.find(n => n.id === S.noteId).title }, 'Note'); },
  'share-pin'(S) { const p = S.pins.find(x => x.id === S.pinId); return actionSheet(S, { kind: p.link ? 'link' : 'text', is: 'pin', title: p.title }, 'Pin'); },

  'delete-note'(S) {
    return sheet({ title: 'Delete this note?', sub: S.notes.find(n => n.id === S.noteId).title, body: '', acts: btn('Keep it', 'back', 'close-sheet') + btn('Delete', 'trash', 'delete-note', '', 'danger') });
  },
  'delete-pin'(S) {
    return sheet({ title: 'Delete this pin?', sub: S.pins.find(p => p.id === S.pinId).title, body: '', acts: btn('Keep it', 'back', 'close-sheet') + btn('Delete', 'trash', 'delete-pin', '', 'danger') });
  },

  custom(S) {
    const c = S.customDraft || S.custom || '#8B5CF6', r = whiteOn(c);
    return sheet({ title: 'Your own colour', body:
      `<div class="swatch-big" style="background:${c}">${icon('check', 22)}<span>Sample</span></div>` +
      labelled('Hue', `<input class="range hue" type="range" min="0" max="359" value="${hueOf(c)}" data-in="hue" aria-label="Hue">`) +
      labelled('Colour code', field({ id: 'hex', hint: '#8B5CF6', value: c, icon: 'palette' })) +
      status(r >= 4.5 ? 'good' : 'warn', r >= 4.5 ? `White text reads well on it, ${r.toFixed(1)} to 1` : `White text is hard to read on it, ${r.toFixed(1)} to 1`),
      acts: btn('Use this colour', 'check', 'use-custom', '', 'primary') });
  },

  power(S) {
    const low = S.power === 'low';
    return sheet({ title: 'Power', sub: !piUp(S) ? 'Offline' : low ? 'Low power' : 'Ready',
      body: (low ? notice('warn', 'The Pi is getting less power than it needs. Use the official power supply, or a powered hub for the drives.') : '') +
        facts([['Now', low ? 'Below 4.63 V' : '5.1 V'], ['Since it started', low ? 'Low 14 times' : 'Never low'], ['Slowed by heat', 'No'], low && ['Affects', 'Pi screen playback, drives']]),
      acts: btn('Check again', 'refresh', 'recheck', '', 'primary') });
  },

  service(S, id) {
    const up = piUp(S), name = { media: 'Media', assistant: 'Assistant', camera: 'Camera' }[id];
    const more = { media: [['Screen', up ? 'Connected' : 'Not known'], ['Drives', S.drive === 'ok' ? '2 connected' : '1 of 2 connected']],
      assistant: [['Model', S.defaultModel], ['Tools', '13']], camera: [['Watching now', '0'], ['Captures', '4']] }[id];
    return sheet({ title: name, sub: up ? 'Ready' : 'Offline', body: facts([['Answered', up ? 'Just now' : 'Not since 14:02'], ...more]) });
  },

  update() {
    return sheet({ title: 'Update to 2.35', sub: 'From your Raspberry Pi', body: facts([['Installed', '2.34'], ['On the Pi', '2.35'], ['Size', '9.4 MB']]),
      acts: btn('Not now', 'back', 'close-sheet') + btn('Install', 'download', 'install', '', 'primary') });
  },

  widget(S, name) {
    const w = WIDGETS.find(x => x.name === name), added = S.widgets.includes(name);
    return sheet({ title: w.name, sub: w.kind, body: `<div class="picture">${icon(w.icon, 36)}</div>` + facts([['Shows', w.shows], ['Updates', w.updates]]),
      acts: added ? btn('Remove', 'trash', 'widget-toggle', name, 'danger') : btn('Add', 'plus', 'widget-toggle', name, 'primary') });
  },

  app(S, name) {
    const a = BUSY_APPS.find(x => x.name === name);
    return sheet({ title: a.name, body: facts([['Memory', a.memory], ['Processor', a.cpu], ['Last hour', a.trend], ['Running for', '3 h 12 min']]) +
      group(row({ icon: 'stop', danger: true, title: `Stop ${a.name}`, sub: 'Unsaved work in it is lost', act: 'sheet', arg: `stop-app|${name}`, off: name === 'csync', opens: true })) });
  },

  'stop-app'(S, name) {
    return sheet({ title: `Stop ${name}?`, sub: 'Unsaved work in it is lost.', body: '', acts: btn('Leave it', 'back', 'close-sheet') + btn('Stop', 'stop', 'toast', `${name} stopped`, 'danger') });
  }
};

function renderSheet(S) {
  if (!S.sheet) return '';
  const make = SHEETS[S.sheet.type];
  return make ? make(S, S.sheet.arg) : '';
}
