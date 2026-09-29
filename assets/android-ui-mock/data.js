// Sample content for the mock. Shapes follow what the Pi services return, so a
// screen that works with this data works with the real thing.

const DEVICES = [
  { name: 'Raspberry Pi', kind: 'pi', online: true, hub: true, address: '100.64.0.9' },
  { name: 'pixel-8', kind: 'device', online: true, self: true, address: '100.80.14.2' },
  { name: 'studio-mac', kind: 'laptop', online: true, address: '100.72.3.41' },
  { name: 'galaxy-tab', kind: 'device', online: true, address: '100.91.7.18' },
  { name: 'work-macbook', kind: 'laptop', online: false, address: '100.66.20.5', seen: 'Yesterday' },
  { name: 'living-room-pc', kind: 'desktop', online: false, address: '100.70.9.33', seen: 'Monday' }
];

const DRIVES = [
  { name: 'Pi USB', items: 123, smb: 'smb://raspberrypi/Pi-USB', ftp: 'ftp://raspberrypi/Pi-USB' },
  { name: 'Elements', items: 418, smb: 'smb://raspberrypi/Elements', ftp: 'ftp://raspberrypi/Elements' }
];

// kind: folder | video | image | audio | doc
const LIBRARY = {
  '': [
    { kind: 'folder', title: 'Films', count: 14 },
    { kind: 'folder', title: 'Shows', count: 38 },
    { kind: 'folder', title: 'Tutorials', count: 61 },
    { kind: 'folder', title: 'Shared', count: 10 },
    { kind: 'video', title: 'Walk in the hills', file: 'Walk_in_the_hills.mp4', length: '8 min', size: '212 MB' },
    { kind: 'image', title: 'Desk at sunset', file: 'desk-sunset.jpg', size: '1.8 MB' },
    { kind: 'doc', title: 'Projector manual', file: 'projector-manual.pdf', size: '4.1 MB' }
  ],
  Shows: [
    { kind: 'video', title: "Blackadder's Christmas Carol", file: 'Blackadder.S00E02.Blackadders.Christmas.Carol.1080p.BluRay.EAC3.2.0.1080p.x265-iVy.mkv', length: '43 min', size: '1.4 GB' },
    { kind: 'video', title: 'The Thick of It, series 1 episode 1', file: 'The.Thick.of.It.S01E01.720p.mkv', length: '29 min', size: '640 MB' },
    { kind: 'video', title: 'Yes Minister, Open Government', file: 'Yes.Minister.S01E01.Open.Government.mkv', length: '30 min', size: '590 MB' }
  ],
  Films: [
    { kind: 'video', title: 'A Matter of Life and Death', file: 'A.Matter.of.Life.and.Death.1946.1080p.mkv', length: '1 h 44 min', size: '3.2 GB' },
    { kind: 'video', title: 'The Red Shoes', file: 'The.Red.Shoes.1948.1080p.mkv', length: '2 h 13 min', size: '4.0 GB' }
  ],
  Tutorials: [
    { kind: 'video', title: 'Adjustable bend', file: 'Adjustable_Bend.wmv', length: '4 min', size: '38 MB' },
    { kind: 'video', title: 'Bamboo pole lashing', file: 'Bamboo_Pole_Lashing.wmv', length: '6 min', size: '52 MB' }
  ],
  Shared: [
    { kind: 'image', title: 'Film poster', file: 'film-poster.jpg', size: '940 kB' },
    { kind: 'doc', title: 'Notes from the call', file: 'notes.txt', size: '4 kB' }
  ]
};

const VIDEOS = [
  { kind: 'video', title: 'Adjustable bend', folder: 'Tutorials', file: 'Adjustable_Bend.wmv', length: '4 min', size: '38 MB' },
  { kind: 'video', title: 'A Matter of Life and Death', folder: 'Films', file: 'A.Matter.of.Life.and.Death.1946.1080p.mkv', length: '1 h 44 min', size: '3.2 GB' },
  { kind: 'video', title: 'Bamboo pole lashing', folder: 'Tutorials', file: 'Bamboo_Pole_Lashing.wmv', length: '6 min', size: '52 MB' },
  { kind: 'video', title: "Blackadder's Christmas Carol", folder: 'Shows', file: 'Blackadder.S00E02.Blackadders.Christmas.Carol.1080p.BluRay.EAC3.2.0.1080p.x265-iVy.mkv', length: '43 min', size: '1.4 GB' },
  { kind: 'video', title: 'The Red Shoes', folder: 'Films', file: 'The.Red.Shoes.1948.1080p.mkv', length: '2 h 13 min', size: '4.0 GB' },
  { kind: 'video', title: 'Walk in the hills', folder: 'Pi USB', file: 'Walk_in_the_hills.mp4', length: '8 min', size: '212 MB' }
];

// seconds are kept so progress bars and resume labels come from one number
const HISTORY = [
  { title: 'F-Droid 2.0, the biggest update in years', source: 'YouTube', output: 'Pi screen', at: 312, total: 778 },
  { title: "Blackadder's Christmas Carol", source: 'Pi USB', output: 'This phone', at: 10, total: 2580 },
  { title: 'Walk in the hills', source: 'Pi USB', output: 'Pi screen', at: 24, total: 480 },
  { title: 'A Matter of Life and Death', source: 'Elements', output: 'Pi screen', at: 3120, total: 6240 }
];

const SENT = [
  { title: 'film-poster.jpg', kind: 'Image', to: 'studio-mac', when: 'Today', time: '10:22', ok: true },
  { title: 'Meeting address', kind: 'Text', to: 'studio-mac', when: 'Yesterday', time: '18:06', ok: true },
  { title: 'camera-photo.jpg', kind: 'Image', to: 'galaxy-tab', when: 'Monday', time: '09:14', ok: true }
];

const RECEIVED = [
  { title: 'Notes from the call', kind: 'Text', from: 'studio-mac', when: 'Today', time: '11:40', body: 'Projector arrives Thursday. Bring the long HDMI cable.' },
  { title: 'film-poster.jpg', kind: 'Image', from: 'studio-mac', when: 'Yesterday', time: '17:02' },
  { title: 'Walk in the hills', kind: 'Video', from: 'galaxy-tab', when: 'Monday', time: '08:51' }
];

const THREADS = [
  { id: 't1', title: 'Plan a movie night', when: 'Today', count: 4, favorite: true, archived: false, tokens: 12400,
    messages: [
      { me: true, text: 'Find **A Matter of Life and Death** on Elements and play it on the Pi screen. [Film notes](https://example.org/notes).', when: '18:40' },
      { thinking: true },
      { me: false, text: 'Found it on Elements and started it on the Pi screen, muted.', when: '18:41',
        results: [
          { kind: 'media', title: 'A Matter of Life and Death', sub: 'Started on Pi screen' },
          { kind: 'facts', title: 'Playback status', sub: 'Read at 18:41' }
        ] },
      { me: true, text: 'What volume is it at?', when: '18:42' },
      { me: false, text: 'Volume is 0. The Pi screen starts muted, so raise it from the player when you are ready.', when: '18:42' }
    ] },
  { id: 't2', title: 'Find a clip on Elements', when: 'Yesterday', count: 8, favorite: false, archived: false, messages: [
      { me: true, text: 'Which knot tutorials are shorter than five minutes?', when: '09:12' },
      { me: false, text: 'One so far:\n\n- Adjustable bend, 4 minutes\n\nBamboo pole lashing runs 6 minutes.', when: '09:12',
        results: [{ kind: 'image', title: 'Camera still', sub: 'Image from the Pi camera' }, { kind: 'file', title: 'Drive report', sub: 'Text file, 4 kB' }] }
    ] },
  { id: 't3', title: 'Camera troubleshooting', when: 'Tuesday', count: 6, favorite: false, archived: true, messages: [
      { me: true, text: 'The camera preview is dark.', when: '21:03' },
      { me: false, text: 'The lens cap is detected as closed in the last three photos. Remove it and try again.', when: '21:03' }
    ] }
];

const ASSISTANT_TOOLS = [
  { group: 'Media', tools: [
    ['Find media', 'Search the drives by name'],
    ['Play media', 'Play a file or a YouTube link on the Pi screen'],
    ['Control playback', 'Pause, resume, seek, stop, volume and speed on a named output'],
    ['Playback status', 'What each output is playing now'],
    ['Check media', 'Drives, power and the screen connection'] ] },
  { group: 'Camera', tools: [['Camera', 'Check the camera, take a photo or record a clip']] },
  { group: 'Devices and files', tools: [
    ['Pi health', 'Storage, memory, uptime and services'],
    ['Your devices', 'Named devices and whether each is online'],
    ['Send to a device', 'Send text to a named device'],
    ['Share a Pi file', 'Bring a file from the Pi into the conversation'] ] },
  { group: 'Notes', tools: [['Notes', 'Read, write and delete notes on the Pi']] },
  { group: 'Skills and commands', tools: [
    ['Saved skills', 'List and read saved skills'],
    ['Pi commands', 'Run a command on the Pi when the Pi allows it'] ] }
];

const MODELS = [
  { provider: 'Gemini', icon: 'launcher', available: true, models: ['gemini-3.8-flash', 'gemini-3.5-flash', 'gemini-2.5-flash'],
    efforts: ['Off', 'Low', 'Medium', 'High'] },
  { provider: 'OpenAI', icon: 'all', available: false, models: ['gpt-5-mini'], efforts: ['Low', 'Medium', 'High'] },
  { provider: 'Claude', icon: 'sun', available: false, models: ['claude-sonnet-5', 'claude-haiku-4-5'], efforts: ['Off', 'Low', 'Medium', 'High'] }
];

const NOTES = [
  { id: 'n1', title: 'Things to try on the phone', edited: 'Edited today',
    body: '# Things to try\n\nOpen **More**, then **Tools**, and update the app from the Pi.\n\n| Area | Try |\n| --- | --- |\n| Media | Resume a film on the Pi screen |\n| Share | Send a photo to studio-mac |\n\n```mermaid\ngraph LR\nPhone --> Pi\nPi --> Screen\n```' },
  { id: 'n2', title: 'Pi display ideas', edited: 'Edited on Monday',
    body: '# Pi display ideas\n\nKeep the screen useful when nothing is playing.\n\n- A cover image per season\n- The camera when someone is at the door' }
];

const PINS = [
  { id: 'p1', title: 'F-Droid 2.0 release notes', link: 'https://f-droid.org/2026/09/20/fdroid-2.html', tags: ['android', 'read later'], about: 'New index format and repository mirrors.' },
  { id: 'p2', title: 'Projector input order', text: 'HDMI 2 is the Pi. HDMI 1 is the laptop dock.', tags: ['hardware'], about: '' }
];

const CAPTURES = [
  { day: 'Today', items: [
    { id: 'c1', kind: 'Photo', when: '7:22 AM', size: '20 kB' },
    { id: 'c2', kind: 'Recording', length: '18 s', when: '7:20 AM', size: '2.0 MB' } ] },
  { day: 'Yesterday', items: [
    { id: 'c3', kind: 'Photo', when: '11:47 PM', size: '18 kB' },
    { id: 'c4', kind: 'Photo', when: '8:43 PM', size: '14 kB' } ] }
];

const COVERS = ['Desk at sunset', 'Mountain light', 'Blueprint', 'Harbour at night'];
const COVER_ART = ['linear-gradient(160deg,#6b4a2f,#a8683a 45%,#2f3d52)', 'linear-gradient(160deg,#35506b,#8aa6b8 50%,#e8d9c0)', 'linear-gradient(160deg,#10294a,#2768b2 60%,#0e1d33)', 'linear-gradient(160deg,#0d1422,#2a3550 55%,#c98a3a)'];

const WIDGETS = [
  { name: 'xkcd', kind: 'Launcher widget', icon: 'image', shows: 'The latest comic', updates: 'Three times a week' },
  { name: 'Media remote', kind: 'Launcher widget', icon: 'play', shows: 'What the Pi screen is playing, with Pause and Stop', updates: 'While something plays' },
  { name: 'Pi camera', kind: 'Quick Settings tile', icon: 'camera', shows: 'Opens the live picture', updates: 'When tapped' },
  { name: 'Send the clipboard', kind: 'Quick Settings tile', icon: 'clipboard', shows: 'Sends the clipboard to your last device', updates: 'When tapped' }
];

const BUSY_APPS = [
  { name: 'Chrome', memory: '612 MB', cpu: '9%', trend: 'Memory rising' },
  { name: 'csync', memory: '148 MB', cpu: '2%', trend: 'Level' },
  { name: 'Photos', memory: '131 MB', cpu: '1%', trend: 'Level' }
];

// fill passes 4.5:1 with white text; onDark and onLight are the text colours
const ACCENTS = [
  { id: 'coral', name: 'Coral', fill: '#CC4620', onDark: '#FF8A66', onLight: '#B23A17' },
  { id: 'teal', name: 'Teal', fill: '#08796F', onDark: '#70D9C7', onLight: '#08695F' },
  { id: 'violet', name: 'Violet', fill: '#6546D8', onDark: '#AD9AFF', onLight: '#5A3CCB' },
  { id: 'rust', name: 'Rust', fill: '#B33B0B', onDark: '#F8A47A', onLight: '#A3330B' },
  { id: 'blue', name: 'Blue', fill: '#2768B2', onDark: '#8BBCF4', onLight: '#235A99' },
  { id: 'leaf', name: 'Leaf', fill: '#287D45', onDark: '#8FDFA7', onLight: '#246C3D' },
  { id: 'rose', name: 'Rose', fill: '#B23773', onDark: '#F4A1C6', onLight: '#982A62' }
];
