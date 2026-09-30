// The shared parts. Every screen is built from these and nothing else, so a
// change to a part reaches every screen that uses it.

const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const on = (act, arg = '') => act ? `data-act="${act}" data-arg="${esc(arg)}"` : '';
const clock = seconds => {
  const s = Math.max(0, Math.round(seconds)), h = Math.floor(s / 3600), m = Math.floor(s % 3600 / 60);
  return h ? `${h}:${String(m).padStart(2, '0')}:${String(s % 60).padStart(2, '0')}` : `${m}:${String(s % 60).padStart(2, '0')}`;
};
const compact = n => new Intl.NumberFormat('en', { notation: 'compact', maximumFractionDigits: 1 }).format(n);
const plural = (n, one, many = one + 's') => `${n} ${n === 1 ? one : many}`;
/** "Today" reads as "today" mid-sentence; a weekday keeps its capital. */
const day = when => /^(Today|Yesterday|Just now|Now)$/.test(when) ? when.toLowerCase() : when;

/** Long text wraps to two lines and fades; `one` keeps it to a single line. */
const clamp = (text, one = false) => `<span class="clamp${one ? ' one' : ''}">${esc(text)}</span>`;

/** A coloured dot followed by words. tone: good, warn, bad, or idle. */
const status = (tone, words, cls = '') => `<span class="status ${cls}"><i class="dot ${tone}"></i><span>${esc(words)}</span></span>`;

function ibtn(symbol, label, act, arg = '', cls = '', size = 20, more = '') {
  return `<button type="button" class="ibtn ${cls}" ${on(act, arg)} aria-label="${esc(label)}" title="${esc(label)}" ${more}>${icon(symbol, size)}</button>`;
}

function btn(label, symbol, act, arg = '', kind = '', more = '') {
  return `<button type="button" class="btn ${kind}" ${on(act, arg)} ${more}>${icon(symbol, 17)}<span>${esc(label)}</span></button>`;
}

/** The bar at the top: the place's name on a bar place, the path on a child place. */
function topBar(placeId, actions = '') {
  const path = pathTo(placeId);
  if (path.length === 1) {
    const p = PLACE[placeId];
    return `<header class="p-top"><nav class="crumbs" aria-label="You are here"><span class="crumb now root">${icon(p.icon, 19)}<span>${esc(p.label)}</span></span></nav><span class="p-actions">${actions}</span></header>`;
  }
  const parent = PLACE[PLACE[placeId].parent];
  const steps = path.map((id, i) => {
    const p = PLACE[id], last = i === path.length - 1;
    return last
      ? `<span class="crumb now" aria-current="page">${icon(p.icon, 14)}<span class="clamp one">${esc(p.label)}</span></span>`
      : `<button type="button" class="crumb" ${on('go', id)} aria-label="Go to ${esc(p.label)}">${icon(p.icon, 14)}<span>${esc(p.label)}</span></button>`;
  }).join('<span class="sep" aria-hidden="true">/</span>');
  return `<header class="p-top"><button type="button" class="back" ${on('back')} aria-label="Back to ${esc(parent.label)}">${icon('back', 20)}</button><nav class="crumbs" aria-label="You are here">${steps}</nav><span class="p-actions">${actions}</span></header>`;
}

function head(title, sub = '', cls = '') {
  return `<div class="head ${cls}"><h2>${clamp(title)}</h2>${sub ? `<p>${sub}</p>` : ''}</div>`;
}

/** A labelled group. With an id it collapses from its label and remembers it. */
function section(label, body, id = '', collapsed = false) {
  if (!id) return `<section class="sec"><h3 class="sec-label">${esc(label)}</h3>${body}</section>`;
  return `<section class="sec"><button type="button" class="sec-label" ${on('fold', id)} aria-expanded="${!collapsed}">${esc(label)}${icon('chevron', 16)}</button>${collapsed ? '' : body}</section>`;
}

const group = rows => `<div class="group">${rows}</div>`;

/**
 * One thing in a list. `opens` names the place or sheet it opens and adds the
 * chevron; `act` makes it do something and adds none. With neither it is plain text.
 */
function row(o) {
  const tappable = o.act && !o.off;
  const tag = tappable ? 'button' : 'div';
  const cls = ['row', o.off && 'off', o.picked && 'picked', o.danger && 'danger'].filter(Boolean).join(' ');
  const end = [
    o.status ? status(o.status[0], o.status[1]) : '',
    o.value ? `<span>${esc(o.value)}</span>` : '',
    o.picked ? icon('check', 17) : '',
    o.opens && tappable ? icon('forward', 16) : ''
  ].join('');
  const bar = o.progress != null ? `<span class="bar-line"><i style="width:${Math.round(o.progress * 100)}%"></i></span>` : '';
  const body = `<span class="row-ico${o.accent ? ' accent' : ''}">${icon(o.icon, 19)}</span><span class="row-copy"><span class="row-title">${clamp(o.title)}</span>${o.sub ? `<span class="row-sub">${clamp(o.sub)}</span>` : ''}${bar}</span>${end ? `<span class="row-end">${end}</span>` : ''}`;
  const main = `<${tag} ${tappable ? 'type="button"' : ''} class="${cls}" ${tappable ? on(o.act, o.arg) : ''}>${body}</${tag}>`;
  return o.trailing ? `<div class="row-wrap">${main}${o.trailing}</div>` : main;
}

/** The same data as a row, laid out for a grid. */
function tile(o) {
  const tag = o.act ? 'button' : 'div';
  return `<${tag} ${o.act ? 'type="button"' : ''} class="tile ${o.cls || ''}" ${on(o.act, o.arg)} ${o.off ? 'disabled' : ''}><span class="tile-head">${icon(o.icon, 18)}${esc(o.title)}</span>${o.big ? `<b>${esc(o.big)}</b>` : ''}${o.status ? status(o.status[0], o.status[1]) : ''}${o.small ? `<small>${esc(o.small)}</small>` : ''}</${tag}>`;
}

/** Pick one of a few. items: [label, icon, disabled?]. */
function seg(items, selected, act, label) {
  return `<div class="seg${items.length > 4 ? ' tight' : ''}" role="tablist" aria-label="${esc(label)}">${items.map(([name, symbol, off]) =>
    `<button type="button" role="tab" aria-selected="${name === selected}" ${on(act, name)} ${off ? 'disabled' : ''}>${icon(symbol, 15)}<span>${esc(name)}</span></button>`).join('')}</div>`;
}

function field(o) {
  const input = o.tall
    ? `<textarea data-in="${o.id}" placeholder="${esc(o.hint)}" aria-label="${esc(o.label || o.hint)}">${esc(o.value)}</textarea>`
    : `<input data-in="${o.id}" type="${o.secret ? 'password' : 'text'}" value="${esc(o.value)}" placeholder="${esc(o.hint)}" aria-label="${esc(o.label || o.hint)}">`;
  return `<div class="field${o.tall ? ' tall' : ''}">${icon(o.icon, 18)}${input}${o.end || ''}</div>`;
}

const labelled = (label, control, help = '') => `<label class="labelled"><span>${esc(label)}</span>${control}${help ? `<small>${esc(help)}</small>` : ''}</label>`;

const toggle = (checked, act, label) => `<button type="button" class="switch" role="switch" aria-checked="${checked}" aria-label="${esc(label)}" ${on(act)}></button>`;

function notice(tone, text, action = '') {
  return `<div class="notice ${tone}" role="status">${icon(tone === 'info' ? 'info' : 'alert', 19)}<div><p>${esc(text)}</p>${action}</div></div>`;
}

function empty(symbol, title, text, action = '') {
  return `<div class="empty">${icon(symbol, 34)}<b>${esc(title)}</b>${text ? `<span>${esc(text)}</span>` : ''}${action}</div>`;
}

const facts = pairs => `<dl class="kv">${pairs.filter(Boolean).map(([k, v]) => `<dt>${esc(k)}</dt><dd>${esc(v)}</dd>`).join('')}</dl>`;

/** A sheet: handle, title, body, and buttons only when it changes something. */
function sheet(o) {
  return `<div class="scrim" ${on('close-sheet')}><div class="sheet" role="dialog" aria-modal="true" aria-label="${esc(o.title)}" data-hold><div class="handle" data-drag="sheet"><span></span></div><div class="sheet-head"><h3>${clamp(o.title)}</h3>${o.sub ? `<p>${esc(o.sub)}</p>` : ''}</div><div class="sheet-body">${o.body}</div>${o.acts ? `<div class="sheet-acts">${o.acts}</div>` : ''}</div></div>`;
}

/** A small Markdown reader: headings, lists, tables, code, links, simple Mermaid arrows. */
function markdown(source) {
  const inline = s => esc(s)
    .replace(/\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)/g, (_, text, url) => `<a href="${url}" target="_blank" rel="noopener noreferrer">${text}</a>`)
    .replace(/`([^`]+)`/g, '<code>$1</code>')
    .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
  const lines = String(source).split('\n'), out = [];
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    if (line.startsWith('```mermaid')) {
      const edges = [];
      for (i++; i < lines.length && !lines[i].startsWith('```'); i++) {
        const m = lines[i].match(/^\s*([\w -]+?)\s*-->\s*([\w -]+)/);
        if (m) edges.push(m);
      }
      out.push(`<div class="flow">${edges.map(m => `<div><span>${esc(m[1])}</span>${icon('forward', 14)}<span>${esc(m[2])}</span></div>`).join('')}</div>`);
    } else if (line.startsWith('```')) {
      const code = [];
      for (i++; i < lines.length && !lines[i].startsWith('```'); i++) code.push(lines[i]);
      out.push(`<pre><code>${esc(code.join('\n'))}</code></pre>`);
    } else if (line.startsWith('|') && /^\|[\s:|-]+\|$/.test(lines[i + 1] || '')) {
      const rows = [line];
      for (i += 2; i < lines.length && lines[i].startsWith('|'); i++) rows.push(lines[i]);
      i--;
      out.push(`<table>${rows.map((r, j) => `<tr>${r.split('|').slice(1, -1).map(c => `<${j ? 'td' : 'th'}>${inline(c.trim())}</${j ? 'td' : 'th'}>`).join('')}</tr>`).join('')}</table>`);
    } else if (line.startsWith('- ')) {
      const items = [];
      for (; i < lines.length && lines[i].startsWith('- '); i++) items.push(`<li>${inline(lines[i].slice(2))}</li>`);
      i--;
      out.push(`<ul>${items.join('')}</ul>`);
    } else if (line.startsWith('## ')) out.push(`<h4>${inline(line.slice(3))}</h4>`);
    else if (line.startsWith('# ')) out.push(`<h3>${inline(line.slice(2))}</h3>`);
    else if (line.trim()) out.push(`<p>${inline(line)}</p>`);
  }
  return `<div class="md">${out.join('')}</div>`;
}

// Composites: parts made of the parts above. A screen that needs one of these
// asks for it by name, so there is one drawing of each in the whole app.

const sessionWords = s => s.busy ? 'Loading' : s.live ? 'Live' : s.paused ? 'Paused' : 'Playing';
const sessionTone = s => s.busy ? 'warn' : s.paused ? 'idle' : 'good';

/** The first line of a page that reports on something: one dot, one sentence. */
const lead = (tone, words) => `<div class="status lead"><i class="dot ${tone}"></i><span>${esc(words)}</span></div>`;
const btns = (...buttons) => `<div class="btns">${buttons.join('')}</div>`;
const tiles = html => `<div class="tiles">${html}</div>`;
const card = html => `<div class="card">${html}</div>`;
const noteLine = (symbols, text) => `<p class="note-line">${[].concat(symbols).map(s => icon(s, 14)).join('')}${esc(text)}</p>`;
const defs = pairs => `<div class="group defs">${pairs.map(([name, does]) => `<p><b>${esc(name)}</b><span>: ${esc(does)}</span></p>`).join('')}</div>`;

/**
 * Where you are inside something that is browsed in place, such as a drive.
 * steps: [label, act, arg, icon]. Every step but the last is tappable and goes there.
 */
function pathLine(steps) {
  return `<nav class="path" aria-label="Folder path">${steps.map(([label, act, arg, symbol], i) => {
    const last = i === steps.length - 1, inner = `${icon(symbol, 15)}<span>${esc(label)}</span>`;
    return (i ? `<span class="sep" aria-hidden="true">/</span>` : '') + (last ? `<span class="path-step now">${inner}</span>` : `<button type="button" class="path-step" ${on(act, arg)} aria-label="Go to ${esc(label)}">${inner}</button>`);
  }).join('')}</nav>`;
}

/** Where a picture or a video goes. mode: live, idle or nothing; tag: [icon, words]. */
function picture(o = {}) {
  const cls = ['picture', o.mode, o.loading && 'loading'].filter(Boolean).join(' ');
  const tag = o.tag ? `<span class="tag">${icon(o.tag[0], 13)}${esc(o.tag[1])}</span>` : '';
  return `<div class="${cls}">${icon(o.icon, o.size || 36)}${tag}</div>`;
}

/** A cover as the Pi screen will show it, with its fit, turn and crop applied. */
function framedPicture(art, f, tag) {
  return `<div class="picture framed" style="--art:${art};--turn:${f.rotate}deg" data-fit="${f.fit}" data-crop="${f.crop}"><i></i><span class="tag">${icon(tag[0], 13)}${esc(tag[1])}</span></div>`;
}

function coverGrid(names, art, chosen, act) {
  return `<div class="covers">${names.map((c, i) => `<button type="button" class="cover" aria-pressed="${c === chosen}" ${on(act, c)} aria-label="Use ${esc(c)}"><span style="background:${art[i]}">${esc(c)}</span></button>`).join('')}</div>`;
}

/** A slider with its value written above it. `live` lets the value change while dragging. */
function range(o) {
  const ends = o.low != null ? `<div class="range-ends"><span>${esc(o.low)}</span><span>${esc(o.high)}</span></div>` : '';
  return `<div class="labelled"><span ${o.live ? `data-live="${o.id}"` : ''}>${esc(o.shown)}</span><input class="range${o.hue ? ' hue' : ''}" type="range" min="${o.min}" max="${o.max}" step="${o.step || 1}" value="${o.value}" data-in="${o.id}" data-arg="${esc(o.arg || '')}" aria-label="${esc(o.label)}">${ends}${o.help ? `<small>${esc(o.help)}</small>` : ''}</div>`;
}

function swatches(accents, chosen, custom) {
  const dots = accents.map(a => `<button type="button" class="swatch" style="--c:${a.fill}" aria-pressed="${chosen === a.id}" aria-label="${a.name}" title="${a.name}" ${on('accent', a.id)}>${chosen === a.id ? icon('check', 18) : ''}</button>`).join('');
  const own = `<button type="button" class="swatch custom${custom ? ' set' : ''}" style="--c:${custom || 'transparent'}" aria-pressed="${chosen === 'custom'}" aria-label="Your own colour" title="Your own colour" ${on('sheet', 'custom')}>${icon(chosen === 'custom' ? 'check' : 'palette', 18)}</button>`;
  return `<div class="swatches">${dots}${own}</div>`;
}
const swatchBig = colour => `<div class="swatch-big" style="background:${colour}">${icon('check', 22)}<span>Sample</span></div>`;

/** Something attached, with a way to take it off again. */
function chip(symbol, text, act, label) {
  return `<span class="chip">${icon(symbol, 15)}${clamp(text, true)}${act ? ibtn('trash', label, act, '', 'quiet', 15) : ''}</span>`;
}

/** The camera's two controls: a shutter, and a smaller record button beside it. */
function shoot(ready, recording) {
  const off = ready ? '' : 'disabled';
  return `<div class="shoot"><button type="button" class="shutter" ${on('photo')} aria-label="Take a photo" ${off}>${icon('camera', 28)}</button><button type="button" class="rec" ${on('record')} aria-label="${recording ? 'Stop recording' : 'Start recording'}" ${off}>${icon(recording ? 'stop' : 'record', 22)}</button></div>` +
    `<div class="shoot-words"><span>Photo</span><span>${recording ? 'Stop' : 'Record'}</span></div>`;
}

/**
 * Transport and settings for one output, used by the page and the panel.
 * A live source (a camera, a shared screen) has no position, so it gets Stop and the settings only.
 */
function player(s, output, small = false) {
  const big = small ? 19 : 22, pend = s.pending || {};
  const wait = (key, shown) => pend[key] != null ? { status: ['warn', `${key === 'rotate' ? pend[key] + '°' : pend[key]}, applying`] } : { small: shown };
  const volume = tile({ icon: 'volume', title: 'Volume', small: s.volume === 0 ? 'Muted' : `${s.volume}%`, act: 'sheet', arg: `volume|${output}`, cls: 'setting' });
  const rotate = tile({ icon: 'rotate', title: 'Rotate', ...wait('rotate', `${s.rotate}°`), act: 'p-rotate', arg: output, cls: 'setting' });
  if (s.live) return `<div class="player">${tiles(volume + rotate)}${btns(btn('Stop', 'stop', 'p-stop', output, 'danger wide'))}</div>`;
  const transport = [
    ibtn('favorite', s.favorite ? 'Remove favorite' : 'Favorite', 'p-favorite', output, s.favorite ? 'on' : 'quiet', big),
    ibtn('rewind', `Back ${s.skip} seconds`, 'p-skip', `${output}|-1`, '', big),
    ibtn(s.paused ? 'play' : 'pause', s.paused ? 'Resume' : 'Pause', 'p-pause', output, 'main', big + 2, s.busy ? 'disabled' : ''),
    ibtn('fastforward', `Forward ${s.skip} seconds`, 'p-skip', `${output}|1`, '', big),
    ibtn('skip', `Skip length, ${s.skip} seconds`, 'sheet', `skip|${output}`, 'quiet', big),
    ibtn('stop', 'Stop', 'p-stop', output, 'stop', big)
  ].join('');
  const words = `<div class="transport-words"><span></span><span></span><span class="main">${s.paused ? 'Resume' : 'Pause'}</span><span></span><span>${s.skip} s</span><span>Stop</span></div>`;
  const settings = volume +
    tile({ icon: 'speed', title: 'Speed', small: `${s.speed}×`, act: 'sheet', arg: `speed|${output}`, cls: 'setting' }) + rotate +
    tile({ icon: 'loop', title: 'Loop', ...wait('loop', s.loop), act: 'p-loop', arg: output, cls: 'setting' });
  return `<div class="player"><input class="range" type="range" min="0" max="${s.total}" value="${s.at}" data-in="seek" data-arg="${esc(output)}" aria-label="Position"><div class="times"><span>${clock(s.at)}</span><span>${clock(s.total)}</span></div><div class="transport">${transport}</div>${words}${tiles(settings)}</div>`;
}

// Conversation parts.

const msgs = html => `<div class="msgs">${html}</div>`;
const thinking = () => `<button type="button" class="think" ${on('toast', 'The assistant looked up Elements and chose the Pi screen')}>${icon('forward', 13)}Thinking</button>`;

/**
 * One message. Yours sits on the right in a tint of the primary colour, the
 * assistant's on the left on the surface. Tapping it shows what you can do with it.
 */
function bubble(m, i, picked = false, tappable = true) {
  const files = (m.files || []).map(f => `<span class="msg-file">${icon(KIND_ICON[f.kind] || 'file', 15)}${clamp(f.title, true)}</span>`).join('');
  const tap = tappable ? `${on('pick-msg', i)} tabindex="0" role="button" aria-label="Message, tap for what you can do with it"` : '';
  const act = (symbol, label, name, arg) => `<button type="button" class="act" ${on(name, arg)}><span>${icon(symbol, 15)}${esc(label)}</span></button>`;
  const acts = picked ? `<div class="msg-acts${m.me ? ' me' : ''}">${act('copy', 'Copy', 'toast', 'Copied')}${m.me ? act('edit', 'Edit', 'edit-msg', i) : act('refresh', 'Regenerate', 'regen', i)}${act('fork', 'Fork', 'sheet', `fork|${i}`)}</div>` : '';
  return `<div class="msg${m.me ? ' me' : ''}${picked ? ' picked' : ''}" ${tap}>${files}${markdown(m.text)}<span class="msg-when">${esc(m.when)}</span></div>${acts}`;
}

const RESULT_ICON = { media: 'media', control: 'speed', image: 'photo', file: 'file', facts: 'tools', note: 'note', devices: 'devices' };

/**
 * What a tool gave back, drawn for its kind so the answer can be used where it
 * is read. kind: media, control, image, file, facts, note or devices.
 * `session` is what that output is playing now, so a media card stays truthful.
 */
function resultCard(r, arg, session) {
  const open = on('sheet', `result|${arg}`);
  const top = `<span class="rcard-top">${icon(RESULT_ICON[r.kind] || 'tools', 14)}${esc(r.tool)}</span>`;
  const line = (title, sub) => `<span class="row-copy"><span class="row-title">${clamp(title)}</span>${sub ? `<span class="row-sub">${clamp(sub)}</span>` : ''}</span>`;
  let body;
  if (r.kind === 'media') {
    const live = session && session.title === r.title;
    const state = live ? status(sessionTone(session), `${sessionWords(session)} on ${r.output === 'Pi screen' ? 'Pi screen' : 'this phone'}`) : status('idle', 'Stopped');
    const bar = live && !session.live ? `<span class="bar-line"><i style="width:${Math.round(session.at / session.total * 100)}%"></i></span>` : '';
    const ctl = live ? ibtn(session.paused ? 'play' : 'pause', session.paused ? 'Resume' : 'Pause', 'p-pause', r.output, '', 19) + ibtn('stop', 'Stop', 'p-stop', r.output, 'stop', 18)
      : ibtn('play', `Play on ${r.output === 'Pi screen' ? 'Pi screen' : 'this phone'}`, 'play', `${r.output}|${r.title}`, 'go', 17);
    body = `<div class="rcard-row"><button type="button" class="rcard-main" ${open}><span class="row-copy"><span class="row-title">${clamp(r.title)}</span>${state}${bar}</span></button>${ctl}</div>`;
  } else if (r.kind === 'image') {
    body = `<button type="button" class="rcard-main pic" ${open} aria-label="Open ${esc(r.title)}">${picture({ icon: 'photo', mode: 'live', tag: ['photo', r.title] })}</button>`;
  } else if (r.kind === 'facts' || r.kind === 'control') {
    const rows = r.facts.map(([k, v]) => `<dt>${esc(k)}</dt><dd>${esc(v)}</dd>`).join('');
    body = `<button type="button" class="rcard-main" ${open} aria-label="Open ${esc(r.title)}"><dl class="kv">${rows}</dl></button>`;
  } else if (r.kind === 'devices') {
    body = `<div class="rcard-list">${r.devices.map(([name, up]) => `<span>${status(up ? 'good' : 'idle', up ? 'Online' : 'Offline')}<b>${esc(name)}</b></span>`).join('')}</div>`;
  } else {
    body = `<button type="button" class="rcard-main" ${open}><span class="row-ico">${icon(RESULT_ICON[r.kind] || 'file', 19)}</span>${line(r.title, r.sub)}${icon('forward', 16)}</button>`;
  }
  return `<div class="rcard">${top}${body}</div>`;
}

/** The top of a conversation: its title, what keeps it, and one quiet line under it. */
function convoHead(o) {
  const title = o.editing
    ? `<input class="title-input" data-in="threadTitle" value="${esc(o.title)}" aria-label="Conversation title">`
    : `<h2>${clamp(o.title)}</h2>`;
  return `<div class="head"><div class="head-row">${title}${o.actions}</div>${o.line ? `<p class="model-line">${esc(o.line)}</p>` : ''}</div>`;
}

/**
 * Where a message is written. One rounded box holds the text, what is attached,
 * the way to add more, the model in use and Send, so they read as one control.
 * It grows with the text, and opens taller when asked.
 */
function composer(o) {
  const attached = o.attachment ? chip(KIND_ICON[o.attachment.kind] || 'file', o.attachment.title, 'chat-detach', 'Remove the attachment') : '';
  const size = o.tall ? ibtn('chevron', 'Make the message box smaller', 'draft-size', '', 'quiet', 18) : o.long ? ibtn('expand', 'Make the message box taller', 'draft-size', '', 'quiet', 17) : '';
  const grip = o.tall ? `<div class="handle" data-drag="draft"><span></span></div>` : '';
  const model = `<button type="button" class="pill" ${on('sheet', 'model|chat')} aria-label="Model, ${esc(o.model)}">${icon('think-2', 15)}<span>${esc(o.model)}</span></button>`;
  return `<div class="composer"><div class="compose${o.tall ? ' tall' : ''}">${grip}${attached}<div class="compose-text"><textarea data-in="draft" rows="1" ${o.tall ? `style="height:${o.height}px"` : ''} aria-label="Message" placeholder="Message the Pi">${esc(o.draft)}</textarea>${size}</div>` +
    `<div class="compose-tools">${ibtn('plus', 'Add to this message', 'sheet', 'chat-add', 'quiet', 20)}${model}<span class="grow"></span>${ibtn('send', 'Send', 'send-chat', '', o.ready ? 'send ready' : 'send', 19, o.canSend ? '' : 'disabled')}</div></div></div>`;
}

// Editing parts.

const editor = (id, value, label) => `<textarea class="editor" data-in="${id}" aria-label="${esc(label)}">${esc(value)}</textarea>`;
const richEditor = (html, label) => `<div class="card rich" contenteditable="true" data-rich role="textbox" aria-multiline="true" aria-label="${esc(label)}">${html}</div>`;

/** Android's own share menu, drawn only so the hand-off can be seen. It is not part of csync. */
function appTiles(apps, act) {
  return `<div class="apps">${apps.map(([name, symbol]) => `<button type="button" class="app" ${on(act, name)}><span>${icon(symbol, 22)}</span>${esc(name)}</button>`).join('')}</div>`;
}

const hexRgb = hex => (hex.replace('#', '').match(/../g) || ['0', '0', '0']).map(x => parseInt(x, 16) || 0);
/** How well white text reads on a colour, as a contrast ratio. */
function whiteOn(hex) {
  const [r, g, b] = hexRgb(hex).map(v => v / 255).map(v => v <= 0.04045 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4);
  return 1.05 / (0.2126 * r + 0.7152 * g + 0.0722 * b + 0.05);
}
function hueOf(hex) {
  const [r, g, b] = hexRgb(hex).map(v => v / 255), max = Math.max(r, g, b), d = max - Math.min(r, g, b);
  if (!d) return 0;
  const h = max === r ? ((g - b) / d) % 6 : max === g ? (b - r) / d + 2 : (r - g) / d + 4;
  return Math.round((h * 60 + 360) % 360);
}
function hueHex(h) {
  const f = n => { const k = (n + h / 30) % 12, c = 0.42 - 0.273 * Math.max(-1, Math.min(k - 3, 9 - k, 1)); return Math.round(c * 255).toString(16).padStart(2, '0'); };
  return `#${f(0)}${f(8)}${f(4)}`.toUpperCase();
}

const KIND_ICON = { folder: 'folder', video: 'video', image: 'photo', audio: 'volume', doc: 'file', Text: 'text', Image: 'photo', Video: 'video', File: 'file', Link: 'link' };
const deviceIcon = d => d.kind;
const deviceStatus = d => d.online ? ['good', 'Online'] : ['idle', 'Offline'];
