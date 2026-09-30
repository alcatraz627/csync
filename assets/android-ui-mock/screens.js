// One entry per place in the map. `actions` fills the right of the top bar,
// `body` fills the page. Both read the state and change nothing, and both are
// built only from the parts in kit.js: check.js fails a screen that draws its own.

const piUp = S => S.pi === 'online';
const active = S => Object.entries(S.sessions).filter(([, s]) => s).map(([output, s]) => ({ output, ...s }));
const device = (S, name) => DEVICES.find(d => d.name === name);
const left = h => `${clock(h.total - h.at)} left`;
const thread = S => S.threads.find(t => t.id === S.threadId);
const hubState = S => !piUp(S) ? ['idle', S.pi === 'checking' ? 'Checking the Raspberry Pi' : 'Raspberry Pi is offline']
  : S.power === 'low' ? ['warn', 'Raspberry Pi is online, power is low'] : ['good', 'Raspberry Pi is online'];

/** The one way every screen says the Pi is away, with the one place that can fix it. */
const offlineNotice = S => piUp(S) ? '' : notice('info', 'The Raspberry Pi cannot be reached. What is saved on this phone still works.', btn('Open Connection', 'wifi', 'go', 'connection'));

const INCOMING = {
  Video: { kind: 'video', icon: 'video', title: 'VID 2026-09-26.mp4', from: 'Gallery' },
  Image: { kind: 'image', icon: 'photo', title: 'IMG 4410.jpg', from: 'Photos' },
  YouTube: { kind: 'link', icon: 'video', title: 'F-Droid 2.0, the biggest update in years', from: 'YouTube' },
  Instagram: { kind: 'link', icon: 'video', title: 'A reel from Instagram', from: 'Instagram' },
  File: { kind: 'doc', icon: 'file', title: 'quote.pdf', from: 'Files' }
};

const KIND_WORDS = { image: 'Image', video: 'Video', audio: 'Sound', doc: 'File', text: 'Text', link: 'Link' };
const longDraft = S => S.draft.split('\n').length > 1 || S.draft.length > 60;

const SCREENS = {

  home: {
    actions: () => ibtn('search', 'Search', 'go', 'search'),
    body(S) {
      const [tone, words] = hubState(S), up = piUp(S);
      const issue = up && S.power === 'low' ? notice('warn', 'Playback on the Pi screen may stop while power is low.', btn('Open Tools', 'tools', 'go', 'tools')) : '';

      const resume = HISTORY[0], chat = S.threads.find(t => !t.archived), blocked = !up && resume.output === 'Pi screen';
      const pickup = group(
        row({ icon: 'history', title: resume.title, sub: `${resume.output} · ${left(resume)}`, progress: resume.at / resume.total,
          act: 'sheet', arg: 'resume|0', off: blocked,
          trailing: ibtn('play', `Resume on ${resume.output}`, 'resume', '0', 'go', 17, blocked ? 'disabled' : '') }) +
        (chat ? row({ icon: 'chat', title: chat.title, sub: `Conversation · ${day(chat.when)}`, act: 'open-thread', arg: chat.id, opens: true }) : ''));

      const online = DEVICES.filter(d => d.online && !d.self && !d.hub).length, screenBusy = S.sessions['Pi screen'], away = ['idle', 'Offline'];
      const caps = [
        { icon: 'media', title: 'Media', to: 'media', s: up ? (S.drive === 'ok' ? ['good', plural(VIDEOS.length, 'video')] : ['warn', 'One drive missing']) : away },
        { icon: 'chat', title: 'Chat', to: 'chat', s: up ? ['good', 'Ready'] : away },
        { icon: 'share', title: 'Share', to: 'share', s: online ? ['good', plural(online, 'device') + ' online'] : ['idle', 'No device online'] },
        { icon: 'screen', title: 'Pi screen', to: 'pi-screen', s: !up ? away : screenBusy ? [sessionTone(screenBusy), sessionWords(screenBusy)] : ['idle', 'Showing the cover'] },
        { icon: 'camera', title: 'Pi camera', to: 'camera', s: up ? ['good', 'Ready'] : away },
        { icon: 'note', title: 'Notes', to: 'notes', s: up ? ['good', `${plural(S.notes.length, 'note')}, ${plural(S.pins.length, 'pin')}`] : away },
        { icon: 'tools', title: 'Tools', to: 'tools', s: !up ? away : S.power === 'low' ? ['warn', 'Low power'] : ['good', 'Ready'] }
      ];
      const rank = { good: 0, warn: 1, idle: 2, bad: 3 };
      caps.sort((a, b) => rank[a.s[0]] - rank[b.s[0]]);

      const devices = group(DEVICES.filter(d => !d.self).sort((a, b) => b.online - a.online).map(d => {
        const st = d.hub ? [tone, !up ? 'Offline' : S.power === 'low' ? 'Low power' : 'Online'] : deviceStatus(d);
        return row({ icon: deviceIcon(d), title: d.name, status: st, act: 'sheet', arg: `device|${d.name}`, opens: true });
      }).join(''));

      return lead(tone, words) + issue + offlineNotice(S) +
        section('Pick up', pickup, 'pickup', S.folded.pickup) +
        section('Capabilities', tiles(caps.map(c => tile({ icon: c.icon, title: c.title, status: c.s, act: 'go', arg: c.to })).join('')), 'caps', S.folded.caps) +
        section('Devices', devices, 'devices', S.folded.devices);
    }
  },

  search: {
    body(S) {
      const q = S.searchQuery.trim().toLowerCase(), scope = S.view.search;
      const all = [
        ...VIDEOS.map(v => ({ scope: 'Media', icon: 'video', title: v.title, sub: `Video in ${v.folder}`, act: 'sheet', arg: `item|${v.title}` })),
        ...S.threads.map(t => ({ scope: 'Chats', icon: 'chat', title: t.title, sub: `Conversation · ${day(t.when)}`, act: 'open-thread', arg: t.id })),
        ...S.notes.map(n => ({ scope: 'Notes', icon: 'note', title: n.title, sub: 'Note', act: 'open-note', arg: n.id })),
        ...S.pins.map(p => ({ scope: 'Notes', icon: 'pin', title: p.title, sub: 'Pin', act: 'open-pin', arg: p.id })),
        ...DEVICES.filter(d => !d.self).map(d => ({ scope: 'Devices', icon: deviceIcon(d), title: d.name, status: d.hub && !piUp(S) ? ['idle', 'Offline'] : deviceStatus(d), act: 'sheet', arg: `device|${d.name}` }))
      ];
      const hits = q ? all.filter(r => (scope === 'All' || r.scope === scope) && `${r.title} ${r.sub || ''}`.toLowerCase().includes(q)) : [];
      const results = !q ? empty('search', 'Search everything you can reach', 'Media, conversations, notes, pins and devices.')
        : hits.length ? section(plural(hits.length, 'result'), group(hits.map(r => row({ ...r, opens: true })).join('')))
        : empty('search', `Nothing matches "${S.searchQuery.trim()}"`, scope === 'All' ? '' : `Searched in ${scope}.`, scope === 'All' ? '' : btn('Search everything', 'search', 'view', 'search|All'));
      return field({ id: 'searchQuery', hint: 'Search media, chats, notes and devices', value: S.searchQuery, icon: 'search' }) +
        seg([['All', 'all'], ['Media', 'media'], ['Chats', 'chat'], ['Notes', 'note'], ['Devices', 'devices']], scope, 'view-search', 'Search in') +
        (piUp(S) ? '' : notice('info', 'The Pi is offline, so results come from what this phone has saved.', btn('Open Connection', 'wifi', 'go', 'connection'))) + results;
    }
  },

  media: {
    actions: S => ibtn('search', 'Search this source', 'toggle', 'mediaSearch', S.mediaSearch ? 'on' : '') + ibtn('source', 'Switch source', 'sheet', 'source'),
    body(S) {
      const view = S.view.media, up = piUp(S), drive = S.drive === 'ok', q = S.mediaQuery.trim().toLowerCase();
      const phoneSource = S.source === 'This phone';
      const browsing = view === 'Files' && !q && (up || phoneSource) && !(S.source === 'Elements' && !drive);
      const scope = browsing ? pathLine([[S.source, 'folder', '', phoneSource ? 'device' : 'files'], ...(S.folder ? [[S.folder, '', '', 'folder']] : [])])
        : view === 'Files' || q ? noteLine(phoneSource ? 'device' : 'files', phoneSource ? 'Browsing this phone' : `Browsing ${S.source}`) : '';
      const top = (S.mediaSearch ? field({ id: 'mediaQuery', hint: `Search ${phoneSource ? 'this phone' : S.source}`, value: S.mediaQuery, icon: 'search' }) : '') +
        seg([['Files', 'files'], ['Videos', 'video'], ['History', 'history'], ['Access', 'access']], view, 'view-media', 'Media views') + scope;
      const itemRow = (it, sub) => row({ icon: KIND_ICON[it.kind], title: it.title, sub, act: 'sheet', arg: `${it.kind === 'folder' ? 'folder' : 'item'}|${it.title}`, opens: true });
      let content = '';

      if (view === 'History') {
        content = section('Continue', group(HISTORY.map((h, i) => {
          const missing = h.source === 'Elements' && !drive, blocked = (h.output === 'Pi screen' && !up) || missing;
          return row({ icon: 'history', title: h.title, sub: missing ? 'Elements is disconnected' : `${h.output} · ${left(h)}`,
            progress: h.at / h.total, act: 'sheet', arg: `resume|${i}`, opens: true, off: blocked });
        }).join(''))) + (up ? '' : notice('info', 'Your place in each item is kept on this phone. Items on the Pi screen resume when the Pi is back.', btn('Open Connection', 'wifi', 'go', 'connection')));
      } else if (!up && !phoneSource) {
        content = offlineNotice(S) + section('Still here', group(
          row({ icon: 'device', title: 'This phone', sub: 'Files stored here', act: 'pick-source', arg: 'This phone', opens: true }) +
          row({ icon: 'history', title: 'History', sub: 'Your place in everything you played', act: 'view', arg: 'media|History', opens: true })));
      } else if (view === 'Access') {
        content = section('Open the drives from a computer', group(DRIVES.map(d => {
          const gone = d.name === 'Elements' && !drive;
          return ['SMB', 'FTP'].map(way => { const address = d[way.toLowerCase()]; return row({ icon: 'access', title: `${d.name} over ${way}`, sub: gone ? 'Disconnected' : address, off: gone, act: 'copy', arg: address, trailing: ibtn('copy', `Copy the ${d.name} ${way} address`, 'copy', address, 'quiet', 18, gone ? 'disabled' : '') }); }).join('');
        }).join(''))) +
        section('Drives', group(DRIVES.map(d => {
          const gone = d.name === 'Elements' && !drive;
          return row({ icon: 'files', title: d.name, sub: gone ? '' : plural(d.items, 'item'), status: gone ? ['idle', 'Disconnected'] : ['good', 'Connected'], act: gone ? '' : 'pick-source', arg: d.name, opens: !gone });
        }).join('')));
      } else if (S.source === 'Elements' && !drive) {
        content = notice('warn', 'Elements is disconnected. Your place in its films is kept.', btn('Open History', 'history', 'view', 'media|History')) +
          section('Other sources', group(row({ icon: 'files', title: 'Pi USB', status: ['good', 'Connected'], act: 'pick-source', arg: 'Pi USB', opens: true })));
      } else if (q) {
        const everything = Object.entries(LIBRARY).flatMap(([folder, items]) => items.map(i => ({ ...i, folder: folder || 'Top level' })));
        const hits = everything.filter(i => `${i.title} ${i.file || ''}`.toLowerCase().includes(q) && (view !== 'Videos' || i.kind === 'video'));
        content = hits.length ? section(`${plural(hits.length, 'match', 'matches')} in ${S.source}`, group(hits.map(i => itemRow(i, `${i.kind === 'folder' ? 'Folder' : i.folder}${i.length ? ' · ' + i.length : ''}`)).join('')))
          : empty('search', `Nothing in ${S.source} matches "${S.mediaQuery.trim()}"`, '', btn('Search everything', 'search', 'go', 'search'));
      } else if (view === 'Videos') {
        content = section(`${plural(VIDEOS.length, 'video')} on every connected drive`, group(VIDEOS.map(v => itemRow(v, `${v.folder} · ${v.length}`)).join('')));
      } else {
        const here = LIBRARY[S.folder] || [], folders = here.filter(i => i.kind === 'folder'), files = here.filter(i => i.kind !== 'folder');
        content = (folders.length ? section('Folders', group(folders.map(f => row({ icon: 'folder', title: f.title, sub: plural(f.count, 'item'), act: 'folder', arg: f.title, opens: true,
            trailing: ibtn('download', `Save or send the folder ${f.title}`, 'sheet', `folder|${f.title}`, 'quiet', 18) })).join(''))) : '') +
          (files.length ? section('Files', group(files.map(f => itemRow(f, f.length ? `${f.length} · ${f.size}` : f.size)).join(''))) : '') +
          (!here.length ? empty('folder', 'This folder is empty', '', btn(`Up to ${S.source}`, 'up', 'folder', '')) : '');
      }
      return top + content;
    }
  },

  'pi-screen': {
    actions: S => S.sessions['Pi screen'] && !S.sessions['Pi screen'].live ? ibtn('device', 'Move to this phone', 'sheet', 'move|Pi screen') : '',
    body(S) {
      const s = S.sessions['Pi screen'];
      if (!piUp(S)) return head('Pi screen', status('idle', 'Offline')) + offlineNotice(S);
      if (s) {
        const fromPhone = s.source === 'This phone';
        return head(s.title, status(sessionTone(s), `${sessionWords(s)} on Pi screen`)) +
          picture({ icon: fromPhone ? 'device' : s.live ? 'image' : 'video', size: 40, mode: 'live', loading: s.busy, tag: ['screen', 'On the Pi screen'] }) +
          (fromPhone ? noteLine('eye', 'What is on this phone is on the Pi screen until you stop.') : '') +
          (s.error ? notice('bad', s.error, btn('Try again', 'refresh', 'p-pause', 'Pi screen')) : '') +
          (S.power === 'low' ? notice('warn', 'Power is low. The picture may stop.', btn('Open Tools', 'tools', 'go', 'tools')) : '') +
          player(s, 'Pi screen');
      }
      return head('Nothing is playing', status('idle', 'Showing the cover')) +
        picture({ icon: 'image', mode: 'idle', tag: ['image', S.cover] }) +
        section('From the Pi', group(
          row({ icon: 'photo', title: 'Photos as a slideshow', sub: 'Every image in a folder, in turn', act: 'sheet', arg: 'slideshow', opens: true }) +
          row({ icon: 'camera', title: 'The Pi camera', sub: 'Live picture', act: 'show-camera', arg: '' }))) +
        section('From this phone', group(
          row({ icon: 'device', title: "This phone's screen", sub: 'Everything you see, live', act: 'sheet', arg: 'cast|screen', opens: true }) +
          row({ icon: 'launcher', title: 'One app', sub: 'Only that app is shown', act: 'sheet', arg: 'cast|app', opens: true }) +
          row({ icon: 'link', title: 'A link', sub: 'YouTube, or share a video from another app', act: 'sheet', arg: 'youtube', opens: true }) +
          row({ icon: 'note', title: 'A note', sub: 'Shown large, easy to read across a room', act: 'sheet', arg: 'show-note', opens: true }))) +
        section('This screen', group(
          row({ icon: 'image', title: 'Cover image', sub: 'Shown when nothing is playing', value: S.cover, act: 'sheet', arg: 'covers', opens: true }) +
          row({ icon: 'screen', title: 'Display', value: DISPLAYS.find(d => d.name === S.display).name, act: 'sheet', arg: 'display', opens: true })));
    }
  },

  'phone-player': {
    actions: S => S.sessions['This phone'] ? ibtn('expand', 'Full screen', 'full', 'on') + ibtn('screen', 'Move to the Pi screen', 'sheet', 'move|This phone') : '',
    body(S) {
      const s = S.sessions['This phone'];
      if (!s) return empty('device', 'Nothing is playing on this phone', 'Choose something in Media and pick Play on this phone. The last thing played is under Pick up on Home.', '');
      return head(s.title, status(sessionTone(s), `${sessionWords(s)} on this phone`)) +
        picture({ icon: 'video', size: 40, mode: 'live', loading: s.busy, tag: ['device', 'On this phone'] }) +
        (s.error ? notice('bad', s.error, btn('Try again', 'refresh', 'p-pause', 'This phone')) : '') +
        player(s, 'This phone');
    }
  },

  share: {
    actions: () => ibtn('devices', 'Choose who receives', 'sheet', 'recipient') + ibtn('download', 'Received', 'go', 'received'),
    body(S) {
      const to = device(S, S.recipient), ready = to.online && (S.shareText.trim() || S.attachment);
      const failed = S.failed ? notice('bad', `${S.failed} was not delivered to ${S.recipient}. It is still attached.`, btn('Send again', 'refresh', 'send', '')) : '';
      const offline = to.online ? '' : notice('warn', `${to.name} is offline and cannot receive anything now.`, btn('Choose another device', 'devices', 'sheet', 'recipient'));
      const attach = S.attachment
        ? row({ icon: KIND_ICON[S.attachment.kind] || 'file', title: S.attachment.title, sub: 'Attached', trailing: ibtn('trash', 'Remove the attachment', 'detach', '', 'quiet', 18) })
        : row({ icon: 'file', title: 'Attach a file', sub: 'A photo, a video or a document', act: 'sheet', arg: 'attach', opens: true });
      const history = S.sent.length
        ? group(S.sent.map((t, i) => row({ icon: KIND_ICON[t.kind], title: t.title, sub: `${t.to} · ${day(t.when)}`, status: t.ok ? ['good', 'Delivered'] : ['bad', 'Failed'], act: 'sheet', arg: `sent|${i}`, opens: true })).join(''))
        : empty('send', 'Nothing sent yet', 'What you send from this phone is listed here.', btn('Attach a file', 'file', 'sheet', 'attach'));
      return group(row({ icon: deviceIcon(to), title: `Send to ${to.name}`, status: deviceStatus(to), act: 'sheet', arg: 'recipient', opens: true })) + offline + failed +
        field({ id: 'shareText', hint: 'Write a message', value: S.shareText, icon: 'text', tall: true }) +
        group(attach + row({ icon: 'clipboard', title: 'Use the clipboard', sub: S.clip.sub, act: 'sheet', arg: 'clipboard', opens: true })) +
        btns(btn('Send', 'send', 'send', '', 'primary wide', ready ? '' : 'disabled')) +
        section('Sent from this phone', history);
    }
  },

  received: {
    body(S) {
      return S.received.length
        ? section(plural(S.received.length, 'item'), group(S.received.map((r, i) => row({ icon: KIND_ICON[r.kind], title: r.title, sub: `${r.from} · ${day(r.when)}`, act: 'sheet', arg: `received|${i}`, opens: true })).join('')))
        : empty('download', 'Nothing received yet', 'What other devices send to this phone is listed here.', btn('Check this phone can receive', 'wifi', 'go', 'connection'));
    }
  },

  incoming: {
    body(S) {
      const it = INCOMING[S.view.incoming], plays = ['video', 'link'].includes(it.kind), o = S.incomingOptions;
      const options = plays ? section('How it plays',
        group(row({ icon: 'loop', title: 'Loop', trailing: toggle(o.loop === 'On', 'in-loop', 'Loop') })) +
        range({ id: 'in-speed', label: 'Speed', shown: `Speed, ${o.speed}×`, value: o.speed, min: 0.5, max: 2, step: 0.25 }) +
        range({ id: 'in-volume', label: 'Volume', shown: o.volume === 0 ? 'Volume, muted' : `Volume, ${o.volume}%`, value: o.volume, min: 0, max: 100, step: 5, help: 'These start the way you last played.' })) : '';
      return head('Where should it go?') +
        group(row({ icon: it.icon, title: it.title, sub: S.view.incoming === 'Instagram' ? 'From Instagram. It is saved to the Pi first, then played.' : `From ${it.from}` })) +
        (plays ? offlineNotice(S) : '') + actionGroups(S, { kind: it.kind, title: it.title, incoming: true }) + options;
    }
  },

  chat: {
    actions: S => ibtn('search', 'Search conversations', 'toggle', 'chatSearch', S.chatSearch ? 'on' : '') +
      ibtn('think-2', 'Model for new conversations', 'sheet', 'model|default', 'quiet') +
      ibtn('plus', 'New chat', 'new-thread', '', '', 21, piUp(S) ? '' : 'disabled'),
    body(S) {
      const view = S.view.chat;
      const state = S.pi === 'online' ? ['good', 'The Pi assistant is online'] : S.pi === 'checking' ? ['warn', 'Checking the Pi assistant'] : ['idle', 'The Pi assistant is offline'];
      const top = lead(...state) + offlineNotice(S) +
        seg([['All', 'all'], ['Favorites', 'favorite'], ['Archived', 'archive'], ['Tools', 'clipboard']], view, 'view-chat', 'Conversation views');
      if (view === 'Tools') return top + ASSISTANT_TOOLS.map(g => section(g.group, defs(g.tools))).join('');
      const q = S.chatQuery.trim().toLowerCase();
      const rows = S.threads.filter(t => (view === 'Archived' ? t.archived : !t.archived) && (view !== 'Favorites' || t.favorite) && (!q || t.title.toLowerCase().includes(q)));
      const showAll = btn('Show all conversations', 'all', 'view', 'chat|All');
      const none = q ? empty('search', `No conversation matches "${S.chatQuery.trim()}"`, '', btn('Search everything', 'search', 'go', 'search'))
        : view === 'Favorites' ? empty('favorite', 'No favorites yet', 'Open a conversation and tap the heart to keep it here.', showAll)
        : view === 'Archived' ? empty('archive', 'Nothing archived', 'Archived conversations leave the main list and wait here.', showAll)
        : empty('chat', 'No conversations yet', 'Ask the Pi assistant to find, play or check something.', btn('New chat', 'plus', 'new-thread', '', 'tonal', piUp(S) ? '' : 'disabled'));
      return top + (S.chatSearch ? field({ id: 'chatQuery', hint: 'Search conversations', value: S.chatQuery, icon: 'search' }) : '') +
        (rows.length ? section(view === 'All' ? 'Recent' : view, group(rows.map(t => row({ icon: 'chat', title: t.title, sub: `${t.when} · ${plural(t.count, 'message')}`, act: 'open-thread', arg: t.id, opens: true })).join(''))) : none);
    }
  },

  conversation: {
    actions: S => thread(S).messages.length ? ibtn('download', 'Save this conversation', 'sheet', 'export-chat') : '',
    body(S) {
      const t = thread(S), started = t.messages.length > 0;
      const keep = started ? ibtn('favorite', t.favorite ? 'Remove from favorites' : 'Add to favorites', 'fav-thread', '', t.favorite ? 'on' : 'quiet', 18) + ibtn('archive', t.archived ? 'Take out of the archive' : 'Archive', 'arch-thread', '', t.archived ? 'on' : 'quiet', 18) : '';
      const said = t.messages.filter(m => !m.thinking).length;
      const line = started ? plural(said, 'message') + (Number.isFinite(t.tokens) ? ` · ${compact(t.tokens)} tokens` : '') : '';
      const top = convoHead({ title: t.title, editing: S.editingTitle, line, actions: ibtn('edit', 'Edit the title', 'edit-title', '', 'quiet', 18) + keep });
      const flow = t.messages.map((m, i) => m.thinking ? thinking()
        : bubble(m, i, S.pickedMsg === i) + (m.results || []).map((r, j) => resultCard(r, `${i}|${j}`, S.sessions[r.output])).join('')).join('');
      return top + (piUp(S) ? '' : notice('info', 'The Pi assistant is offline. You can read this conversation. Sending waits for the Pi.', btn('Open Connection', 'wifi', 'go', 'connection'))) +
        (started ? msgs(flow) : empty('chat', 'Ask the Pi assistant', 'It can find and play media, check the Pi and keep notes.', btn('See what it can use', 'clipboard', 'sheet', 'tools')));
    },
    composer(S) {
      return composer({ draft: S.draft, tall: S.draftOpen, height: S.draftHeight, long: longDraft(S), attachment: S.chatAttachment,
        model: `${S.model} ${S.effort.toLowerCase()}`, ready: Boolean(S.draft.trim() || S.chatAttachment), canSend: piUp(S) });
    }
  },

  more: {
    body(S) {
      const up = piUp(S), toolState = !up ? ['idle', 'Offline'] : S.power === 'low' ? ['warn', 'Low power'] : ['good', 'Ready'];
      return section('On the Pi', group(
        row({ icon: 'camera', title: 'Pi camera', sub: 'Live picture, photos and recordings', act: 'go', arg: 'camera', opens: true }) +
        row({ icon: 'note', title: 'Notes', sub: `${plural(S.notes.length, 'note')} and ${plural(S.pins.length, 'pin')}`, act: 'go', arg: 'notes', opens: true }))) +
        section('Looking after things', group(
          row({ icon: 'tools', title: 'Tools', sub: 'Pi health, this phone, updates', status: toolState, act: 'go', arg: 'tools', opens: true }) +
          row({ icon: 'settings', title: 'Settings', sub: 'How the app connects, plays and looks', act: 'go', arg: 'settings', opens: true }))) +
        section('Reference', group(
          row({ icon: 'help', title: 'Assistant guide', sub: 'What you can ask the Pi assistant', act: 'go', arg: 'guide', opens: true }) +
          row({ icon: 'info', title: 'Help and about', sub: 'Version 2.34', act: 'go', arg: 'help', opens: true }) +
          row({ icon: 'palette', title: 'Design system', sub: 'Every part this app is built from', act: 'go', arg: 'showcase', opens: true })));
    }
  },

  camera: {
    body(S) {
      const up = piUp(S), connecting = up && S.camera === 'connecting', ready = up && !connecting;
      const st = !up ? ['idle', 'Offline'] : connecting ? ['warn', 'Connecting'] : S.recording ? ['good', 'Recording, 0:18'] : ['good', 'Live'];
      const view = picture({ icon: 'camera', mode: ready ? 'live' : '', loading: connecting, tag: ready && S.recording ? ['record', 'Recording'] : null });
      return lead(...st) + view + offlineNotice(S) + shoot(ready, S.recording) +
        group(row({ icon: 'photo', title: 'Captures', sub: plural(S.captures.reduce((n, d) => n + d.items.length, 0), 'photo and recording', 'photos and recordings'), act: 'go', arg: 'captures', opens: true }) +
          row({ icon: 'screen', title: 'Show on Pi screen', sub: ready ? 'The live picture' : '', off: !ready, act: 'show-camera' }));
    }
  },

  captures: {
    body(S) {
      const days = S.captures.filter(d => d.items.length);
      if (!days.length) return empty('photo', 'No captures yet', 'Photos and recordings from the Pi camera are kept here.', btn('Open the camera', 'camera', 'go', 'camera'));
      return days.map(d => section(d.day, group(d.items.map(c => row({ icon: c.kind === 'Photo' ? 'photo' : 'video', title: c.kind === 'Photo' ? 'Photo' : `Recording, ${c.length}`, sub: `${c.when} · ${c.size}`, act: 'sheet', arg: `capture|${c.id}`, opens: true })).join('')))).join('');
    }
  },

  notes: {
    actions: S => ibtn('search', 'Search notes and pins', 'toggle', 'notesSearch', S.notesSearch ? 'on' : '') +
      (S.view.notes === 'Notes' ? ibtn('plus', 'New note', 'new-note', '', '', 21) : ibtn('plus', 'New pin', 'new-pin', '', '', 21)),
    body(S) {
      const view = S.view.notes, q = S.noteQuery.trim().toLowerCase(), everywhere = btn('Search everything', 'search', 'go', 'search');
      const top = seg([['Notes', 'note'], ['Pins', 'pin']], view, 'view-notes', 'Notes or pins') +
        (S.notesSearch ? field({ id: 'noteQuery', hint: `Search ${view.toLowerCase()}`, value: S.noteQuery, icon: 'search' }) : '');
      if (view === 'Notes') {
        const rows = S.notes.filter(n => !q || `${n.title} ${n.body}`.toLowerCase().includes(q));
        return top + (rows.length ? group(rows.map(n => row({ icon: 'note', title: n.title, sub: n.edited, value: n.items.length ? plural(n.items.length, 'item') : '', act: 'open-note', arg: n.id, opens: true })).join(''))
          : q ? empty('search', `No note matches "${S.noteQuery.trim()}"`, '', everywhere)
          : empty('note', 'No notes yet', 'Notes are kept on the Pi and the assistant can read them.', btn('New note', 'plus', 'new-note', '', 'tonal')));
      }
      const rows = S.pins.filter(p => !q || `${p.title} ${p.link || p.text} ${p.tags.join(' ')}`.toLowerCase().includes(q));
      return top + (rows.length ? group(rows.map(p => row({ icon: p.link ? 'link' : 'text', title: p.title, sub: p.link ? new URL(p.link).host : 'Text', value: p.tags.length ? plural(p.tags.length, 'tag') : '', act: 'open-pin', arg: p.id, opens: true })).join(''))
        : q ? empty('search', `No pin matches "${S.noteQuery.trim()}"`, '', everywhere)
        : empty('pin', 'No pins yet', 'Save a link or a snippet to find it again.', btn('New pin', 'plus', 'new-pin', '', 'tonal')));
    }
  },

  note: {
    actions: () => ibtn('open', 'Send or share this note', 'sheet', 'share-note') + ibtn('trash', 'Delete this note', 'sheet', 'delete-note', 'quiet'),
    body(S) {
      const n = S.notes.find(x => x.id === S.noteId), mode = S.view.note, editing = mode !== 'Preview';
      const modes = seg([['Preview', 'eye'], ['Rich', 'edit'], ['Plain', 'markdown']], mode, 'view-note', 'How to see this note');
      const kept = n.items.length ? section('In this note', group(n.items.map((it, i) => row({ icon: KIND_ICON[it.kind], title: it.title, sub: KIND_WORDS[it.kind], act: 'sheet', arg: `note-item|${i}`, opens: true })).join(''))) : '';
      if (!editing) return head(n.title, n.edited) + modes + (n.body.trim() ? card(markdown(n.body)) : '') + kept +
        (n.body.trim() || n.items.length ? '' : empty('note', 'This note is empty', 'Write in Rich or Plain, or add a picture, a video or a file.'));
      const text = mode === 'Rich' ? richEditor(markdown(n.body), 'Note, formatted') : editor('noteBody', n.body, 'Note, as Markdown');
      return labelled('Title', field({ id: 'noteTitle', hint: 'Title', value: n.title, icon: 'note' })) + modes + text + kept +
        btns(btn('Save', 'check', 'save-note', '', 'primary'), btn('Add to this note', 'plus', 'sheet', 'note-add'));
    }
  },

  pin: {
    actions: () => ibtn('open', 'Send or share this pin', 'sheet', 'share-pin') + ibtn('trash', 'Delete this pin', 'sheet', 'delete-pin', 'quiet'),
    body(S) {
      const p = S.pins.find(x => x.id === S.pinId);
      return labelled(p.link != null && !p.text ? 'Link' : 'Text', field({ id: 'pinBody', hint: 'A link or some text', value: p.link || p.text || '', icon: p.link ? 'link' : 'text', tall: !p.link })) +
        labelled('Title', field({ id: 'pinTitle', hint: 'Title', value: p.title, icon: 'pin' })) +
        labelled('Tags', field({ id: 'pinTags', hint: 'Separate tags with commas', value: p.tags.join(', '), icon: 'tag' })) +
        labelled('About', field({ id: 'pinAbout', hint: 'Why you kept it', value: p.about, icon: 'text', tall: true })) +
        btns(btn('Save', 'check', 'save-pin', '', 'primary'), p.link ? btn('Open the link', 'link', 'toast', 'Opened in the browser') : '');
    }
  },

  tools: {
    actions: () => ibtn('refresh', 'Check again', 'recheck'),
    body(S) {
      const up = piUp(S), low = S.power === 'low', gone = S.drive !== 'ok';
      const state = !up ? ['idle', 'The Raspberry Pi is offline'] : low ? ['warn', 'Power is low'] : gone ? ['warn', 'One drive is disconnected'] : ['good', 'Everything is ready'];
      const svc = (title, symbol, id) => row({ icon: symbol, title, status: up ? ['good', 'Ready'] : ['idle', 'Offline'], act: 'sheet', arg: `service|${id}`, opens: true });
      return lead(...state) + offlineNotice(S) +
        section('Raspberry Pi', group(
          svc('Media', 'media', 'media') + svc('Assistant', 'chat', 'assistant') + svc('Camera', 'camera', 'camera') +
          row({ icon: 'power', title: 'Power', status: !up ? ['idle', 'Offline'] : low ? ['warn', 'Low power'] : ['good', 'Ready'], act: 'sheet', arg: 'power', opens: true }) +
          row({ icon: 'files', title: 'Drives', status: !up ? ['idle', 'Offline'] : gone ? ['warn', '1 of 2 connected'] : ['good', '2 connected'], act: 'view', arg: 'media|Access', opens: true }))) +
        section('This phone', group(
          row({ icon: 'cpu', title: 'Process monitor', sub: 'Memory, processor, temperature', act: 'go', arg: 'process', opens: true }) +
          row({ icon: 'launcher', title: 'Widgets', sub: 'Widgets, tiles, shortcuts and the share menu', act: 'go', arg: 'widgets', opens: true }))) +
        section('This app', group(S.update
          ? row({ icon: 'download', title: 'Update to 2.35', sub: up ? 'Waiting on the Pi' : 'The Pi is offline', act: 'sheet', arg: 'update', opens: true, off: !up })
          : row({ icon: 'check', title: 'csync 2.35', sub: 'Up to date' })));
    }
  },

  process: {
    actions: S => ibtn('refresh', 'Check again', S.shizuku ? 'toast' : 'shizuku-on', S.shizuku ? 'Read just now' : ''),
    body(S) {
      if (!S.shizuku) return notice('info', 'Live readings need Shizuku to be running on this phone.', btn('Open Shizuku', 'open', 'toast', 'Opened Shizuku'));
      return tiles(tile({ icon: 'memory', title: 'Memory free', big: '4.8 GB', small: 'Falling over the last hour' }) + tile({ icon: 'cpu', title: 'Processor', big: '17%', small: 'Level over the last hour' }) +
        tile({ icon: 'thermo', title: 'Temperature', big: '36°', small: 'Level over the last hour' }) + tile({ icon: 'files', title: 'Swap in use', big: '1.1 GB', small: 'Rising over the last hour' })) +
        section('Busiest apps', group(BUSY_APPS.map(a => row({ icon: 'device', title: a.name, sub: `${a.memory} · ${a.cpu} processor`, act: 'sheet', arg: `app|${a.name}`, opens: true })).join('')));
    }
  },

  widgets: {
    body(S) {
      const placed = kind => group(WIDGETS.filter(w => w.kind === kind).map(w => row({ icon: w.icon, title: w.name, sub: w.shows, status: S.widgets.includes(w.name) ? ['good', 'Added'] : ['idle', 'Not added'], act: 'sheet', arg: `widget|${w.name}`, opens: true })).join(''));
      const always = kind => group(WIDGETS.filter(w => w.kind === kind).map(w => row({ icon: w.icon, title: w.name, sub: w.shows, act: 'sheet', arg: `widget|${w.name}`, opens: true })).join(''));
      return section('Launcher widgets', placed('Launcher widget')) + section('Quick Settings tiles', placed('Quick Settings tile')) +
        section('App shortcuts', always('App shortcut')) + section('In the share menu of other apps', always('Share menu entry'));
    }
  },

  settings: {
    body(S) {
      const d = S.defaults, missing = MODELS.filter(m => !m.available).map(m => m.provider);
      const playback = group(
        row({ icon: 'volume', title: 'Starting volume', sub: 'On the Pi screen', value: d.startVolume === 0 ? 'Muted' : `${d.startVolume}%`, act: 'sheet', arg: 'start-volume', opens: true }) +
        row({ icon: 'history', title: 'Resume where I stopped', trailing: toggle(d.resume, 'toggle-resume', 'Resume where I stopped') }) +
        row({ icon: 'loop', title: 'Loop', trailing: toggle(d.loop === 'On', 'default-loop', 'Loop') }) +
        row({ icon: 'skip', title: 'Skip length', value: `${d.skip} seconds`, act: 'sheet', arg: 'skip|default', opens: true }));
      const assistant = labelled('Provider', seg(MODELS.map(m => [m.provider, m.icon, !m.available]), S.provider, 'provider', 'Provider'), missing.length ? `${missing.join(' and ')} are not set up on this Pi.` : '') +
        group(row({ icon: 'think-2', title: 'Model', value: `${S.defaultModel} ${S.defaultEffort.toLowerCase()}`, act: 'sheet', arg: 'model|default', opens: true }) +
          row({ icon: 'key', title: 'Pi commands', sub: 'Set on the Pi', status: piUp(S) ? ['good', 'Allowed'] : ['idle', 'Offline'] }));
      const appearance = labelled('Theme', seg([['System', 'system'], ['Light', 'sun'], ['Dark', 'moon']], S.theme === 'system' ? 'System' : S.theme === 'dark' ? 'Dark' : 'Light', 'theme', 'Theme')) +
        labelled('Text size', seg([['Small', 'text-s'], ['Medium', 'text-m'], ['Large', 'text-l']], { sm: 'Small', md: 'Medium', lg: 'Large' }[S.size], 'size', 'Text size')) +
        labelled('Primary colour', swatches(ACCENTS, S.accent, S.custom)) +
        noteLine(['device', 'screen'], 'Applies to every screen and the system bars.');
      return group(row({ icon: 'wifi', title: 'Connection', sub: S.conn.pi, status: piUp(S) ? ['good', 'Connected'] : ['idle', 'Offline'], act: 'go', arg: 'connection', opens: true })) +
        section('Playback', playback, 'set-playback', S.folded['set-playback']) +
        section('Assistant', assistant, 'set-assistant', S.folded['set-assistant']) +
        section('Appearance', appearance, 'set-appearance', S.folded['set-appearance']);
    }
  },

  connection: {
    body(S) {
      const c = S.conn, up = piUp(S);
      return lead(up ? 'good' : 'idle', up ? 'Connected over Tailscale' : 'The Raspberry Pi cannot be reached') +
        (up ? '' : notice('info', 'Check that Tailscale is on, and that the address below is the Pi.', btn('Check again', 'refresh', 'recheck', ''))) +
        section('Your devices', group(DEVICES.filter(d => !d.self).map(d => row({ icon: deviceIcon(d), title: d.name, status: d.hub && !up ? ['idle', 'Offline'] : deviceStatus(d), act: 'sheet', arg: `device|${d.name}`, opens: true })).join(''))) +
        group(row({ icon: 'download', title: 'Receive on this phone', sub: 'Other devices can send to it', trailing: toggle(c.receive, 'toggle-receive', 'Receive on this phone') })) +
        section('Connection details',
          labelled('Raspberry Pi address', field({ id: 'conn.pi', hint: 'raspberrypi', value: c.pi, icon: 'pi' }), 'Where Media, Chat, the camera and Notes live.') +
          labelled('Second address (optional)', field({ id: 'conn.second', hint: 'studio-mac', value: c.second, icon: 'laptop' }), 'A device that is usually on. It finds your devices when the Pi is off.') +
          labelled('Access token', field({ id: 'conn.token', hint: 'Token', value: c.token, icon: 'key', secret: !S.showToken, end: ibtn('eye', S.showToken ? 'Hide the token' : 'Show the token', 'toggle', 'showToken', S.showToken ? 'on' : 'quiet', 17) }), 'The same token on every device you own.') +
          labelled("This phone's name", field({ id: 'conn.name', hint: 'pixel-8', value: c.name, icon: 'device' }))) +
        btns(btn('Save', 'check', 'toast', 'Connection saved', 'primary'));
    }
  },

  guide: {
    body() {
      return card(markdown('## Ask\n\nFind a film, ask what is playing, or check how the Pi is doing.\n\n- What is on the Pi screen?\n- Find the knot tutorials shorter than five minutes\n- Is the Pi running hot?\n\n## Act\n\nThe assistant names the output or the device before it acts, the same way the app does.\n\n- Play Walk in the hills on the Pi screen\n- Send the projector note to studio-mac\n- Take a photo with the Pi camera\n\n## Keep\n\nIt can read and write your notes on the Pi.')) +
        btns(btn('See what it can use', 'clipboard', 'sheet', 'tools'));
    }
  },

  help: {
    body(S) {
      return card(markdown('## Where things live\n\n**Media** browses the drives and plays on the Pi screen or this phone. **Share** sends to your devices. **Chat** talks to the Pi assistant. **More** holds the camera, notes, tools and settings.\n\n## When something does not work\n\nOpen **More**, then **Tools**. It shows how the Pi is doing right now. If the Pi cannot be reached at all, open **Settings**, then **Connection**.')) +
        group(row({ icon: 'info', title: 'csync', value: S.update ? '2.34' : '2.35' }) + row({ icon: 'pi', title: 'Raspberry Pi', value: S.conn.pi }));
    }
  },

  showcase: {
    body: S => showcaseBody(S)
  }
};
