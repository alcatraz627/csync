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
