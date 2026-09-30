// The design system: every part in kit.js, the rules for using it, and a live
// example drawn by the part itself. The review page shows it in full, and the
// app shows the same list under More, Help and about, Design system.

const DEMO_SESSION = { title: 'Walk in the hills', at: 120, total: 480, paused: false, busy: false, volume: 35, speed: 1, rotate: 0, loop: 'Off', favorite: false, skip: 10, pending: {} };
const DEMO_MINE = { me: true, text: 'Play **Walk in the hills** on the Pi screen.', when: '18:40', files: [{ kind: 'Image', title: 'IMG 4410.jpg' }] };
const DEMO_REPLY = { me: false, text: 'Started it on the Pi screen, muted.', when: '18:41' };

// uses: the kit functions this entry covers, so the audit can count who calls them.
const PARTS = [
  { group: 'Page', name: 'Top bar', uses: ['topBar'],
    rules: ['A bar place shows its name. A child place shows the path to it and a Back arrow.', 'Always 52 high. It never wraps and never scrolls.', 'Actions for the whole page sit on its right as icons, three at most.'],
    demo: () => topBar('connection', ibtn('refresh', 'Check again', 'toast')) },
  { group: 'Page', name: 'Lead line', uses: ['lead'],
    rules: ['The first line of a page that reports on something: one dot, one sentence.', 'It states the worst thing that is true right now.'],
    demo: () => lead('good', 'Raspberry Pi is online') + lead('warn', 'Power is low') },
  { group: 'Page', name: 'Heading', uses: ['head'],
    rules: ['Only where the page is about one named thing: a film, a cover, a note.', 'A bar place has no heading. Its name is already in the top bar.'],
    demo: () => head('A Matter of Life and Death', status('good', 'Playing on Pi screen')) },
  { group: 'Page', name: 'Section', uses: ['section'],
    rules: ['A plain label over a group. Sentence case, never capitals.', 'Given an id it folds from its label and stays folded.'],
    demo: () => section('Devices', group(row({ icon: 'laptop', title: 'studio-mac', status: ['good', 'Online'] }))) },

  { group: 'Lists', name: 'Row and group', uses: ['row', 'group'],
    rules: ['One thing per row. A chevron only when the row opens a page or a sheet.', 'A row that acts in place has no chevron. A row with neither is plain text.', 'At most two facts on the second line, split by one dot.', 'A second action on a row is an icon at its end, never a second row.'],
    demo: () => group(
      row({ icon: 'folder', title: 'Films', sub: '14 items', act: 'toast', opens: true }) +
      row({ icon: 'history', title: 'Walk in the hills', sub: 'Pi screen · 7:36 left', progress: 0.25, act: 'toast', trailing: ibtn('play', 'Resume on Pi screen', 'toast', '', 'go', 17) }) +
      row({ icon: 'skip', title: '10 seconds', picked: true, act: 'toast' }) +
      row({ icon: 'volume', title: 'Starting volume', value: 'Muted', act: 'toast', opens: true }) +
      row({ icon: 'loop', title: 'Loop', trailing: toggle(true, 'toast', 'Loop') }) +
      row({ icon: 'screen', title: 'Play on Pi screen', sub: 'The Pi is offline', off: true }) +
      row({ icon: 'trash', danger: true, title: 'Delete', act: 'toast', opens: true })) },
  { group: 'Lists', name: 'Status', uses: ['status'],
    rules: ['A dot, then words. Colour never carries the meaning alone.', 'Green: it works now. Amber: wait, or look. Red: it failed. Grey: it is not running.', 'Only the words in the status vocabulary. A new state needs a new word agreed first.'],
    demo: () => group(row({ icon: 'pi', title: 'Raspberry Pi', status: ['good', 'Online'] }) + row({ icon: 'power', title: 'Power', status: ['warn', 'Low power'] }) +
      row({ icon: 'send', title: 'film-poster.jpg', status: ['bad', 'Failed'] }) + row({ icon: 'laptop', title: 'work-macbook', status: ['idle', 'Offline'] })) },
  { group: 'Lists', name: 'Tile', uses: ['tile', 'tiles'],
    rules: ['The same facts as a row, for a grid of equals: capabilities, readings, player settings.', 'Two across. One across at the largest text size.'],
    demo: () => tiles(tile({ icon: 'media', title: 'Media', status: ['good', '6 videos'], act: 'toast' }) + tile({ icon: 'memory', title: 'Memory free', big: '4.8 GB', small: 'Falling over the last hour' })) },
  { group: 'Lists', name: 'Facts', uses: ['facts', 'defs'],
    rules: ['Name on the left, value on the right. For things you read and do not change.', 'A definition list names a tool and says what it does, in one line.'],
    demo: () => facts([['Kind', 'Laptop'], ['Address', '100.72.3.41']]) + defs([['Find media', 'Search the drives by name'], ['Play media', 'Play a file on the Pi screen']]) },

  { group: 'Actions', name: 'Button', uses: ['btn', 'btns'],
    rules: ['Filled is rare. A page has one only when the page exists to do that one thing: Send, Save, Install, Create.', 'Tinted confirms a choice inside a sheet: Replace, Move, Add.', 'Outlined is every other button. Quiet is for undoing or clearing.', 'An action for the whole page is an icon in the top bar, not a button in the page.', 'Every button has an icon and a verb.'],
    demo: () => btns(btn('Save', 'check', 'toast', '', 'primary'), btn('Replace', 'play', 'toast', '', 'tonal'), btn('Check again', 'refresh', 'toast'), btn('Clear framing', 'refresh', 'toast', '', 'quiet'), btn('Delete', 'trash', 'toast', '', 'danger')) },
  { group: 'Actions', name: 'Icon button', uses: ['ibtn'],
    rules: ['48 by 48 to the finger, whatever the icon size.', 'It always has a spoken name. Accent colour means it is on.'],
    demo: () => btns(ibtn('search', 'Search', 'toast'), ibtn('favorite', 'Favorite', 'toast', '', 'quiet'), ibtn('favorite', 'Remove favorite', 'toast', '', 'on'), ibtn('play', 'Resume', 'toast', '', 'go', 17)) },
  { group: 'Actions', name: 'Tabs', uses: ['seg'],
    rules: ['Looks at the same place, so switching one is not navigation and Back ignores it.', 'Each has an icon and a word. No two in one set share an icon.', 'More than fit: the row slides and fades at the edge. It never wraps.'],
    demo: () => seg([['Files', 'files'], ['Videos', 'video'], ['History', 'history'], ['Access', 'access']], 'Files', 'toast', 'Media views') },
  { group: 'Actions', name: 'Path line', uses: ['pathLine'],
    rules: ['Where you are inside something browsed in place, such as a drive. Tapping a step goes there.', 'It is not navigation: the page stays the same and Back ignores it.'],
    demo: () => pathLine([['Pi USB', 'toast', '', 'files'], ['Shows', '', '', 'folder']]) },
  { group: 'Actions', name: 'Switch', uses: ['toggle'],
    rules: ['For something that is on or off and takes effect at once.', 'It sits at the end of the row that names it.'],
    demo: () => group(row({ icon: 'download', title: 'Receive on this phone', sub: 'Other devices can send to it', trailing: toggle(true, 'toast', 'Receive on this phone') })) },

  { group: 'Input', name: 'Field', uses: ['field', 'labelled'],
    rules: ['A label above, one line of help below when the name is not enough.', 'The hint is an example of what to type, never an instruction.'],
    demo: () => labelled('Raspberry Pi address', field({ id: 'demo', hint: 'raspberrypi', value: 'raspberrypi', icon: 'pi' }), 'Where Media, Chat, the camera and Notes live.') },
  { group: 'Input', name: 'Slider', uses: ['range'],
    rules: ['The value is written above it and changes as you drag.', 'Both ends are labelled when they are not obvious.'],
    demo: () => range({ id: 'demo', label: 'Volume', shown: '35%', value: 35, min: 0, max: 100, step: 5, low: 'Muted', high: '100%' }) },
  { group: 'Input', name: 'Editor', uses: ['editor', 'richEditor'],
    rules: ['Rich edits the formatted text. Plain edits the Markdown. Both save the same note.'],
    demo: () => editor('demo', '# Pi display ideas\n\n- A cover image per season', 'Note, as Markdown') },
  { group: 'Input', name: 'Colour choice', uses: ['swatches', 'swatchBig'],
    rules: ['Circles only, a ring and a check on the chosen one.', 'Every offered colour carries white text at 4.5 to 1 or better.'],
    demo: S => swatches(ACCENTS, S.accent, S.custom) },

  { group: 'Messages', name: 'Notice', uses: ['notice'],
    rules: ['Says what is wrong in one sentence and offers the one place that can fix it.', 'It stays until the state changes. It is not a pop-up.'],
    demo: () => notice('info', 'The Raspberry Pi cannot be reached. What is saved on this phone still works.', btn('Open Connection', 'wifi', 'toast')) + notice('warn', 'Power is low. The picture may stop.') + notice('bad', 'The Pi did not answer, so nothing changed.') },
  { group: 'Messages', name: 'Empty state', uses: ['empty'],
    rules: ['Says what belongs here and how it gets here.', 'One way forward at most, and it is tinted or outlined, not filled.'],
    demo: () => empty('pin', 'No pins yet', 'Save a link or a snippet to find it again.', btn('New pin', 'plus', 'toast', '', 'tonal')) },
  { group: 'Messages', name: 'Quiet line', uses: ['noteLine'],
    rules: ['A small aside under a control. Never the only place a fact is told.'],
    demo: () => noteLine(['device', 'screen'], 'Applies to every screen and the system bars.') },
  { group: 'Messages', name: 'Card and text', uses: ['card', 'markdown'],
    rules: ['Long text the person reads: a note, a guide, an answer.', 'Headings, lists, tables, code and links are drawn. Nothing else is.'],
    demo: () => card(markdown('## Ask\n\nFind a film, or check how the Pi is doing.\n\n- What is on the Pi screen?\n- Is the Pi running hot?')) },
  { group: 'Messages', name: 'Sheet', uses: ['sheet'],
    rules: ['A short choice, one value, a confirmation, or the facts about one row. Anything larger is a page.', 'It has no close button. Drag it down, tap outside it, or press Back.', 'Buttons appear only when it changes something, and the one that keeps things as they are comes first.'],
    demo: () => group(row({ icon: 'source', title: 'Choose a source', sub: 'A sheet with three rows', act: 'toast', opens: true })) },

  { group: 'Media', name: 'Picture', uses: ['picture', 'framedPicture', 'coverGrid'],
    rules: ['Where a picture or a video goes. A tag in its corner says where it is being shown.', 'While it loads, a light sweeps across it. It is never an empty box.'],
    demo: () => picture({ icon: 'video', size: 40, mode: 'live', tag: ['screen', 'On the Pi screen'] }) },
  { group: 'Media', name: 'Player', uses: ['player'],
    rules: ['The same controls for the Pi screen and this phone, in the same order.', 'Pause or Resume is the one filled control. Stop is red and sits last.', 'Every control under the transport says its name. Rotate and Loop say applying while they wait.', 'A live source has no position, so it shows Stop and its settings only.'],
    demo: () => player(DEMO_SESSION, 'Pi screen') },
  { group: 'Media', name: 'Camera controls', uses: ['shoot'],
    rules: ['The shutter is the one filled control on the camera page. Record sits beside it, smaller and red.'],
    demo: () => shoot(true, false) },

  { group: 'Conversation', name: 'Message', uses: ['bubble', 'msgs', 'thinking'],
    rules: ['Yours sits right in a tint of the primary colour. The assistant sits left on the surface.', 'The time is inside the bubble. What is attached sits above the words.', 'Tap a message for Copy, Fork, and Regenerate on a reply or Edit on your own.'],
    demo: () => msgs(bubble(DEMO_MINE, 0) + thinking() + bubble(DEMO_REPLY, 1, true)) },
  { group: 'Conversation', name: 'Result card', uses: ['resultCard'],
    rules: ['What a tool gave back, drawn for its kind, named by the tool that made it.', 'A media card carries Pause and Stop while it plays, so the answer can be used where it is read.', 'Tap a card for everything else that kind of item can do.'],
    demo: () => msgs(
      resultCard({ kind: 'media', tool: 'Play media', title: 'Walk in the hills', output: 'Pi screen' }, '0|0', DEMO_SESSION) +
      resultCard({ kind: 'control', tool: 'Control playback', title: 'Volume', facts: [['Volume', '35%'], ['Before', 'Muted']] }, '0|0') +
      resultCard({ kind: 'image', tool: 'Camera', title: 'Camera still' }, '0|0') +
      resultCard({ kind: 'file', tool: 'Share a Pi file', title: 'Drive report', sub: 'Text file, 4 kB' }, '0|0') +
      resultCard({ kind: 'devices', tool: 'Your devices', title: 'Your devices', devices: [['studio-mac', true], ['work-macbook', false]] }, '0|0')) },
  { group: 'Conversation', name: 'Message box', uses: ['composer', 'chip', 'convoHead'],
    rules: ['One box holds the words, what is attached, the way to add more, the model and Send.', 'It grows with the text up to six lines, and opens taller when asked.', 'Send is filled only when there is something to send.'],
    demo: () => composer({ draft: 'Find the three shortest tutorials.', tall: false, long: false, attachment: { kind: 'Image', title: 'IMG 4410.jpg' }, model: 'gemini-3.8-flash medium', ready: true, canSend: true }) },

  { group: 'Android', name: 'Share menu', uses: ['appTiles'],
    rules: ["Android's own menu, shown only where csync hands an item to it. csync never draws its own list of apps."],
    demo: () => appTiles(SHARE_APPS.slice(0, 3), 'toast') }
];

/** Rewire an example so tapping it only says it is an example. */
const sample = html => html.replace(/data-act="[^"]*" data-arg="[^"]*"/g, 'data-act="toast" data-arg="This is an example"').replace(/data-in="[^"]*"/g, 'data-in="demo"');

/** The design system as a place in the app: every part, its first rule, and an example. */
function showcaseBody(S) {
  const groups = [...new Set(PARTS.map(p => p.group))];
  return head('Design system', `${plural(PARTS.length, 'part')}. Every screen is built from these.`) +
    groups.map(g => section(g, PARTS.filter(p => p.group === g).map(p => section(p.name, sample(p.demo(S)) + noteLine('info', p.rules[0]))).join(''), `ds-${g}`, S.folded[`ds-${g}`])).join('');
}

// The review page's version, with every rule, the tokens, and who uses each part.

const TOKENS = [
  ['bg', 'Page'], ['surface', 'Groups, sheets, bars'], ['surface2', 'Icon tiles, tracks'], ['line', 'Borders'],
  ['text', 'Main text'], ['dim', 'Second lines'], ['faint', 'Asides, chevrons'],
  ['accent-fill', 'Filled controls'], ['accent', 'Accent text, what is on'],
  ['good', 'It works now'], ['warn', 'Wait, or look'], ['bad', 'It failed'], ['idle', 'Not running']
];
const TYPE = [['Page heading', 22, 700], ['Lead line', 18, 650], ['Bar place name', 17, 650], ['Row title', 15, 600], ['Body', 14.5, 400], ['Second line, labels', 13, 400], ['Aside', 12.5, 400]];
const SHAPE = [['Tap target', '48 by 48 at least'], ['Page margin', '16'], ['Gap between blocks', '18'], ['Gap inside a block', '8 to 12'], ['Group corner', '16'], ['Button and field corner', '13 to 14'], ['Sheet corner', '24, top only'], ['Top bar', '52 high'], ['Bottom bar', '62 high, five places']];
const NEVER = ['An ellipsis, in text or in a hint', 'All capitals', 'A text character used as an arrow or a mark', 'More than two facts on one line', 'A second name for an action that already has one', 'A close button on a sheet', 'A button without an icon', 'A word about what is coming later'];

function usedBy(names) {
  const calls = text => names.some(n => new RegExp(`\\b${n}\\(`).test(text));
  const places = PLACES.filter(p => { const s = SCREENS[p.id]; return calls(String(s.body) + String(s.actions || '') + String(s.composer || '')); }).map(p => p.label);
  const sheets = Object.keys(SHEETS).filter(k => calls(String(SHEETS[k])));
  return { places, sheets };
}

function renderSystem() {
  const el = document.querySelector('#system');
  if (!KIT_AUDIT) { kitAudit().then(renderSystem); return; }
  const probe = getComputedStyle(phone);
  const token = name => probe.getPropertyValue('--p-' + name).trim();
  const block = (title, body) => `<section class="sys-block"><h2>${esc(title)}</h2>${body}</section>`;
  const uses = PARTS.map(p => usedBy(p.uses));
  const unused = PARTS.filter((p, i) => !uses[i].places.length && !uses[i].sheets.length).map(p => p.name);

  const audit = `<div class="sys-audit ${KIT_AUDIT.problems.length ? 'bad' : 'good'}"><b>${KIT_AUDIT.problems.length ? `${KIT_AUDIT.problems.length} places draw their own markup` : 'Every screen and sheet is drawn only by these parts'}</b>` +
    `<span>${KIT_AUDIT.lines} lines of screens.js and sheets.js read. ${KIT_AUDIT.problems.length ? '' : 'None contains a tag, a class or a style of its own.'}</span>` +
    (KIT_AUDIT.problems.length ? `<ul>${KIT_AUDIT.problems.slice(0, 12).map(p => `<li>${esc(p)}</li>`).join('')}</ul>` : '') +
    (unused.length ? `<span>Called only through another part or the phone frame: ${esc(unused.join(', '))}.</span>` : '') + '</div>';

  const colours = `<div class="sys-swatches">${TOKENS.map(([name, use]) => `<div><i style="background:${token(name)}"></i><b>${name}</b><span>${token(name)}</span><span>${esc(use)}</span></div>`).join('')}</div>`;
  const type = `<div class="sys-type">${TYPE.map(([name, px, weight]) => `<div><span style="font-size:${px}px;font-weight:${weight}">${esc(name)}</span><small>${px} · ${weight}</small></div>`).join('')}</div>`;
  const list = pairs => `<dl class="facts">${pairs.map(([k, v]) => `<dt>${esc(k)}</dt><dd>${esc(v)}</dd>`).join('')}</dl>`;
  const words = list(Object.entries(STATUS_WORDS).map(([tone, w]) => [{ good: 'Green', warn: 'Amber', bad: 'Red', idle: 'Grey' }[tone], w.join(', ')]));
  const icons = `<div class="sys-icons">${Object.keys(SHAPES).map(n => `<span title="${n}">${icon(n, 20)}<small>${n}</small></span>`).join('')}</div>`;
  const never = `<ul class="sys-rules">${NEVER.map(n => `<li>${esc(n)}</li>`).join('')}</ul>`;

  const parts = [...new Set(PARTS.map(p => p.group))].map(g => `<h2 class="sys-group">${esc(g)}</h2>` + PARTS.map((p, i) => p.group !== g ? '' :
    `<article class="sys-part"><div><h3>${esc(p.name)}</h3><ul class="sys-rules">${p.rules.map(r => `<li>${esc(r)}</li>`).join('')}</ul>` +
    `<p class="sys-used">${uses[i].places.length || uses[i].sheets.length ? `Used on ${plural(uses[i].places.length, 'screen')} and ${plural(uses[i].sheets.length, 'sheet')}${uses[i].places.length ? ': ' + esc(uses[i].places.slice(0, 8).join(', ')) + (uses[i].places.length > 8 ? ' and more' : '') : ''}.` : 'Called through another part or the phone frame.'}</p></div>` +
    `<div class="phone bare" data-part="${i}"></div></article>`).join('')).join('');

  el.innerHTML = `<div class="sys-intro"><h1>Design system</h1><p>${PARTS.length} parts in kit.js. The examples below are drawn by the parts themselves, in the theme, text size and colour chosen above, so this page cannot drift from the app.</p>${audit}</div>` +
    `<div class="sys-found">${block('Colour', colours)}${block('Type', type)}${block('Size and shape', list(SHAPE))}${block('Status words', words)}${block('Never appears', never)}</div>` +
    block('Icons, one per idea', icons) + parts;
  for (const box of el.querySelectorAll('[data-part]')) {
    dress(box, S);
    box.innerHTML = sample(PARTS[box.dataset.part].demo(S));
    tidy(box);
  }
}
