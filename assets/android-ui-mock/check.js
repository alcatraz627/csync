// Checks every screen and sheet in both themes and all three text sizes against
// the rules in docs/android-app-model.md. Run `runChecks()` in the browser console.

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
      try { f.change(s); dress(el, s); el.innerHTML = phoneHtml(s); } catch (e) { found.push(`${tag}: cannot be drawn, ${e.message}`); el.remove(); continue; }
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
        if (r.height && r.height < 33.5) found.push(`${tag}: "${name.slice(0, 30)}" is only ${Math.round(r.height)}px tall`);
        if (b.classList.contains('btn') && !b.querySelector('svg')) found.push(`${tag}: button "${name}" has no icon`);
      }
      for (const b of el.querySelectorAll('.seg button')) if (!b.querySelector('svg')) found.push(`${tag}: a tab has no icon`);
      for (const s of el.querySelectorAll('.seg')) {
        const drawn = [...s.querySelectorAll('svg')].map(i => i.innerHTML);
        if (new Set(drawn).size < drawn.length) found.push(`${tag}: two options in "${s.getAttribute('aria-label')}" share an icon`);
      }
      for (const b of el.querySelectorAll('.seg button span')) if (b.scrollWidth > b.clientWidth + 1) found.push(`${tag}: tab "${b.innerText}" is cut`);
      if (el.querySelectorAll('.btn.primary').length + el.querySelectorAll('.p-page .ibtn.go, .p-page .shutter').length > 1 && !el.querySelector('.sheet'))
        found.push(`${tag}: more than one primary action on the page`);

      for (const a of el.querySelectorAll('[data-act]')) if (!ACTS[a.dataset.act]) found.push(`${tag}: tap "${a.dataset.act}" does nothing`);
      for (const a of el.querySelectorAll('[data-act="sheet"]')) if (!SHEETS[a.dataset.arg.split('|')[0]]) found.push(`${tag}: sheet "${a.dataset.arg}" does not exist`);
      for (const a of el.querySelectorAll('[data-act="go"]')) if (!PLACE[a.dataset.arg]) found.push(`${tag}: place "${a.dataset.arg}" does not exist`);
      if (el.querySelector('.sheet .ibtn[aria-label*="lose" i]')) found.push(`${tag}: a sheet has a close button`);

      const walk = document.createTreeWalker(el, NodeFilter.SHOW_TEXT);
      for (let n; (n = walk.nextNode());) {
        const t = n.nodeValue.trim();
        if (/\b[A-Z]{3,}\s+[A-Z]{2,}\b/.test(t) && t === t.toUpperCase() && !/^[A-Z]{2,5} \d/.test(t)) found.push(`${tag}: all capitals "${t.slice(0, 30)}"`);
        if ((t.match(/·/g) || []).length > 1) found.push(`${tag}: more than two facts on a line "${t.slice(0, 50)}"`);
        if (/[›»⌄▾▸—]/.test(t)) found.push(`${tag}: a text character used as a mark "${t.slice(0, 30)}"`);
        if (/\b(planned|fixture|prototype|unavailable|TODO)\b/i.test(t)) found.push(`${tag}: roadmap or placeholder wording "${t.slice(0, 40)}"`);
      }
      el.remove();
    }
  }

  for (const p of PLACES) {
    if (!SCREENS[p.id]) found.push(`no screen for ${p.id}`);
    if (pathTo(p.id).length > 3) found.push(`${p.id} is deeper than three levels`);
    let at = p.id, hops = 0;
    while (at !== 'home' && hops++ < 6) at = backTarget(at);
    if (at !== 'home') found.push(`Back from ${p.id} never reaches Home`);
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
