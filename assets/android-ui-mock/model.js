// Where every screen of the phone app lives: its parent, its views and its icon.
// Breadcrumbs, Back and the bottom-bar highlight are all read from this list.
// The reasoning is in docs/android-app-model.md section 3.
//
// kind 'bar' is one of the five bottom-bar places; 'page' is a child place.
// views are looks at the same place, so switching one is not navigation.
// built and asks feed the review panel only and never appear in the phone.

const PLACES = [
  { id: 'home', kind: 'bar', label: 'Home', icon: 'home', built: 'partly',
    asks: ['G-07', 'H-01', 'H-02', 'H-04', 'H-05', 'H-06', 'H-07', 'H-08', 'H-09'] },
  { id: 'search', kind: 'page', parent: 'home', label: 'Search', icon: 'search', built: 'yes',
    views: ['All', 'Media', 'Chats', 'Notes', 'Devices'], asks: ['S-01', 'S-02', 'S-03'] },

  { id: 'media', kind: 'bar', label: 'Media', icon: 'media', built: 'partly',
    views: ['Files', 'Videos', 'History', 'Access'],
    asks: ['M-01', 'M-02', 'M-03', 'M-04', 'M-06', 'M-09', 'M-10', 'M-11', 'M-12', 'M-13', 'M-14', 'G-24'] },
  { id: 'pi-screen', kind: 'page', parent: 'media', label: 'Pi screen', icon: 'screen', built: 'partly',
    asks: ['P-02', 'P-03', 'P-04', 'P-05', 'P-06', 'P-07', 'P-08', 'P-09', 'P-10', 'P-11', 'P-21', 'P-24', 'C-01', 'C-07'] },
  { id: 'covers', kind: 'page', parent: 'pi-screen', label: 'Covers', icon: 'image', built: 'no',
    asks: ['C-02', 'C-03', 'C-04', 'C-05', 'C-06'] },
  { id: 'phone-player', kind: 'page', parent: 'media', label: 'This phone', icon: 'device', built: 'partly',
    asks: ['P-02', 'P-04', 'P-10', 'P-21', 'O-03', 'O-07'] },

  { id: 'share', kind: 'bar', label: 'Share', icon: 'share', built: 'partly',
    asks: ['SH-01', 'SH-02', 'SH-03', 'SH-11', 'SH-13', 'SH-14'] },
  { id: 'received', kind: 'page', parent: 'share', label: 'Received', icon: 'download', built: 'partly',
    asks: ['SH-11'] },
  { id: 'incoming', kind: 'page', parent: 'share', label: 'From another app', icon: 'upload', built: 'partly',
    views: ['Video', 'Image', 'YouTube', 'Instagram', 'File'],
    asks: ['SH-04', 'SH-05', 'SH-06', 'SH-07', 'SH-08', 'SH-09', 'SH-10', 'SH-12', 'N-09', 'O-06'] },

  { id: 'chat', kind: 'bar', label: 'Chat', icon: 'chat', built: 'yes',
    views: ['All', 'Favorites', 'Archived', 'Tools'],
    asks: ['CH-19', 'CH-20', 'CH-21', 'CH-22', 'CH-38', 'CH-39'] },
  { id: 'conversation', kind: 'page', parent: 'chat', label: 'Conversation', icon: 'chat', built: 'partly',
    asks: ['CH-01', 'CH-02', 'CH-03', 'CH-04', 'CH-05', 'CH-06', 'CH-07', 'CH-08', 'CH-09', 'CH-10', 'CH-11',
      'CH-12', 'CH-13', 'CH-15', 'CH-16', 'CH-17', 'CH-18', 'CH-23', 'CH-24', 'CH-25', 'CH-26', 'CH-27', 'CH-28',
      'CH-29', 'CH-30', 'CH-31', 'CH-32', 'CH-33', 'CH-35', 'CH-36', 'CH-37', 'CH-40'] },

  { id: 'more', kind: 'bar', label: 'More', icon: 'more', built: 'yes',
    asks: ['MO-01', 'MO-02', 'MO-03', 'MO-04'] },
  { id: 'camera', kind: 'page', parent: 'more', label: 'Pi camera', icon: 'camera', built: 'yes',
    asks: ['CA-01', 'CA-02', 'CA-03', 'CA-04'] },
  { id: 'captures', kind: 'page', parent: 'camera', label: 'Captures', icon: 'photo', built: 'yes',
    asks: ['CA-01', 'N-08'] },
  { id: 'notes', kind: 'page', parent: 'more', label: 'Notes', icon: 'note', built: 'yes',
    views: ['Notes', 'Pins'], asks: ['N-01', 'N-05', 'N-06', 'N-10'] },
  { id: 'note', kind: 'page', parent: 'notes', label: 'Note', icon: 'note', built: 'yes',
    views: ['Preview', 'Rich', 'Plain'], asks: ['N-01', 'N-02', 'N-03', 'N-08', 'SH-12'] },
  { id: 'pin', kind: 'page', parent: 'notes', label: 'Pin', icon: 'pin', built: 'partly',
    asks: ['N-06', 'N-07', 'N-08'] },
  { id: 'tools', kind: 'page', parent: 'more', label: 'Tools', icon: 'tools', built: 'partly',
    asks: ['T-05', 'T-06', 'PI-07'] },
  { id: 'process', kind: 'page', parent: 'tools', label: 'Process monitor', icon: 'cpu', built: 'partly',
    asks: ['T-02', 'T-03', 'T-04', 'T-06', 'T-08'] },
  { id: 'widgets', kind: 'page', parent: 'tools', label: 'Widgets', icon: 'launcher', built: 'partly',
    asks: ['T-01', 'T-07'] },
  { id: 'settings', kind: 'page', parent: 'more', label: 'Settings', icon: 'settings', built: 'partly',
    asks: ['SE-20'] },
  { id: 'connection', kind: 'page', parent: 'settings', label: 'Connection', icon: 'wifi', built: 'partly',
    asks: ['PI-05'] },
  { id: 'playback', kind: 'page', parent: 'settings', label: 'Playback', icon: 'play', built: 'no',
    asks: ['SH-08'] },
  { id: 'assistant', kind: 'page', parent: 'settings', label: 'Assistant', icon: 'chat', built: 'partly',
    asks: ['SE-18', 'SE-19', 'CH-12'] },
  { id: 'appearance', kind: 'page', parent: 'settings', label: 'Appearance', icon: 'palette', built: 'yes',
    asks: ['SE-01', 'SE-02', 'SE-03', 'SE-04', 'SE-05', 'SE-06', 'SE-07', 'SE-08', 'SE-09', 'SE-12', 'SE-16', 'SE-17'] },
  { id: 'guide', kind: 'page', parent: 'more', label: 'Assistant guide', icon: 'help', built: 'partly',
    asks: ['SE-10'] },
  { id: 'help', kind: 'page', parent: 'more', label: 'Help and about', icon: 'info', built: 'partly',
    asks: ['SE-11'] }
];

const PLACE = Object.fromEntries(PLACES.map(p => [p.id, p]));

/** The path from the bar place down to this place, bar place first. */
function pathTo(id) {
  const path = [];
  for (let at = id; at; at = PLACE[at].parent) path.unshift(at);
  return path;
}

/** The bar place that owns this place; this is what the bottom bar highlights. */
function barOf(id) { return pathTo(id)[0]; }

/** Where Back goes from this place with nothing open on top of it. */
function backTarget(id) {
  const place = PLACE[id];
  if (place.parent) return place.parent;
  return id === 'home' ? null : 'home';
}

const BAR = PLACES.filter(p => p.kind === 'bar').map(p => p.id);

if (typeof module !== 'undefined') module.exports = { PLACES, PLACE, pathTo, barOf, backTarget, BAR };
