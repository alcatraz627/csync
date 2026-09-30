// Every sheet in the app. A sheet is a short choice, one value to adjust, a
// confirmation, or the facts about one row. Anything larger is a page.
// Like the screens, a sheet is built only from the parts in kit.js.

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
 * kind: video, audio, image, doc, text, link or folder. Every kind but a folder
 * can go to the Pi screen, a device, a conversation, a note and a pin.
 */
function itemActions(S, item) {
  const { kind, title } = item, up = piUp(S);
  const plays = ['video', 'audio', 'link'].includes(kind), shows = ['image', 'doc', 'text'].includes(kind);
  const first = [
    plays && playRows(S, title),
    shows && row({ icon: 'screen', title: 'Show on Pi screen', sub: up ? '' : 'The Pi is offline', off: !up, act: 'play', arg: `Pi screen|${title}|0|1|Shown` }),
    ['image', 'doc'].includes(kind) && !item.incoming && row({ icon: 'eye', title: 'Open', sub: 'Look at it here', act: 'sheet', arg: `view|${kind}|${title}`, opens: true }),
    kind === 'video' && !item.incoming && row({ icon: 'open', title: 'Open in VLC', sub: 'Hands the file to VLC on this phone', act: 'toast', arg: 'Opened in VLC' }),
    kind === 'image' && item.is !== 'export' && row({ icon: 'image', title: 'Set as the Pi cover', sub: up ? '' : 'The Pi is offline', off: !up, act: 'set-cover', arg: title }),
    kind === 'folder' && row({ icon: 'folder', title: 'Open', act: 'folder', arg: title }),
    kind === 'text' && row({ icon: 'copy', title: 'Copy the text', act: 'toast', arg: 'Copied' })
  ].filter(Boolean).join('');
  const rest = [
    row({ icon: 'devices', title: 'Send to a device', act: 'sheet', arg: `to-device|${kind}|${title}`, opens: true }),
    kind !== 'folder' && row({ icon: 'chat', title: 'Send to a conversation', act: 'sheet', arg: `to-chat|${kind}|${title}`, opens: true }),
    kind !== 'folder' && item.is !== 'note' && row({ icon: 'note', title: 'Add to a note', act: 'sheet', arg: `to-note|${kind}|${title}`, opens: true }),
    kind !== 'folder' && item.is !== 'pin' && row({ icon: 'pin', title: 'Save as a pin', act: 'toast', arg: 'Saved to Pins' }),
    !['text', 'link'].includes(kind) && !item.incoming && row({ icon: 'download', title: 'Save on this phone', sub: kind === 'folder' ? 'Everything inside it' : '', act: 'toast', arg: `Saving ${title}` }),
    !item.incoming && row({ icon: 'open', title: 'Share with another app', act: 'sheet', arg: `share-out|${title}`, opens: true }),
    item.details && row({ icon: 'info', title: 'File details', act: 'sheet', arg: `details|${title}`, opens: true }),
    item.remove && row({ icon: 'trash', danger: true, title: item.removeWords || 'Delete', act: 'sheet', arg: item.remove, opens: true })
  ].filter(Boolean).join('');
  return { first, rest, firstLabel: plays ? 'Play' : shows ? 'Show' : '', restLabel: first ? (item.incoming ? 'Keep or send' : 'Also') : '' };
}

function actionGroups(S, item) {
  const a = itemActions(S, item);
  return (a.first ? (a.firstLabel ? section(a.firstLabel, group(a.first)) : group(a.first)) : '') + (a.restLabel ? section(a.restLabel, group(a.rest)) : group(a.rest));
}

const actionSheet = (S, item, sub, top = '') => sheet({ title: item.title, sub, body: top + actionGroups(S, item) });

const kindOf = name => ({ Image: 'image', Video: 'video', Text: 'text', File: 'doc', Link: 'link', YouTube: 'link', Instagram: 'link' }[name] || name);
const splitItem = arg => { const [kind, ...rest] = arg.split('|'); return [kind, rest.join('|')]; };

function deviceRows(S, act) {
  return group(DEVICES.filter(d => !d.self).sort((a, b) => b.online - a.online).map(d =>
    row({ icon: deviceIcon(d), title: d.name, status: d.hub && !piUp(S) ? ['idle', 'Offline'] : deviceStatus(d), picked: d.name === S.recipient, act, arg: d.name })).join(''));
}

const percent = v => v === 0 ? 'Muted' : v + '%';
const exportName = S => `${thread(S).title}.${S.exportFormat === 'Image' ? 'png' : 'md'}`;

const SHEETS = {

  item(S, title) {
    const it = findItem(title);
    return actionSheet(S, { kind: it.kind, title, details: true }, [it.length, it.size].filter(Boolean).join(' · '));
  },

  details(S, title) {
    const it = findItem(title);
    return sheet({ title, sub: 'File details', body: facts([['File name', it.file || title], ['Kind', it.kind], it.length && ['Length', it.length], it.size && ['Size', it.size], ['Drive', S.source], ['Folder', it.folder || S.folder || 'Top level']]) });
  },

  view(S, arg) {
    const [kind, title] = splitItem(arg);
    return sheet({ title, sub: KIND_WORDS[kind], body: kind === 'image' ? picture({ icon: 'photo', size: 44, mode: 'live' })
      : card(markdown('## Setting up\n\nPut the projector on a level surface two metres from the wall.\n\n- HDMI 2 is the Pi\n- HDMI 1 is the laptop dock')) });
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
      body: '', acts: btn('Keep playing', 'back', 'close-sheet') + btn('Replace', 'play', 'play-now', arg, 'tonal') });
  },

  move(S, from) {
    const s = S.sessions[from], to = from === 'Pi screen' ? 'This phone' : 'Pi screen', up = piUp(S) || to === 'This phone';
    return sheet({ title: `Move to ${to === 'Pi screen' ? 'the Pi screen' : 'this phone'}`, sub: `${s.title} carries on from ${clock(s.at)}.`,
      body: up ? '' : notice('bad', 'The Pi is offline.'), acts: btn('Stay here', 'back', 'close-sheet') + btn('Move', to === 'Pi screen' ? 'screen' : 'device', 'move', from, 'tonal', up ? '' : 'disabled') });
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
    const [kind, title] = splitItem(arg), to = device(S, S.recipient), up = to.hub ? piUp(S) : to.online;
    return sheet({ title: 'Send to a device', sub: title, body: deviceRows(S, 'pick-recipient-stay') + (up ? '' : notice('warn', `${to.name} is offline and cannot receive anything now.`)),
      acts: btn(`Send to ${to.name}`, 'send', 'send-item', `${kind}|${title}`, 'primary', up ? '' : 'disabled') });
  },

  'to-chat'(S, arg) {
    const [kind, title] = splitItem(arg);
    return sheet({ title: 'Send to a conversation', sub: 'It is added to the message you write next. Nothing is sent yet.', body: group(
      S.threads.filter(t => !t.archived).map(t => row({ icon: 'chat', title: t.title, sub: day(t.when), act: 'attach-chat', arg: `${t.id}|${kind}|${title || 'Shared item'}`, opens: true })).join('') +
      row({ icon: 'plus', title: 'A new conversation', act: 'attach-chat', arg: `new|${kind}|${title || 'Shared item'}`, opens: true })) });
  },

  'to-note'(S, arg) {
    const [kind, title] = splitItem(arg);
    return sheet({ title: 'Add to a note', sub: title, body: group(
      S.notes.map(n => row({ icon: 'note', title: n.title, sub: n.edited, act: 'add-to-note', arg: `${n.id}|${kind}|${title}` })).join('') +
      row({ icon: 'plus', title: 'A new note', act: 'add-to-note', arg: `new|${kind}|${title}` })) });
  },

  'share-out'(S, title) {
    return sheet({ title: 'Share with another app', sub: title, body: appTiles(SHARE_APPS, 'shared-out') +
      noteLine('open', "This is Android's own share menu. csync hands over the item and its name.") });
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
    return sheet({ title: 'On the clipboard', sub: S.clip.sub, body: S.clip.kind === 'Image' ? picture({ icon: 'photo', mode: 'live' }) : card(esc(S.clip.body)),
      acts: btn('Add to message', 'clipboard', 'use-clip', '') + btn('Send', 'send', 'send-clip', '', 'primary', device(S, S.recipient).online ? '' : 'disabled') });
  },

  sent(S, index) {
    const t = S.sent[index];
    return sheet({ title: t.title, sub: t.ok ? 'Delivered' : 'Not delivered', body: facts([['Kind', t.kind], ['To', t.to], ['When', `${t.when}${t.time ? ', ' + t.time : ''}`]]),
      acts: btn('Send again', 'refresh', 'resend', index, t.ok ? '' : 'primary') });
  },

  received(S, index) {
    const r = S.received[index];
    return actionSheet(S, { kind: kindOf(r.kind), title: r.title }, `From ${r.from} · ${day(r.when)}, ${r.time}`, r.body ? card(esc(r.body)) : '');
  },

  volume(S, output) {
    const v = S.sessions[output].volume;
    return sheet({ title: 'Volume', sub: output === 'Pi screen' ? 'Pi screen' : 'This phone', body: range({ id: 'volume', label: 'Volume', shown: percent(v), value: v, min: 0, max: 100, step: 5, low: 'Muted', high: '100%', arg: output, live: true }) });
  },

  speed(S, output) {
    const v = S.sessions[output].speed;
    return sheet({ title: 'Speed', sub: output === 'Pi screen' ? 'Pi screen' : 'This phone', body: range({ id: 'speed', label: 'Speed', shown: v + '×', value: v, min: 0.5, max: 2, step: 0.25, low: '0.5×', high: '2×', arg: output, live: true }) });
  },

  skip(S, output) {
    const now = output === 'default' ? S.defaults.skip : S.sessions[output].skip;
    return sheet({ title: 'Skip length', sub: 'For both Back and Forward', body: group([5, 10, 15, 30, 60].map(n => row({ icon: 'skip', title: `${n} seconds`, picked: n === now, act: 'set-skip', arg: `${output}|${n}` })).join('')) });
  },

  'start-volume'(S) {
    const v = S.defaults.startVolume;
    return sheet({ title: 'Starting volume', sub: 'On the Pi screen', body: range({ id: 'startVolume', label: 'Starting volume', shown: percent(v), value: v, min: 0, max: 100, step: 5, low: 'Muted', high: '100%', live: true }) });
  },

  youtube(S) {
    return sheet({ title: 'A link', sub: 'Plays on the Pi screen',
      body: field({ id: 'ytLink', hint: 'Paste a YouTube link', value: S.ytLink, icon: 'link' }) + noteLine('open', 'From YouTube or Instagram, use Share and choose Send to Pi screen.'),
      acts: btn('Play on Pi screen', 'screen', 'play-link', '', 'tonal', S.ytLink.trim() ? '' : 'disabled') });
  },

  cast(S, what) {
    if (what === 'app') {
      return sheet({ title: 'Show one app', sub: 'On the Pi screen', body: appTiles(PHONE_APPS, 'cast-app') +
        noteLine('eye', 'Only that app is shown. Notifications and the rest of this phone stay private.') });
    }
    return sheet({ title: "Show this phone's screen", sub: 'On the Pi screen',
      body: notice('info', 'Everything on this phone is shown, notifications too. Android asks before it starts.') +
        facts([['Picture', 'Up to 1080p'], ['Sound', 'Stays on this phone'], ['Needs', 'The same network as the Pi']]),
      acts: btn('Not now', 'back', 'close-sheet') + btn('Start', 'screen', 'cast-screen', '', 'tonal') });
  },

  covers(S) {
    const f = S.framing[S.cover] || { fit: 'Cover', rotate: 0, crop: 'Full' }, at = Math.max(0, COVERS.indexOf(S.cover));
    return sheet({ title: 'Cover image', sub: `${S.cover}, shown when nothing is playing`, body:
      framedPicture(COVER_ART[at] || COVER_ART[0], f, ['screen', 'On the Pi screen']) +
      coverGrid(COVERS, COVER_ART, S.cover, 'cover') +
      labelled('Fit', seg([['Cover', 'expand'], ['Contain', 'fit'], ['Stretch', 'screen']], f.fit, 'frame-fit', 'Fit')) +
      labelled('Crop', seg([['Full', 'image'], ['Center', 'crop'], ['Top', 'up']], f.crop, 'frame-crop', 'Crop'), 'The image file is never changed.') +
      group(row({ icon: 'rotate', title: 'Rotate', value: `${f.rotate}°`, act: 'frame-turn' })) +
      btns(btn('Add an image', 'plus', 'toast', 'Choose an image from this phone'), btn('Clear framing', 'refresh', 'frame-clear', '', 'quiet')) });
  },

  display(S) {
    const now = DISPLAYS.find(d => d.name === S.display);
    return sheet({ title: 'Display', sub: 'What the Pi is plugged into', body:
      group(DISPLAYS.map(d => row({ icon: 'screen', title: d.name, sub: d.connected ? `${d.size}, ${d.port}` : `Last seen ${d.seen}`, picked: d.name === S.display, off: !d.connected, act: 'pick-display', arg: d.name })).join('')) +
      facts([['Picture', now.size], ['Turned', `${now.rotate}°`], ['Sound', now.sound], ['Starts', now.volume === 0 ? 'Muted' : `At ${now.volume}%`]]) +
      noteLine('info', 'Each display keeps its own size, turn, sound and cover framing. A new one appears here when it is plugged in.') });
  },

  slideshow(S) {
    const folders = Object.entries(LIBRARY).map(([name, items]) => [name || 'Top level', items.filter(i => i.kind === 'image').length]).filter(([, n]) => n);
    return sheet({ title: 'Photos as a slideshow', sub: `From ${S.source}`, body: group(folders.map(([name, n]) =>
      row({ icon: 'folder', title: name, sub: plural(n, 'image'), act: 'play', arg: `Pi screen|Photos in ${name}|0|1|Slideshow` })).join('')) });
  },

  'show-note'(S) {
    return sheet({ title: 'Show a note', sub: 'On the Pi screen', body: group(S.notes.map(n => row({ icon: 'note', title: n.title, sub: n.edited, act: 'play', arg: `Pi screen|${n.title}|0|1|Shown` })).join('')) });
  },

  'chat-add'(S) {
    return sheet({ title: 'Add to this message', body: group(
      row({ icon: 'photo', title: 'An image', sub: 'The assistant can look at it', act: 'attach-chat-file', arg: 'Image|IMG 4410.jpg' }) +
      row({ icon: 'file', title: 'A file', sub: 'Kept on the Pi', act: 'attach-chat-file', arg: 'File|quote.pdf' }) +
      row({ icon: 'camera', title: 'A photo from the Pi camera', sub: piUp(S) ? 'Taken now' : 'The Pi is offline', off: !piUp(S), act: 'attach-chat-file', arg: 'Image|Pi camera photo' }) +
      row({ icon: 'clipboard', title: 'The clipboard', sub: S.clip.sub, act: 'attach-chat-file', arg: `${S.clip.kind}|Clipboard ${S.clip.kind.toLowerCase()}` })) });
  },

  'export-chat'(S) {
    const image = S.exportFormat === 'Image';
    return sheet({ title: 'Save this conversation', sub: exportName(S), body:
      labelled('Save as', seg([['Markdown', 'markdown'], ['Image', 'image']], S.exportFormat, 'export-format', 'Save as'),
        image ? 'One tall picture of the whole conversation, as it looks here.' : 'Text you can edit. What the assistant found is listed under each reply.') +
      actionGroups(S, { kind: image ? 'image' : 'doc', title: exportName(S), is: 'export' }) });
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
      body: msgs(upTo.map((m, i) => bubble(m, i, false, false)).join('')) +
        group(row({ icon: 'think-2', title: 'Model', value: `${S.model} ${S.effort.toLowerCase()}`, act: 'sheet', arg: 'model|chat', opens: true })),
      acts: btn('Create the fork', 'fork', 'fork', index, 'primary') });
  },

  result(S, arg) {
    const [i, j] = arg.split('|').map(Number), m = thread(S).messages[i], r = m.results[j];
    if (r.kind === 'media') return actionSheet(S, { kind: 'video', title: r.title }, `The assistant started it at ${m.when}`);
    if (r.kind === 'image') return actionSheet(S, { kind: 'image', title: r.title }, `From the assistant, ${m.when}`, picture({ icon: 'photo', mode: 'live' }));
    if (r.kind === 'file') return actionSheet(S, { kind: 'doc', title: r.title }, r.sub, card(markdown('Pi USB has 6 videos. Elements has 418 items and was last connected on Monday.')));
    if (r.kind === 'note') return sheet({ title: r.title, sub: r.sub, body: card(markdown(NOTES[1].body)) + group(row({ icon: 'note', title: 'Open in Notes', act: 'open-note', arg: 'n2', opens: true })) });
    return sheet({ title: r.title, sub: `From the assistant, ${m.when}`, body: facts(r.facts), acts: btn('Copy', 'copy', 'toast', 'Copied') });
  },

  tools() {
    return sheet({ title: 'What the assistant can use', body: ASSISTANT_TOOLS.map(g => section(g.group, defs(g.tools))).join('') });
  },

  capture(S, id) {
    const c = S.captures.flatMap(d => d.items.map(i => ({ ...i, day: d.day }))).find(i => i.id === id), title = c.kind === 'Photo' ? 'Photo' : `Recording, ${c.length}`;
    return actionSheet(S, { kind: c.kind === 'Photo' ? 'image' : 'video', title, remove: `delete-capture|${id}` }, `${c.day}, ${c.when} · ${c.size}`, picture({ icon: c.kind === 'Photo' ? 'photo' : 'video', mode: 'live' }));
  },

  'delete-capture'(S, id) {
    return sheet({ title: 'Delete this capture?', sub: 'It is removed from the Pi.', body: '', acts: btn('Keep it', 'back', 'close-sheet') + btn('Delete', 'trash', 'delete-capture', id, 'danger') });
  },

  'share-note'(S) { return actionSheet(S, { kind: 'text', is: 'note', title: S.notes.find(n => n.id === S.noteId).title }, 'Note'); },
  'share-pin'(S) { const p = S.pins.find(x => x.id === S.pinId); return actionSheet(S, { kind: p.link ? 'link' : 'text', is: 'pin', title: p.title }, 'Pin'); },

  'note-item'(S, index) {
    const it = S.notes.find(n => n.id === S.noteId).items[index];
    return actionSheet(S, { kind: it.kind, title: it.title, is: 'note', remove: `drop-note-item|${index}`, removeWords: 'Take out of this note' }, `${KIND_WORDS[it.kind]}, in this note`);
  },

  'drop-note-item'(S, index) {
    const it = S.notes.find(n => n.id === S.noteId).items[index];
    return sheet({ title: 'Take it out of this note?', sub: `${it.title} stays where it came from.`, body: '', acts: btn('Keep it', 'back', 'close-sheet') + btn('Take out', 'trash', 'drop-note-item', index, 'danger') });
  },

  'note-add'(S) {
    const add = (symbol, title, sub, arg, off = false) => row({ icon: symbol, title, sub, off, act: 'note-add', arg });
    return sheet({ title: 'Add to this note', body: group(
      add('photo', 'An image', 'From this phone', 'image|IMG 4410.jpg') +
      add('video', 'A video', 'From this phone', 'video|VID 2026-09-26.mp4') +
      add('file', 'A file', 'Any document', 'doc|quote.pdf') +
      add('media', 'Something from Media', 'A file on the Pi drives', 'video|Adjustable bend', !piUp(S)) +
      add('camera', 'A photo from the Pi camera', piUp(S) ? 'Taken now' : 'The Pi is offline', 'image|Pi camera photo', !piUp(S)) +
      add('clipboard', 'The clipboard', S.clip.sub, `${kindOf(S.clip.kind)}|Clipboard ${S.clip.kind.toLowerCase()}`)) });
  },

  'delete-note'(S) {
    return sheet({ title: 'Delete this note?', sub: S.notes.find(n => n.id === S.noteId).title, body: '', acts: btn('Keep it', 'back', 'close-sheet') + btn('Delete', 'trash', 'delete-note', '', 'danger') });
  },
  'delete-pin'(S) {
    return sheet({ title: 'Delete this pin?', sub: S.pins.find(p => p.id === S.pinId).title, body: '', acts: btn('Keep it', 'back', 'close-sheet') + btn('Delete', 'trash', 'delete-pin', '', 'danger') });
  },

  custom(S) {
    const c = S.customDraft || S.custom || '#8B5CF6', r = whiteOn(c);
    return sheet({ title: 'Your own colour', body: swatchBig(c) +
      range({ id: 'hue', label: 'Hue', shown: 'Hue', value: hueOf(c), min: 0, max: 359, hue: true }) +
      labelled('Colour code', field({ id: 'hex', hint: '#8B5CF6', value: c, icon: 'palette' })) +
      status(r >= 4.5 ? 'good' : 'warn', r >= 4.5 ? `White text reads well on it, ${r.toFixed(1)} to 1` : `White text is hard to read on it, ${r.toFixed(1)} to 1`),
      acts: btn('Use this colour', 'check', 'use-custom', '', 'tonal') });
  },

  power(S) {
    const low = S.power === 'low';
    return sheet({ title: 'Power', sub: !piUp(S) ? 'Offline' : low ? 'Low power' : 'Ready',
      body: (low ? notice('warn', 'The Pi is getting less power than it needs. Use the official power supply, or a powered hub for the drives.') : '') +
        facts([['Now', low ? 'Below 4.63 V' : '5.1 V'], ['Since it started', low ? 'Low 14 times' : 'Never low'], ['Slowed by heat', 'No'], low && ['Affects', 'Pi screen playback, drives']]),
      acts: btn('Check again', 'refresh', 'recheck', '') });
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
    const w = WIDGETS.find(x => x.name === name), added = S.widgets.includes(name), placed = ['Launcher widget', 'Quick Settings tile'].includes(w.kind);
    const where = placed ? 'Updates' : 'Where';
    return sheet({ title: w.name, sub: w.kind, body: picture({ icon: w.icon }) + facts([['Does', w.shows], [where, w.updates]]),
      acts: !placed ? '' : added ? btn('Remove', 'trash', 'widget-toggle', name, 'danger') : btn('Add', 'plus', 'widget-toggle', name, 'tonal') });
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
