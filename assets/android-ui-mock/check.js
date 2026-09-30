// Checks every screen and sheet in both themes and all three text sizes against
// the rules in docs/android-app-model.md. Run `runChecks()` in the browser console.

// The status words the app may use, by dot colour. docs/android-app-model.md section 7 is the source.
const STATUS_WORDS = {
  good: ['Online', 'Ready', 'Connected', 'Playing', 'Live', 'Recording', 'Delivered', 'Allowed', 'Added'],
  warn: ['Checking', 'Connecting', 'Loading', 'Low power', 'applying'],
  bad: ['Failed', 'Blocked'],
  idle: ['Offline', 'Disconnected', 'Paused', 'Stopped', 'Not set up', 'Not added', 'Showing the cover', 'No device online']
};

// A filled button is allowed only for the verb a page or sheet exists for.
const FILLED_VERBS = /^(Send|Save|Install|Create)\b/;

/**
 * Reads the screens and the sheets as text and reports any line that draws
 * its own markup. A screen with no tag, class or style in it can only have
 * been built from the parts in kit.js.
 */
let KIT_AUDIT = null;
async function kitAudit() {
  const problems = [];
  let lines = 0;
  for (const file of ['screens.js', 'sheets.js']) {
    const text = await (await fetch(file, { cache: 'no-store' })).text();
    text.split('\n').forEach((line, n) => {
      if (/^\s*(\/\/|\/?\*)/.test(line)) return;
      lines++;
      const tag = line.match(/<\/?[a-z][a-z0-9]*[\s>]/i), own = line.match(/\b(class|style)=/);
      if (tag || own) problems.push(`${file} line ${n + 1} draws its own ${tag ? tag[0].trim() : own[0]} where a part belongs`);
    });
  }
  return (KIT_AUDIT = { problems, lines });
}
kitAudit();

function runChecks() {
  const host = document.createElement('div');
  host.style.cssText = 'position:absolute;left:-9999px;top:0';
  document.body.appendChild(host);
  const found = [], all = frames();
  let rendered = 0;

  const lum = hex => {
    const c = hex.replace('#', '').match(/../g).map(x => parseInt(x, 16) / 255).map(v => v <= 0.04045 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4);
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2];
  };
  const ratio = (a, b) => { const [x, y] = [lum(a), lum(b)].sort((p, q) => q - p); return (x + 0.05) / (y + 0.05); };

  for (const theme of ['dark', 'light']) for (const size of ['sm', 'md', 'lg']) {
    document.documentElement.dataset.theme = theme;
    for (const f of all) {
      const tag = `${theme}/${size} ${f.label}`;
      const s = freshState();
      Object.assign(s, { theme, size, place: f.place });
      const el = document.createElement('div');
      el.className = 'phone';
      host.appendChild(el);
      try { f.change(s); dress(el, s); if (f.end) el.dataset.end = '1'; el.innerHTML = phoneHtml(s); } catch (e) { found.push(`${tag}: cannot be drawn, ${e.message}`); el.remove(); continue; }
      tidy(el);
      rendered++;
      const box = el.getBoundingClientRect();

      if (/…|\.\.\./.test(el.innerText)) found.push(`${tag}: an ellipsis in text`);
      for (const p of el.querySelectorAll('[placeholder]')) if (/…|\.\.\./.test(p.placeholder)) found.push(`${tag}: an ellipsis in a placeholder`);

      const crumbs = el.querySelector('.crumbs');
      if (crumbs.scrollWidth > crumbs.clientWidth + 1) found.push(`${tag}: the path does not fit`);
      const top = el.querySelector('.p-top').getBoundingClientRect().height;
      if (Math.abs(top - 52) > 0.5) found.push(`${tag}: the top bar is ${top}px tall`);

      for (const n of el.querySelectorAll('*')) {
        if (n.closest('.seg, .md pre, .crumbs, svg, .full')) continue;
        const r = n.getBoundingClientRect();
        if (!r.width || !r.height) continue;
        const over = Math.max(r.right - box.right, box.left - r.left);
        if (over > 1.5) { found.push(`${tag}: ${n.tagName.toLowerCase()}.${String(n.className).split(' ')[0]} runs ${Math.round(over)}px outside the phone`); break; }
      }
      for (const area of el.querySelectorAll('.p-scroll, .sheet-body, .panel')) if (area.scrollWidth > area.clientWidth + 1) found.push(`${tag}: ${area.className} scrolls sideways`);
      const panel = el.querySelector('.panel');
      if (panel && panel.scrollHeight > panel.clientHeight + 1) found.push(`${tag}: the player panel would need scrolling`);
      const sheetEl = el.querySelector('.sheet');
      if (sheetEl && sheetEl.getBoundingClientRect().top < box.top + 60) found.push(`${tag}: the sheet covers the whole screen`);

      for (const b of el.querySelectorAll('button')) {
        const name = (b.getAttribute('aria-label') || b.innerText).trim();
        if (!name) found.push(`${tag}: a button has no name`);
        const r = b.getBoundingClientRect();
        if (r.height && (r.height < 47.5 || r.width < 47.5)) found.push(`${tag}: "${name.slice(0, 30)}" is ${Math.round(r.width)} by ${Math.round(r.height)}, under 48`);
        if (b.classList.contains('btn') && !b.querySelector('svg')) found.push(`${tag}: button "${name}" has no icon`);
      }
      for (const b of el.querySelectorAll('.seg button')) if (!b.querySelector('svg')) found.push(`${tag}: a tab has no icon`);
      for (const s of el.querySelectorAll('.seg')) {
        const drawn = [...s.querySelectorAll('svg')].map(i => i.innerHTML);
        if (new Set(drawn).size < drawn.length) found.push(`${tag}: two options in "${s.getAttribute('aria-label')}" share an icon`);
      }
      for (const b of el.querySelectorAll('.seg button span')) if (b.scrollWidth > b.clientWidth + 1) found.push(`${tag}: tab "${b.innerText}" is cut`);
      for (const t of el.querySelectorAll('.row-title .clamp')) { const word = t.innerText.trim(); if (!/[\s-]/.test(word) && t.clientHeight > parseFloat(getComputedStyle(t).lineHeight) * 1.5) found.push(`${tag}: the one word "${word}" is broken across lines`); }
      if (f.place !== 'showcase') {
        if (el.querySelectorAll('.btn.primary').length + el.querySelectorAll('.p-page .shutter, .p-page .transport .main').length > 1 && !el.querySelector('.sheet'))
          found.push(`${tag}: more than one filled control on the page`);
        if (el.querySelectorAll('.sheet .btn.primary').length > 1) found.push(`${tag}: more than one filled button in the sheet`);
        for (const b of el.querySelectorAll('.btn.primary')) if (!FILLED_VERBS.test(b.innerText.trim())) found.push(`${tag}: "${b.innerText.trim()}" is filled, and only Send, Save, Install and Create may be`);
      }

      for (const a of el.querySelectorAll('[data-act]')) if (!ACTS[a.dataset.act]) found.push(`${tag}: tap "${a.dataset.act}" does nothing`);
      for (const a of el.querySelectorAll('[data-act="sheet"]')) if (!SHEETS[a.dataset.arg.split('|')[0]]) found.push(`${tag}: sheet "${a.dataset.arg}" does not exist`);
      for (const a of el.querySelectorAll('[data-act="go"]')) if (!PLACE[a.dataset.arg]) found.push(`${tag}: place "${a.dataset.arg}" does not exist`);
      if (el.querySelector('.sheet .ibtn[aria-label*="lose" i]')) found.push(`${tag}: a sheet has a close button`);

      for (const st of el.querySelectorAll('.status:not(.lead)')) {
        const tone = ['good', 'warn', 'bad'].find(t => st.querySelector('.dot').classList.contains(t)) || 'idle', said = st.innerText.trim();
        const known = STATUS_WORDS[tone].some(w => said === w || said.startsWith(w + ' ') || said.startsWith(w + ',') || said.endsWith(w));
        const count = tone === 'good' && /^\d/.test(said) || tone === 'warn' && /^\d+ of \d+/.test(said);
        const measure = st.closest('.sheet') && /to 1$/.test(said);
        if (!known && !count && !measure) found.push(`${tag}: status "${said}" with a ${tone} dot is not in the vocabulary`);
      }
      const walk = document.createTreeWalker(el, NodeFilter.SHOW_TEXT);
      for (let n; (n = walk.nextNode());) {
        const t = n.nodeValue.trim();
        if (/\b[A-Z]{3,}\s+[A-Z]{2,}\b/.test(t) && t === t.toUpperCase() && !/^[A-Z]{2,5} \d/.test(t)) found.push(`${tag}: all capitals "${t.slice(0, 30)}"`);
        if ((t.match(/·/g) || []).length > 1) found.push(`${tag}: more than two facts on a line "${t.slice(0, 50)}"`);
        if (/[›»⌄▾▸—]/.test(t)) found.push(`${tag}: a text character used as a mark "${t.slice(0, 30)}"`);
        if (/\b(Download to|Save as a note|To a device|To another app)\b/.test(t)) found.push(`${tag}: a second name for an action "${t.slice(0, 40)}"`);
        if (/\b(planned|fixture|prototype|unavailable|TODO)\b/i.test(t)) found.push(`${tag}: roadmap or placeholder wording "${t.slice(0, 40)}"`);
      }
      el.remove();
    }
  }

  if (!KIT_AUDIT) found.push('the kit audit has not finished reading the screens, run the checks again');
  else found.push(...KIT_AUDIT.problems);

  for (const p of PLACES) {
    if (!SCREENS[p.id]) found.push(`no screen for ${p.id}`);
    if (pathTo(p.id).length > 3) found.push(`${p.id} is deeper than three levels`);
    let at = p.id, hops = 0;
    while (at && at !== 'home' && hops++ < 6) at = backTarget(at);
    if (at !== 'home' && !p.fromOutside) found.push(`Back from ${p.id} never reaches Home`);
    if (p.parent && !PLACE[p.parent]) found.push(`${p.id} has a parent that does not exist`);
  }

  const probe = document.createElement('div');
  probe.className = 'phone';
  document.body.appendChild(probe);
  for (const theme of ['dark', 'light']) {
    document.documentElement.dataset.theme = theme;
    const t = name => getComputedStyle(probe).getPropertyValue('--p-' + name).trim();
    for (const fg of ['text', 'dim', 'faint', 'bad']) for (const bg of ['bg', 'surface', 'surface2']) {
      const r = ratio(t(fg), t(bg));
      if (r < 4.5) found.push(`contrast, ${theme}: ${fg} on ${bg} is ${r.toFixed(2)} to 1`);
    }
    for (const a of ACCENTS) for (const bg of ['bg', 'surface', 'surface2']) {
      const r = ratio(theme === 'dark' ? a.onDark : a.onLight, t(bg));
      if (r < 4.5) found.push(`contrast, ${theme}: ${a.id} text on ${bg} is ${r.toFixed(2)} to 1`);
    }
  }
  probe.remove();
  for (const a of ACCENTS) if (ratio('#FFFFFF', a.fill) < 4.5) found.push(`contrast: white on ${a.id} is ${ratio('#FFFFFF', a.fill).toFixed(2)} to 1`);

  host.remove();
  document.documentElement.dataset.theme = resolvedTheme(S);
  const grouped = {};
  for (const f of found) {
    const m = f.match(/^(dark|light)\/(sm|md|lg) (.*?): (.*)$/);
    const key = m ? m[4] : f;
    const g = grouped[key] = grouped[key] || { on: new Set(), where: new Set() };
    if (m) { g.on.add(m[3]); g.where.add(`${m[1]}/${m[2]}`); }
  }
  return { frames: all.length, drawn: rendered, of: all.length * 6,
    problems: Object.entries(grouped).map(([k, g]) => g.on.size ? `${k} | ${g.on.size} frames, first: ${[...g.on][0]} | ${[...g.where].join(' ')}` : k) };
}
