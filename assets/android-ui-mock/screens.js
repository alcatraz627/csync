// One entry per place in the map. `actions` fills the right of the top bar,
// `body` fills the page. Both read the state and change nothing.

const piUp = S => S.pi === 'online';
const active = S => Object.entries(S.sessions).filter(([, s]) => s).map(([output, s]) => ({ output, ...s }));
const device = (S, name) => DEVICES.find(d => d.name === name);
const sessionWords = s => s.error ? 'Failed' : s.busy ? 'Loading' : s.paused ? 'Paused' : 'Playing';
const sessionTone = s => s.error ? 'bad' : s.busy ? 'warn' : s.paused ? 'idle' : 'good';
const left = h => `${clock(h.total - h.at)} left`;
const thread = S => S.threads.find(t => t.id === S.threadId);
const hubState = S => !piUp(S) ? ['idle', S.pi === 'checking' ? 'Checking the Raspberry Pi' : 'Raspberry Pi is offline']
  : S.power === 'low' ? ['warn', 'Raspberry Pi is online, power is low'] : ['good', 'Raspberry Pi is online'];

const offlineNotice = S => piUp(S) ? '' : notice('bad', 'The Raspberry Pi cannot be reached. Things saved on this phone still work.', btn('Open Tools', 'tools', 'go', 'tools'));

/** Transport and settings for one output, used by the page and the panel. */
function playerControls(S, output, small = false) {
  const s = S.sessions[output];
  const big = small ? 19 : 22;
  const pend = s.pending || {};
  const transport = [
    ibtn('favorite', s.favorite ? 'Remove favorite' : 'Favorite', 'p-favorite', output, s.favorite ? 'on' : 'quiet', big),
    ibtn('rewind', `Back ${s.skip} seconds`, 'p-skip', `${output}|-1`, '', big),
    ibtn(s.paused ? 'play' : 'pause', s.paused ? 'Resume' : 'Pause', 'p-pause', output, 'main', big + 2, s.busy ? 'disabled' : ''),
    ibtn('fastforward', `Forward ${s.skip} seconds`, 'p-skip', `${output}|1`, '', big),
    ibtn('skip', `Skip length, ${s.skip} seconds`, 'sheet', `skip|${output}`, 'quiet', big),
    ibtn('stop', 'Stop', 'p-stop', output, 'stop', big)
  ].join('');
  const words = small ? '' : `<div class="transport-words"><span></span><span></span><span class="main">${s.paused ? 'Resume' : 'Pause'}</span><span></span><span></span><span>Stop</span></div>`;
  const settings = [
    tile({ icon: 'volume', title: 'Volume', small: s.volume === 0 ? 'Muted' : `${s.volume}%`, act: 'sheet', arg: `volume|${output}`, cls: 'setting' }),
    tile({ icon: 'speed', title: 'Speed', small: `${s.speed}×`, act: 'sheet', arg: `speed|${output}`, cls: 'setting' }),
    tile({ icon: 'rotate', title: 'Rotate', small: pend.rotate != null ? `${pend.rotate}°, applying` : `${s.rotate}°`, act: 'p-rotate', arg: output, cls: 'setting' }),
    tile({ icon: 'loop', title: 'Loop', small: pend.loop != null ? `${pend.loop}, applying` : s.loop, act: 'p-loop', arg: output, cls: 'setting' })
  ].join('');
  return `<div class="player"><input class="range" type="range" min="0" max="${s.total}" value="${s.at}" data-in="seek" data-arg="${esc(output)}" aria-label="Position"><div class="times"><span>${clock(s.at)}</span><span>${clock(s.total)}</span></div><div class="transport">${transport}</div>${words}<div class="tiles">${settings}</div></div>`;
}

const SCREENS = {

  home: {
    actions: () => ibtn('search', 'Search', 'go', 'search'),
    body(S) {
      const [tone, words] = hubState(S);
      const issue = piUp(S) && S.power === 'low'
        ? notice('warn', 'Playback on the Pi screen may stop while power is low.', btn('Open Tools', 'tools', 'go', 'tools')) : '';

      const resume = HISTORY[0], chat = S.threads.find(t => !t.archived);
      const pickup = group(
        row({ icon: 'history', title: resume.title, sub: `${resume.source} on ${resume.output} · ${left(resume)}`, progress: resume.at / resume.total,
          act: 'sheet', arg: 'resume|0', off: !piUp(S) && resume.output === 'Pi screen',
          trailing: ibtn('play', `Resume on ${resume.output}`, 'resume', '0', 'go', 17, !piUp(S) && resume.output === 'Pi screen' ? 'disabled' : '') }) +
        (chat ? row({ icon: 'chat', title: chat.title, sub: `Conversation · ${day(chat.when)}`, act: 'open-thread', arg: chat.id, opens: true }) : ''));

      const up = piUp(S), online = DEVICES.filter(d => d.online && !d.self && !d.hub).length;
      const screenBusy = S.sessions['Pi screen'];
      const caps = [
        { icon: 'media', title: 'Media', to: 'media', s: up ? (S.drive === 'ok' ? ['good', '123 videos'] : ['warn', 'One drive missing']) : ['idle', 'Pi offline'] },
        { icon: 'chat', title: 'Chat', to: 'chat', s: up ? ['good', 'Assistant ready'] : ['idle', 'Saved chats only'] },
        { icon: 'share', title: 'Share', to: 'share', s: online ? ['good', plural(online, 'device') + ' online'] : ['idle', 'No device online'] },
        { icon: 'screen', title: 'Pi screen', to: 'pi-screen', s: !up ? ['idle', 'Pi offline'] : screenBusy ? ['good', sessionWords(screenBusy)] : ['idle', 'Showing the cover'] },
        { icon: 'camera', title: 'Pi camera', to: 'camera', s: up ? ['good', 'Preview ready'] : ['idle', 'Pi offline'] },
        { icon: 'note', title: 'Notes', to: 'notes', s: ['good', `${plural(S.notes.length, 'note')}, ${plural(S.pins.length, 'pin')}`] },
        { icon: 'tools', title: 'Tools', to: 'tools', s: !up ? ['idle', 'Pi offline'] : S.power === 'low' ? ['warn', 'Power is low'] : ['good', 'All ready'] }
      ];
      const rank = { good: 0, warn: 1, idle: 2, bad: 3 };
      caps.sort((a, b) => rank[a.s[0]] - rank[b.s[0]]);
      const tiles = `<div class="tiles">${caps.map(c => tile({ icon: c.icon, title: c.title, status: c.s, act: 'go', arg: c.to })).join('')}</div>`;

      const devices = group(DEVICES.filter(d => !d.self).sort((a, b) => b.online - a.online).map(d => {
        const st = d.hub ? [tone, !piUp(S) ? 'Offline' : S.power === 'low' ? 'Low power' : 'Online'] : deviceStatus(d);
        return row({ icon: deviceIcon(d), title: d.name, status: st, act: 'sheet', arg: `device|${d.name}`, opens: true });
      }).join(''));

      return `<div class="status lead"><i class="dot ${tone}"></i><span>${esc(words)}</span></div>${issue}` +
        section('Pick up', pickup, 'pickup', S.folded.pickup) +
        section('Capabilities', tiles, 'caps', S.folded.caps) +
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
        seg([['All', 'all'], ['Media', 'media'], ['Chats', 'chat'], ['Notes', 'note'], ['Devices', 'device']], scope, 'view-search', 'Search in') +
        (piUp(S) ? '' : notice('info', 'The Pi is offline, so results come from what this phone has saved.')) + results;
    }
  },

  media: {
    actions: S => ibtn('search', 'Search this source', 'toggle', 'mediaSearch', S.mediaSearch ? 'on' : '') + ibtn('source', 'Switch source', 'sheet', 'source'),
    body(S) {
      const view = S.view.media, up = piUp(S), drive = S.drive === 'ok';
      const scope = S.source === 'This phone' ? 'Browsing this phone' : `Browsing ${S.source}`;
      const top = `<p class="note-line">${icon(S.source === 'This phone' ? 'device' : 'files', 15)}${esc(scope)}</p>` +
        (S.mediaSearch ? field({ id: 'mediaQuery', hint: `Search ${S.source}`, value: S.mediaQuery, icon: 'search' }) : '') +
        seg([['Files', 'files'], ['Videos', 'video'], ['History', 'history'], ['Access', 'access']], view, 'view-media', 'Media views');
      const q = S.mediaQuery.trim().toLowerCase();
      const itemRow = (it, sub) => row({ icon: KIND_ICON[it.kind], title: it.title, sub, act: 'sheet', arg: `item|${it.title}`, opens: true });
      let content = '';

      if (view === 'History') {
        content = section('Continue', group(HISTORY.map((h, i) => {
          const missing = h.source === 'Elements' && !drive, blocked = (h.output === 'Pi screen' && !up) || missing;
          return row({ icon: 'history', title: h.title, sub: missing ? 'Elements is disconnected' : `${h.output} · stopped at ${clock(h.at)}`,
            progress: h.at / h.total, act: 'sheet', arg: `resume|${i}`, opens: true, off: blocked });
        }).join(''))) + (up ? '' : notice('info', 'Your place in each item is kept on this phone. Items on the Pi screen resume when the Pi is back.'));
      } else if (!up) {
        content = offlineNotice(S) + section('Still here', group(row({ icon: 'history', title: 'History', sub: 'Your place in everything you played', act: 'view', arg: 'media|History', opens: true })));
      } else if (view === 'Access') {
        content = section('Open the drives from a computer', group(DRIVES.map(d => {
          const gone = d.name === 'Elements' && !drive;
          return row({ icon: 'access', title: `${d.name} over SMB`, sub: gone ? 'Disconnected' : d.smb, off: gone, act: 'copy', arg: d.smb, trailing: ibtn('copy', `Copy the ${d.name} SMB address`, 'copy', d.smb, 'quiet', 18, gone ? 'disabled' : '') }) +
            row({ icon: 'access', title: `${d.name} over FTP`, sub: gone ? 'Disconnected' : d.ftp, off: gone, act: 'copy', arg: d.ftp, trailing: ibtn('copy', `Copy the ${d.name} FTP address`, 'copy', d.ftp, 'quiet', 18, gone ? 'disabled' : '') });
        }).join(''))) +
        section('Drives', group(DRIVES.map(d => {
          const gone = d.name === 'Elements' && !drive;
          return row({ icon: 'files', title: d.name, sub: gone ? '' : plural(d.items, 'item'), status: gone ? ['idle', 'Disconnected'] : ['good', 'Connected'], act: gone ? '' : 'pick-source', arg: d.name, opens: !gone });
        }).join('')));
      } else if (S.source === 'Elements' && !drive) {
        content = notice('warn', 'Elements is disconnected. Your place in its films is kept.', btn('Open History', 'history', 'view', 'media|History')) +
          section('Other sources', group(row({ icon: 'files', title: 'Pi USB', status: ['good', 'Connected'], act: 'pick-source', arg: 'Pi USB', opens: true })));
      } else if (q) {
        const hits = VIDEOS.filter(v => v.title.toLowerCase().includes(q));
        content = hits.length ? section(plural(hits.length, 'match', 'matches'), group(hits.map(v => itemRow(v, `${v.folder} · ${v.length}`)).join('')))
          : empty('search', `Nothing in ${S.source} matches "${S.mediaQuery.trim()}"`, '');
      } else if (view === 'Videos') {
        content = section(plural(VIDEOS.length, 'video'), group(VIDEOS.map(v => itemRow(v, `${v.folder} · ${v.length}`)).join('')));
      } else {
        const here = LIBRARY[S.folder] || [], folders = here.filter(i => i.kind === 'folder'), files = here.filter(i => i.kind !== 'folder');
        const upRow = S.folder ? group(row({ icon: 'up', title: `Up to ${S.source}`, sub: `${S.source} / ${S.folder}`, act: 'folder', arg: '' })) : '';
        content = upRow +
          (folders.length ? section('Folders', group(folders.map(f => row({ icon: 'folder', title: f.title, sub: plural(f.count, 'item'), act: 'folder', arg: f.title, opens: true,
            trailing: ibtn('download', `Download or send the folder ${f.title}`, 'sheet', `folder|${f.title}`, 'framed', 17) })).join(''))) : '') +
          (files.length ? section('Files', group(files.map(f => itemRow(f, f.length ? `${f.length} · ${f.size}` : f.size)).join(''))) : '') +
          (!here.length ? empty('folder', 'This folder is empty', '') : '');
      }
      return top + content;
    }
  },

  'pi-screen': {
    actions: S => S.sessions['Pi screen'] ? ibtn('device', 'Move to this phone', 'sheet', 'move|Pi screen') : '',
    body(S) {
      const s = S.sessions['Pi screen'];
      if (!piUp(S)) return head('Pi screen') + offlineNotice(S);
      if (s) {
        return head(s.title, status(sessionTone(s), `${sessionWords(s)} on Pi screen`)) +
          `<div class="picture live${s.busy ? ' loading' : ''}">${icon('video', 40)}<span class="tag">${icon('screen', 13)}On the Pi screen</span></div>` +
          (s.error ? notice('bad', s.error, btn('Try again', 'refresh', 'p-pause', 'Pi screen')) : '') +
          (S.power === 'low' ? notice('warn', 'Power is low. The picture may stop.', btn('Open Tools', 'tools', 'go', 'tools')) : '') +
          playerControls(S, 'Pi screen');
      }
      return head('Nothing is playing', status('idle', 'Showing the cover')) +
        `<div class="picture idle">${icon('image', 36)}<span class="tag">${icon('image', 13)}${esc(S.cover)}</span></div>` +
        section('Put something on the screen', group(
          row({ icon: 'media', title: 'A file from Media', sub: 'Films, shows, photos', act: 'go', arg: 'media', opens: true }) +
          row({ icon: 'link', title: 'A YouTube link', sub: 'Or share a video from the YouTube app', act: 'sheet', arg: 'youtube', opens: true }) +
          row({ icon: 'camera', title: 'The Pi camera', sub: 'Live picture', act: 'show-camera', arg: '' }))) +
        section('When nothing is playing', group(row({ icon: 'image', title: 'Cover image', value: S.cover, act: 'go', arg: 'covers', opens: true })));
    }
  },

  covers: {
    body(S) {
      const f = S.framing[S.cover] || { fit: 'Cover', rotate: 0, crop: 'Full' };
      const hues = ['linear-gradient(160deg,#6b4a2f,#a8683a 45%,#2f3d52)', 'linear-gradient(160deg,#35506b,#8aa6b8 50%,#e8d9c0)', 'linear-gradient(160deg,#10294a,#2768b2 60%,#0e1d33)', 'linear-gradient(160deg,#0d1422,#2a3550 55%,#c98a3a)'];
      return head(S.cover, 'Shown on the Pi screen when nothing is playing') +
        `<div class="covers">${COVERS.map((c, i) => `<button type="button" class="cover" aria-pressed="${c === S.cover}" ${on('cover', c)} aria-label="Use ${esc(c)}"><span style="background:${hues[i]}">${esc(c)}</span></button>`).join('')}</div>` +
        `<div class="btns">${btn('Add an image', 'plus', 'toast', 'Choose an image from this phone')}</div>` +
        section('Frame this image',
          labelled('Fit', seg([['Cover', 'expand'], ['Contain', 'fit'], ['Stretch', 'screen']], f.fit, 'frame-fit', 'Fit')) +
          group(row({ icon: 'rotate', title: 'Rotate', sub: 'Tap to turn a quarter', value: `${f.rotate}°`, act: 'frame-turn' })) +
          labelled('Crop', seg([['Full', 'image'], ['Center', 'crop'], ['Top', 'up']], f.crop, 'frame-crop', 'Crop'), 'The image file is never changed.')) +
        `<div class="btns">${btn('Clear framing', 'refresh', 'frame-clear', '', 'quiet')}</div>`;
    }
  },

  'phone-player': {
    actions: S => S.sessions['This phone'] ? ibtn('expand', 'Full screen', 'full', 'on') + ibtn('screen', 'Move to the Pi screen', 'sheet', 'move|This phone') : '',
    body(S) {
      const s = S.sessions['This phone'];
      if (!s) return empty('device', 'Nothing is playing on this phone', '', btn('Browse Media', 'media', 'go', 'media', 'primary'));
      return head(s.title, status(sessionTone(s), `${sessionWords(s)} on this phone`)) +
        `<div class="picture live${s.busy ? ' loading' : ''}">${icon('video', 40)}<span class="tag">${icon('device', 13)}On this phone</span>${ibtn('expand', 'Full screen', 'full', 'on', 'corner', 18)}</div>` +
        playerControls(S, 'This phone');
    }
  },

  share: {
    actions: () => ibtn('device', 'Choose who receives', 'sheet', 'recipient') + ibtn('download', 'Received', 'go', 'received'),
    body(S) {
      const to = device(S, S.recipient), ready = to.online && (S.shareText.trim() || S.attachment);
      const failed = S.failed ? notice('bad', `${S.failed} was not delivered to ${S.recipient}. It is still attached.`, btn('Send again', 'refresh', 'send', '')) : '';
      const offline = to.online ? '' : notice('warn', `${to.name} is offline and cannot receive anything now.`, btn('Choose another device', 'device', 'sheet', 'recipient'));
      const attach = S.attachment
        ? row({ icon: KIND_ICON[S.attachment.kind] || 'file', title: S.attachment.title, sub: 'Attached', trailing: ibtn('trash', 'Remove the attachment', 'detach', '', 'quiet', 18) })
        : row({ icon: 'file', title: 'Attach a file', sub: 'A photo, a video or a document', act: 'sheet', arg: 'attach', opens: true });
      const history = S.sent.length
        ? group(S.sent.map((t, i) => row({ icon: KIND_ICON[t.kind], title: t.title, sub: `${t.to} · ${day(t.when)}`, status: t.ok ? ['good', 'Delivered'] : ['bad', 'Failed'], act: 'sheet', arg: `sent|${i}`, opens: true })).join(''))
        : empty('send', 'Nothing sent yet', 'What you send from this phone is listed here.');
      return head(`Send to ${to.name}`, status(...deviceStatus(to))) + offline + failed +
        field({ id: 'shareText', hint: 'Write a message', value: S.shareText, icon: 'text', tall: true }) +
        group(attach + row({ icon: 'clipboard', title: 'Use the clipboard', sub: S.clip.sub, act: 'sheet', arg: 'clipboard', opens: true })) +
        `<div class="btns">${btn('Send', 'send', 'send', '', 'primary wide', ready ? '' : 'disabled')}</div>` +
        section('Sent from this phone', history);
    }
  },

  received: {
    body(S) {
      return S.received.length
        ? section(plural(S.received.length, 'item'), group(S.received.map((r, i) => row({ icon: KIND_ICON[r.kind], title: r.title, sub: `${r.from} · ${day(r.when)}`, act: 'sheet', arg: `received|${i}`, opens: true })).join('')))
        : empty('download', 'Nothing received yet', 'What other devices send to this phone is listed here.');
    }
  },

  incoming: {
    body(S) {
      const kind = S.view.incoming;
      const item = {
        Video: { icon: 'video', title: 'VID 2026-09-26.mp4', from: 'Gallery' },
        Image: { icon: 'photo', title: 'IMG 4410.jpg', from: 'Photos' },
        YouTube: { icon: 'video', title: 'F-Droid 2.0, the biggest update in years', from: 'YouTube' },
        Instagram: { icon: 'video', title: 'A reel from Instagram', from: 'Instagram' },
        File: { icon: 'file', title: 'quote.pdf', from: 'Files' }
      }[kind];
      const plays = ['Video', 'YouTube', 'Instagram'].includes(kind), up = piUp(S);
      const o = S.incomingOptions;
      const options = plays ? section('How it plays',
        labelled('Loop', seg([['Off', 'once'], ['One', 'loop-one'], ['All', 'loop']], o.loop, 'in-loop', 'Loop')) +
        labelled(`Speed, ${o.speed}×`, `<input class="range" type="range" min="0.5" max="2" step="0.25" value="${o.speed}" data-in="in-speed" aria-label="Speed">`) +
        labelled(o.volume === 0 ? 'Volume, muted' : `Volume, ${o.volume}%`, `<input class="range" type="range" min="0" max="100" step="5" value="${o.volume}" data-in="in-volume" aria-label="Volume">`, 'Starts the way you last played. Change anything before it begins.')) : '';
      const main = plays
        ? btn(kind === 'Instagram' ? 'Download, then play on Pi screen' : 'Play on Pi screen', 'screen', 'play-incoming', 'Pi screen', 'primary wide', up ? '' : 'disabled')
        : kind === 'Image' ? btn('Save on this phone', 'download', 'toast', 'Saved to Photos', 'primary wide')
        : btn(`Send to ${S.recipient}`, 'send', 'send-incoming', '', 'primary wide');
      const others = [
        plays && row({ icon: 'device', title: 'Play on this phone', act: 'play-incoming', arg: 'This phone' }),
        kind === 'Image' && row({ icon: 'screen', title: 'Show on Pi screen', act: 'play-incoming', arg: 'Pi screen', off: !up }),
        kind === 'Image' && row({ icon: 'image', title: 'Set as the Pi cover', act: 'cover-from-share', off: !up }),
        kind !== 'File' && row({ icon: 'share', title: `Send to ${S.recipient}`, act: 'send-incoming' }),
        row({ icon: 'device', title: 'Send to another device', act: 'sheet', arg: 'recipient', opens: true }),
        row({ icon: 'chat', title: 'Send to a conversation', act: 'sheet', arg: 'to-chat', opens: true }),
        row({ icon: 'note', title: 'Add to a note', act: 'toast', arg: 'Added to a new note' }),
        row({ icon: 'pin', title: 'Save as a pin', act: 'toast', arg: 'Saved to Pins' })
      ].filter(Boolean).join('');
      return head('Shared with csync') +
        group(row({ icon: item.icon, title: item.title, sub: `From ${item.from}` })) +
        (plays && !up ? offlineNotice(S) : '') + options + `<div class="btns">${main}</div>` + section('Or', group(others));
    }
  },

  chat: {
    actions: S => ibtn('search', 'Search conversations', 'toggle', 'chatSearch', S.chatSearch ? 'on' : ''),
    body(S) {
      const view = S.view.chat;
      const lead = S.pi === 'online' ? ['good', 'The Pi assistant is online'] : S.pi === 'checking' ? ['warn', 'Checking the Pi assistant'] : ['idle', 'The Pi assistant is offline'];
      const top = `<div class="status lead"><i class="dot ${lead[0]}"></i><span>${lead[1]}</span></div>` +
        seg([['All', 'all'], ['Favorites', 'favorite'], ['Archived', 'archive'], ['Tools', 'tools']], view, 'view-chat', 'Conversation views');
      if (view === 'Tools') {
        return top + ASSISTANT_TOOLS.map(g => section(g.group, `<div class="group defs">${g.tools.map(([name, does]) => `<p><b>${esc(name)}</b><span>: ${esc(does)}</span></p>`).join('')}</div>`)).join('');
      }
      const q = S.chatQuery.trim().toLowerCase();
      const rows = S.threads.filter(t => (view === 'Archived' ? t.archived : !t.archived) && (view !== 'Favorites' || t.favorite) && (!q || t.title.toLowerCase().includes(q)));
      const none = q ? empty('search', `No conversation matches "${S.chatQuery.trim()}"`, '')
        : view === 'Favorites' ? empty('favorite', 'No favorites yet', 'Open a conversation and tap the heart to keep it here.')
        : view === 'Archived' ? empty('archive', 'Nothing archived', 'Archived conversations leave the main list and wait here.')
        : empty('chat', 'No conversations yet', '', btn('New chat', 'plus', 'new-thread', '', 'primary'));
      return top + (S.chatSearch ? field({ id: 'chatQuery', hint: 'Search conversations', value: S.chatQuery, icon: 'search' }) : '') +
        `<div class="btns">${btn('New chat', 'plus', 'new-thread', '', 'primary', piUp(S) ? '' : 'disabled')}${btn('Settings', 'settings', 'sheet', 'model|default')}</div>` +
        (rows.length ? section(view === 'All' ? 'Recent' : view, group(rows.map(t => row({ icon: 'chat', title: t.title, sub: `${t.when} · ${plural(t.count, 'message')}`, act: 'open-thread', arg: t.id, opens: true })).join(''))) : none);
    }
  },

  conversation: {
    body(S) {
      const t = thread(S);
      const title = S.editingTitle
        ? `<input class="title-input" data-in="threadTitle" value="${esc(t.title)}" aria-label="Conversation title">`
        : `<h2>${clamp(t.title)}</h2>`;
      const tokens = Number.isFinite(t.tokens) ? ` · ${compact(t.tokens)} tokens` : '';
      const headRow = `<div class="head"><div class="head-row">${title}${ibtn('edit', 'Edit the title', 'edit-title', '', 'quiet', 18)}${ibtn('favorite', t.favorite ? 'Remove from favorites' : 'Add to favorites', 'fav-thread', '', t.favorite ? 'on' : 'quiet', 18)}${ibtn('archive', t.archived ? 'Take out of the archive' : 'Archive', 'arch-thread', '', t.archived ? 'on' : 'quiet', 18)}</div><p class="model-line">${esc(S.model)} <span class="effort">${esc(S.effort.toLowerCase())}</span>${tokens}</p></div>`;
      const msgs = t.messages.map((m, i) => {
        if (m.thinking) return `<button type="button" class="think" ${on('toast', 'The assistant looked up Elements and chose the Pi screen')}>${icon('forward', 13)}Thinking</button>`;
        const bubble = `<div class="msg${m.me ? ' me' : ''}" ${on('pick-msg', i)} tabindex="0" role="button" aria-label="Message, tap for copy and fork">${markdown(m.text)}</div>`;
        const meta = S.pickedMsg === i ? `<div class="msg-meta${m.me ? ' me' : ''}"><span>${esc(m.when)}</span>${ibtn('copy', 'Copy this message', 'toast', 'Copied', 'quiet', 16)}${ibtn('fork', 'Fork from here', 'sheet', `fork|${i}`, 'quiet', 16)}</div>` : '';
        const results = m.results ? `<div class="results">${group(m.results.map((r, j) => row({ icon: { media: 'media', facts: 'tools', image: 'photo', file: 'file' }[r.kind], title: r.title, sub: r.sub, act: 'sheet', arg: `result|${i}|${j}`, opens: true })).join(''))}</div>` : '';
        return bubble + meta + results;
      }).join('');
      return headRow + (piUp(S) ? '' : notice('info', 'The Pi assistant is offline. You can read this conversation; sending waits for the Pi.')) +
        (t.messages.length ? `<div class="msgs">${msgs}</div>` : empty('chat', 'Ask the Pi assistant', 'It can find and play media, check the Pi and keep notes.'));
    },
    composer(S) {
      const long = S.draft.split('\n').length > 2 || S.draft.length > 90;
      const panel = S.draftOpen ? `<div class="draft" style="height:${S.draftHeight}px"><div class="handle" data-drag="draft"><span></span></div><textarea data-in="draft" aria-label="Message" placeholder="Message the Pi">${esc(S.draft)}</textarea></div>` : '';
      const chip = S.chatAttachment ? `<span class="chip">${icon(KIND_ICON[S.chatAttachment.kind] || 'file', 15)}${esc(S.chatAttachment.title)}${ibtn('trash', 'Remove the attachment', 'chat-detach', '', 'quiet', 15)}</span>` : '';
      const line = S.draftOpen || long
        ? `<button type="button" class="field" ${on('draft-open')} aria-label="Open the full message"><span class="clamp one">${esc(S.draft.split('\n')[0] || 'Message the Pi')}</span></button>`
        : `<div class="field"><textarea data-in="draft" rows="1" aria-label="Message" placeholder="Message the Pi">${esc(S.draft)}</textarea></div>`;
      return `<div class="composer">${panel}${chip}<div class="composer-row">${ibtn('plus', 'Add to this message', 'sheet', 'chat-add', 'framed', 19)}${line}${ibtn('send', 'Send', 'send-chat', '', 'send', 19, piUp(S) ? '' : 'disabled')}</div></div>`;
    }
  },

  more: {
    body(S) {
      const tools = !piUp(S) ? ['idle', 'Pi offline'] : S.power === 'low' ? ['warn', 'Power is low'] : ['good', 'All ready'];
      return section('Areas', group(
        row({ icon: 'camera', title: 'Pi camera', sub: 'Live picture, photos and recordings', act: 'go', arg: 'camera', opens: true }) +
        row({ icon: 'note', title: 'Notes', sub: `${plural(S.notes.length, 'note')} and ${plural(S.pins.length, 'pin')} on the Pi`, act: 'go', arg: 'notes', opens: true }) +
        row({ icon: 'tools', title: 'Tools', status: tools, act: 'go', arg: 'tools', opens: true }) +
        row({ icon: 'settings', title: 'Settings', sub: 'How the app connects, plays and looks', act: 'go', arg: 'settings', opens: true }))) +
        section('Reference', group(
          row({ icon: 'help', title: 'Assistant guide', sub: 'What you can ask the Pi assistant', act: 'go', arg: 'guide', opens: true }) +
          row({ icon: 'info', title: 'Help and about', sub: 'Version 2.34', act: 'go', arg: 'help', opens: true })));
    }
  },

  camera: {
    body(S) {
      const up = piUp(S), connecting = up && S.camera === 'connecting';
      const st = !up ? ['idle', 'Offline'] : connecting ? ['warn', 'Connecting'] : S.recording ? ['bad', 'Recording 0:18'] : ['good', 'Live'];
      const picture = !up ? `<div class="picture">${icon('camera', 36)}</div>`
        : connecting ? `<div class="picture loading">${icon('camera', 36)}</div>`
        : `<div class="picture live">${icon('camera', 36)}${S.recording ? `<span class="tag"><i class="dot bad"></i>Recording</span>` : ''}</div>`;
      return `<div class="status lead"><i class="dot ${st[0]}"></i><span>${st[1]}</span></div>` + picture + (up ? '' : offlineNotice(S)) +
        `<div class="shoot"><button type="button" class="thumb" ${on('go', 'captures')} aria-label="Captures"></button><button type="button" class="shutter" ${on('photo')} aria-label="Take a photo" ${up && !connecting ? '' : 'disabled'}>${icon('camera', 28)}</button><button type="button" class="rec" ${on('record')} aria-label="${S.recording ? 'Stop recording' : 'Start recording'}" ${up && !connecting ? '' : 'disabled'}>${icon(S.recording ? 'stop' : 'record', 22)}</button></div>`;
    }
  },

  captures: {
    body(S) {
      const days = S.captures.filter(d => d.items.length);
      if (!days.length) return empty('photo', 'No captures yet', 'Photos and recordings from the Pi camera are kept here.', btn('Open the camera', 'camera', 'go', 'camera', 'primary'));
      return days.map(d => section(d.day, group(d.items.map(c => row({ icon: c.kind === 'Photo' ? 'photo' : 'video', title: c.kind === 'Photo' ? 'Photo' : `Recording, ${c.length}`, sub: `${c.when} · ${c.size}`, act: 'sheet', arg: `capture|${c.id}`, opens: true })).join('')))).join('');
    }
  },

  notes: {
    actions: S => ibtn('search', 'Search notes and pins', 'toggle', 'notesSearch', S.notesSearch ? 'on' : ''),
    body(S) {
      const view = S.view.notes, q = S.noteQuery.trim().toLowerCase();
      const top = seg([['Notes', 'note'], ['Pins', 'pin']], view, 'view-notes', 'Notes or pins') +
        (S.notesSearch ? field({ id: 'noteQuery', hint: `Search ${view.toLowerCase()}`, value: S.noteQuery, icon: 'search' }) : '');
      if (view === 'Notes') {
        const rows = S.notes.filter(n => !q || `${n.title} ${n.body}`.toLowerCase().includes(q));
        return top + `<div class="btns">${btn('New note', 'plus', 'new-note', '', 'primary')}</div>` +
          (rows.length ? group(rows.map(n => row({ icon: 'note', title: n.title, sub: n.edited, act: 'open-note', arg: n.id, opens: true })).join(''))
            : q ? empty('search', `No note matches "${S.noteQuery.trim()}"`, '') : empty('note', 'No notes yet', 'Notes are kept on the Pi and the assistant can read them.'));
      }
      const rows = S.pins.filter(p => !q || `${p.title} ${p.link || p.text} ${p.tags.join(' ')}`.toLowerCase().includes(q));
      return top + `<div class="btns">${btn('New pin', 'plus', 'new-pin', '', 'primary')}</div>` +
        (rows.length ? group(rows.map(p => row({ icon: p.link ? 'link' : 'text', title: p.title, sub: p.link ? new URL(p.link).host : 'Text', value: p.tags.length ? plural(p.tags.length, 'tag') : '', act: 'open-pin', arg: p.id, opens: true })).join(''))
          : q ? empty('search', `No pin matches "${S.noteQuery.trim()}"`, '') : empty('pin', 'No pins yet', 'Save a link or a snippet to find it again.'));
    }
  },

  note: {
    actions: () => ibtn('share', 'Send or share this note', 'sheet', 'share-note') + ibtn('trash', 'Delete this note', 'sheet', 'delete-note', 'quiet'),
    body(S) {
      const n = S.notes.find(x => x.id === S.noteId), mode = S.view.note;
      const modes = seg([['Preview', 'image'], ['Rich', 'edit'], ['Plain', 'markdown']], mode, 'view-note', 'How to see this note');
      if (mode === 'Preview') return head(n.title, n.edited) + modes + `<div class="card">${markdown(n.body)}</div>`;
      return labelled('Title', field({ id: 'noteTitle', hint: 'Title', value: n.title, icon: 'note' })) + modes +
        `<textarea class="editor" data-in="noteBody" aria-label="Note text">${esc(n.body)}</textarea>` +
        (mode === 'Rich' ? `<div class="card" id="rich-preview">${markdown(n.body)}</div>` : '') +
        `<div class="btns">${btn('Save', 'check', 'save-note', '', 'primary')}${btn('Add an image', 'image', 'toast', 'Choose an image from this phone')}</div>`;
    }
  },

  pin: {
    actions: () => ibtn('share', 'Send or share this pin', 'sheet', 'share-pin') + ibtn('trash', 'Delete this pin', 'sheet', 'delete-pin', 'quiet'),
    body(S) {
      const p = S.pins.find(x => x.id === S.pinId);
      return labelled(p.link != null && !p.text ? 'Link' : 'Text', field({ id: 'pinBody', hint: 'A link or some text', value: p.link || p.text || '', icon: p.link ? 'link' : 'text', tall: !p.link })) +
        labelled('Title', field({ id: 'pinTitle', hint: 'Title', value: p.title, icon: 'pin' })) +
        labelled('Tags', field({ id: 'pinTags', hint: 'Separate tags with commas', value: p.tags.join(', '), icon: 'tag' })) +
        labelled('About', field({ id: 'pinAbout', hint: 'Why you kept it', value: p.about, icon: 'text', tall: true })) +
        `<div class="btns">${btn('Save', 'check', 'save-pin', '', 'primary')}${p.link ? btn('Open the link', 'link', 'toast', 'Opened in the browser') : ''}</div>`;
    }
  },

  tools: {
    body(S) {
      const up = piUp(S), low = S.power === 'low', gone = S.drive !== 'ok';
      const lead = !up ? ['idle', 'The Raspberry Pi is offline'] : low ? ['warn', 'Power is low'] : gone ? ['warn', 'One drive is disconnected'] : ['good', 'Everything is ready'];
      const svc = (title, symbol, id) => row({ icon: symbol, title, status: up ? ['good', 'Ready'] : ['idle', 'Offline'], act: 'sheet', arg: `service|${id}`, opens: true });
      return `<div class="status lead"><i class="dot ${lead[0]}"></i><span>${lead[1]}</span></div>` +
        `<div class="btns">${btn('Check again', 'refresh', 'recheck', '', 'primary')}</div>` +
        section('Raspberry Pi', group(
          svc('Media', 'media', 'media') + svc('Assistant', 'chat', 'assistant') + svc('Camera', 'camera', 'camera') +
          row({ icon: 'power', title: 'Power', status: !up ? ['idle', 'Offline'] : low ? ['warn', 'Low power'] : ['good', 'Steady'], act: 'sheet', arg: 'power', opens: true }) +
          row({ icon: 'files', title: 'Drives', status: !up ? ['idle', 'Offline'] : gone ? ['warn', '1 of 2 connected'] : ['good', '2 connected'], act: 'view', arg: 'media|Access', opens: true }))) +
        section('This phone', group(
          row({ icon: 'cpu', title: 'Process monitor', sub: 'Memory, processor, temperature', act: 'go', arg: 'process', opens: true }) +
          row({ icon: 'launcher', title: 'Widgets', sub: 'Launcher widgets, tiles and shortcuts', act: 'go', arg: 'widgets', opens: true }))) +
        section('This app', group(S.update
          ? row({ icon: 'download', accent: true, title: 'Update to 2.35', sub: 'Ready on the Pi', act: 'sheet', arg: 'update', opens: true, off: !up })
          : row({ icon: 'check', title: 'csync 2.34', sub: 'Up to date' })));
    }
  },

  process: {
    body(S) {
      if (!S.shizuku) {
        return notice('info', 'Live readings need Shizuku to be running on this phone.', btn('Open Shizuku', 'expand', 'toast', 'Opened Shizuku')) +
          `<div class="btns">${btn('Check again', 'refresh', 'shizuku-on', '')}</div>`;
      }
      return `<div class="btns">${btn('Read again', 'refresh', 'toast', 'Readings updated', 'primary')}</div>` +
        `<div class="tiles">${tile({ icon: 'memory', title: 'Memory free', big: '4.8 GB', small: 'of 12 GB' })}${tile({ icon: 'cpu', title: 'Processor', big: '17%', small: 'Last minute' })}${tile({ icon: 'thermo', title: 'Temperature', big: '36°', small: 'Normal' })}${tile({ icon: 'files', title: 'Swap in use', big: '1.1 GB', small: 'of 4 GB' })}</div>` +
        section('Busiest apps', group(BUSY_APPS.map(a => row({ icon: 'device', title: a.name, sub: `${a.memory} · ${a.cpu} processor`, act: 'sheet', arg: `app|${a.name}`, opens: true })).join('')));
    }
  },

  widgets: {
    body() {
      return section('Launcher widgets', group(
        row({ icon: 'image', title: 'xkcd', sub: 'The latest comic', status: ['good', 'On your launcher'] }) +
        row({ icon: 'play', title: 'Media remote', sub: 'Pause, resume and stop the Pi screen', act: 'toast', arg: 'Choose where to place the widget', value: 'Add' }))) +
        section('Quick Settings tiles', group(
          row({ icon: 'camera', title: 'Pi camera', sub: 'Open the live picture', act: 'toast', arg: 'Added to Quick Settings', value: 'Add' }) +
          row({ icon: 'share', title: 'Share the clipboard', sub: 'Send it to your last device', act: 'toast', arg: 'Added to Quick Settings', value: 'Add' }))) +
        section('App shortcuts', group(row({ icon: 'launcher', title: 'Media, Share and Chat', sub: 'Press and hold the csync icon on your launcher' })));
    }
  },

  settings: {
    body(S) {
      const theme = S.theme === 'system' ? 'System' : S.theme === 'dark' ? 'Dark' : 'Light';
      return group(
        row({ icon: 'wifi', title: 'Connection', sub: S.conn.pi, status: piUp(S) ? ['good', 'Connected'] : ['idle', 'Offline'], act: 'go', arg: 'connection', opens: true }) +
        row({ icon: 'play', title: 'Playback', sub: `Starts ${S.defaults.startVolume === 0 ? 'muted' : `at ${S.defaults.startVolume}%`} on the Pi screen`, act: 'go', arg: 'playback', opens: true }) +
        row({ icon: 'chat', title: 'Assistant', sub: `${S.defaultModel} ${S.defaultEffort.toLowerCase()}`, act: 'go', arg: 'assistant', opens: true }) +
        row({ icon: 'palette', title: 'Appearance', sub: `${theme} theme`, act: 'go', arg: 'appearance', opens: true }));
    }
  },

  connection: {
    body(S) {
      const c = S.conn;
      return `<div class="status lead"><i class="dot ${piUp(S) ? 'good' : 'idle'}"></i><span>${piUp(S) ? 'Connected over Tailscale' : 'Not connected'}</span></div>` +
        labelled('Raspberry Pi address', field({ id: 'conn.pi', hint: 'Name or address', value: c.pi, icon: 'pi' }), 'Where Media, Chat, the camera and Notes live.') +
        labelled('Second address (optional)', field({ id: 'conn.second', hint: 'Another device that knows your devices', value: c.second, icon: 'laptop' }), 'Used to find your devices when the Pi is off.') +
        labelled('Access token', field({ id: 'conn.token', hint: 'Token', value: c.token, icon: 'key', secret: !S.showToken, end: ibtn(S.showToken ? 'moon' : 'sun', S.showToken ? 'Hide the token' : 'Show the token', 'toggle', 'showToken', 'quiet', 17) }), 'The same token on every device you own.') +
        labelled("This phone's name", field({ id: 'conn.name', hint: 'Name', value: c.name, icon: 'device' })) +
        group(row({ icon: 'download', title: 'Receive on this phone', sub: 'Other devices can send to it', trailing: toggle(c.receive, 'toggle-receive', 'Receive on this phone') })) +
        `<div class="btns">${btn('Save', 'check', 'toast', 'Connection saved', 'primary')}</div>` +
        section('Your devices', group(DEVICES.filter(d => !d.self).map(d => row({ icon: deviceIcon(d), title: d.name, status: d.hub && !piUp(S) ? ['idle', 'Offline'] : deviceStatus(d), act: 'sheet', arg: `device|${d.name}`, opens: true })).join('')));
    }
  },

  playback: {
    body(S) {
      const d = S.defaults;
      return section('On the Pi screen', group(
        row({ icon: 'volume', title: 'Starting volume', value: d.startVolume === 0 ? 'Muted' : `${d.startVolume}%`, act: 'sheet', arg: 'start-volume', opens: true }))) +
        section('Everywhere', group(
          row({ icon: 'history', title: 'Resume where I stopped', trailing: toggle(d.resume, 'toggle-resume', 'Resume where I stopped') }) +
          row({ icon: 'skip', title: 'Skip length', value: `${d.skip} seconds`, act: 'sheet', arg: 'skip|default', opens: true }))) +
        labelled('Loop', seg([['Off', 'once'], ['One', 'loop-one'], ['All', 'loop']], d.loop, 'default-loop', 'Loop'));
    }
  },

  assistant: {
    body(S) {
      const p = MODELS.find(m => m.provider === S.provider);
      const missing = MODELS.filter(m => !m.available).map(m => m.provider);
      return labelled('Provider', seg(MODELS.map(m => [m.provider, m.icon, !m.available]), S.provider, 'provider', 'Provider'), missing.length ? `${missing.join(' and ')} chat is not set up on this Pi.` : '') +
        group(row({ icon: 'chat', title: 'Model', value: S.defaultModel, act: 'sheet', arg: 'model|default', opens: true })) +
        labelled('Thinking', seg(p.efforts.map((e, i) => [e, `think-${i}`]), S.defaultEffort, 'default-effort', 'Thinking')) +
        section('Set on the Pi', group(row({ icon: 'key', title: 'Pi commands', status: piUp(S) ? ['good', 'Allowed'] : ['idle', 'Offline'] }))) +
        `<div class="btns">${btn('Save', 'check', 'toast', 'Assistant settings saved', 'primary')}</div>`;
    }
  },

  appearance: {
    body(S) {
      const swatches = ACCENTS.map(a => `<button type="button" class="swatch" style="--c:${a.fill}" aria-pressed="${S.accent === a.id}" aria-label="${a.name}" title="${a.name}" ${on('accent', a.id)}>${S.accent === a.id ? icon('check', 18) : ''}</button>`).join('') +
        `<button type="button" class="swatch custom${S.custom ? ' set' : ''}" style="--c:${S.custom || 'transparent'}" aria-pressed="${S.accent === 'custom'}" aria-label="Your own colour" title="Your own colour" ${on('sheet', 'custom')}>${icon(S.accent === 'custom' ? 'check' : 'palette', 18)}</button>`;
      return labelled('Theme', seg([['System', 'system'], ['Light', 'sun'], ['Dark', 'moon']], S.theme === 'system' ? 'System' : S.theme === 'dark' ? 'Dark' : 'Light', 'theme', 'Theme')) +
        labelled('Text size', seg([['Small', 'text-s'], ['Medium', 'text-m'], ['Large', 'text-l']], { sm: 'Small', md: 'Medium', lg: 'Large' }[S.size], 'size', 'Text size')) +
        labelled('Primary colour', `<div class="swatches">${swatches}</div>`) +
        `<p class="note-line">${icon('device', 14)}${icon('screen', 14)}Applies to every screen and the system bars.</p>`;
    }
  },

  guide: {
    body() {
      return `<div class="card">${markdown('## Ask\n\nFind a film, ask what is playing, or check how the Pi is doing.\n\n- What is on the Pi screen?\n- Find the knot tutorials shorter than five minutes\n- Is the Pi running hot?\n\n## Act\n\nThe assistant names the output or the device before it acts, the same way the app does.\n\n- Play Walk in the hills on the Pi screen\n- Send the projector note to studio-mac\n- Take a photo with the Pi camera\n\n## Keep\n\nIt can read and write your notes on the Pi.')}</div>` +
        `<div class="btns">${btn('See every tool', 'tools', 'view', 'chat|Tools')}</div>`;
    }
  },

  help: {
    body(S) {
      return `<div class="card">${markdown('## Where things live\n\n**Media** browses the drives and plays on the Pi screen or this phone. **Share** sends to your devices. **Chat** talks to the Pi assistant. **More** holds the camera, notes, tools and settings.\n\n## When something does not work\n\nOpen **Tools**. It shows what the Pi can and cannot do right now.')}</div>` +
        group(row({ icon: 'info', title: 'csync', value: '2.34' }) + row({ icon: 'pi', title: 'Raspberry Pi', value: S.conn.pi }) +
          row({ icon: 'tools', title: 'Tools', act: 'go', arg: 'tools', opens: true }));
    }
  }
};
