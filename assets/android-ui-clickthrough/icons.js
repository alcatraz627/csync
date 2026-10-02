const shapes = {
  home: '<path d="M3 10 12 3l9 7v10a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1z"/><path d="M9 21v-7h6v7"/>',
  media: '<rect x="3" y="3" width="8" height="8" rx="1"/><rect x="13" y="3" width="8" height="8" rx="1"/><rect x="3" y="13" width="8" height="8" rx="1"/><path d="m15 13 6 4-6 4z"/>',
  share: '<circle cx="18" cy="4.5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19.5" r="3"/><path d="M8.5 10.6 15.4 6M8.5 13.4l6.9 4" stroke="currentColor" stroke-width="2.4" fill="none"/>',
  chat: '<path d="M4 4h16v12H9l-5 4z"/><path d="M8 9h8M8 12h6"/>',
  more: '<path d="M4 6h16M4 12h16M4 18h16"/>',
  camera: '<path d="M4 6h4l1.5-2h5L16 6h4a2 2 0 0 1 2 2v11a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2z"/><circle cx="12" cy="13" r="4" fill="var(--icon-cutout)"/>',
  search: '<circle cx="10.5" cy="10.5" r="6.5"/><path d="m15.5 15.5 5 5"/>',
  screen: '<rect x="2" y="3" width="20" height="15" rx="2"/><path d="M8 21h8M12 18v3" stroke="currentColor" stroke-width="2" fill="none"/>',
  history: '<path d="M4 8a9 9 0 1 1-1 6M3 3v5h5"/><path d="M12 7v5l3 2"/>',
  files: '<path d="M2 6h8l2 3h10v11H2z"/><path d="M2 6V4h8l2 2"/>',
  access: '<path d="M3 4h7v7H3zM14 4h7v7h-7zM3 14h7v7H3zM14 14h7v7h-7z"/><path d="M10 7h4M7 11v3M17 11v3M10 17h4"/>',
  tools: '<path d="M3 6h18M3 12h18M3 18h18"/><circle cx="9" cy="6" r="2"/><circle cx="16" cy="12" r="2"/><circle cx="7" cy="18" r="2"/>',
  settings: '<path d="M10 2h4l.5 2.3 2 .9 2-1.2 2.8 2.8-1.2 2 .9 2L23 11v4l-2.3.5-.9 2 1.2 2-2.8 2.8-2-1.2-2 .9L14 24h-4l-.5-2.3-2-.9-2 1.2-2.8-2.8 1.2-2-.9-2L1 15v-4l2.3-.5.9-2-1.2-2L5.8 3.7l2 1.2 2-.9z" transform="translate(0 -1) scale(1 .92)"/><circle cx="12" cy="12" r="3" fill="var(--icon-cutout)"/>',
  launcher: '<path d="M12 2 15 8l7 .9-5 5 1.2 7.1L12 17.7 5.8 21 7 13.9l-5-5L9 8z"/>',
  back: '<path d="m15 4-8 8 8 8"/>', forward: '<path d="m9 4 8 8-8 8"/>', chevron: '<path d="m6 9 6 6 6-6"/>', close: '<path d="M5 5 19 19M19 5 5 19"/>',
  play: '<path d="m7 4 13 8-13 8z"/>', pause: '<path d="M6 4h4v16H6zM14 4h4v16h-4z"/>', stop: '<rect x="5" y="5" width="14" height="14" rx="2"/>',
  send: '<path d="m3 11 18-8-7 18-3.6-7.4zM10.4 13.6 21 3"/>', copy: '<rect x="8" y="8" width="12" height="12" rx="2"/><path d="M16 8V5a2 2 0 0 0-2-2H5a2 2 0 0 0-2 2v9a2 2 0 0 0 2 2h3"/>',
  plus: '<path d="M12 4v16M4 12h16"/>', check: '<path d="m4 12 5 5L20 6"/>', alert: '<path d="m12 2 10 18H2zM12 8v5M12 17h.01"/>', info: '<circle cx="12" cy="12" r="10"/><path d="M12 11v6M12 7h.01"/>',
  file: '<path d="M5 2h9l5 5v15H5zM14 2v5h5M8 12h8M8 16h8"/>', folder: '<path d="M2 6h8l2 3h10v11H2z"/>', video: '<rect x="2" y="4" width="20" height="16" rx="2"/><path d="m10 8 6 4-6 4z"/>',
  photo: '<rect x="2" y="3" width="20" height="18" rx="2"/><circle cx="8" cy="9" r="2"/><path d="m4 18 6-5 4 3 3-3 3 3"/>', record: '<circle cx="12" cy="12" r="8"/>',
  volume: '<path d="M3 9h4l5-4v14l-5-4H3zM16 9a5 5 0 0 1 0 6M19 6a9 9 0 0 1 0 12"/>', rotate: '<path d="M4 8a9 9 0 0 1 15-2l2 2M20 16a9 9 0 0 1-15 2l-2-2M21 3v5h-5M3 21v-5h5"/>', loop: '<path d="M5 7h13l-3-3M18 7l-3 3M19 17H6l3 3M6 17l3-3"/>',
  refresh: '<path d="M20 8a8 8 0 1 0 1 6M20 3v5h-5"/>', wifi: '<path d="M2 8a16 16 0 0 1 20 0M5 12a11 11 0 0 1 14 0M8 16a6 6 0 0 1 8 0M12 20h.01"/>',
  download: '<path d="M12 2v13m-5-5 5 5 5-5M3 18v4h18v-4"/>', upload: '<path d="M12 21V8m-5 5 5-5 5 5M3 6V2h18v4"/>', link: '<path d="M10 13a5 5 0 0 0 7 .5l3-3a5 5 0 0 0-7-7l-2 2M14 11a5 5 0 0 0-7-.5l-3 3a5 5 0 0 0 7 7l2-2"/>',
  moon: '<path d="M20 15A8 8 0 0 1 9 4 8 8 0 1 0 20 15z"/>', sun: '<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M2 12h2M20 12h2M4.9 4.9l1.4 1.4m11.4 11.4 1.4 1.4M19.1 4.9l-1.4 1.4M6.3 17.7l-1.4 1.4"/>',
  menu: '<path d="M3 6h18M3 12h18M3 18h18"/>', sliders: '<path d="M3 7h18M3 17h18"/><circle cx="9" cy="7" r="2"/><circle cx="16" cy="17" r="2"/>'
  ,favorite: '<path d="M12 21s-8-4.6-9.7-9.5C.8 7.3 3.4 4 7.1 4c2 0 3.7 1 4.9 2.5C13.2 5 14.9 4 16.9 4c3.7 0 6.3 3.3 4.8 7.5C20 16.4 12 21 12 21z"/>'
  ,rewind: '<path d="m11 5-8 7 8 7V5zm10 0-8 7 8 7V5z"/>'
  ,fastforward: '<path d="m3 5 8 7-8 7V5zm10 0 8 7-8 7V5z"/>'
  ,speed: '<path d="M4 17a9 9 0 1 1 16 0M12 13l4-5M8 19h8"/>'
  ,volume_off: '<path d="M3 9h4l5-4v14l-5-4H3zM16 9.5l5 5M21 9.5l-5 5"/>'
  ,volume_low: '<path d="M3 9h4l5-4v14l-5-4H3zM16 10.5a2.5 2.5 0 0 1 0 3"/>'
  ,volume_half: '<path d="M3 9h4l5-4v14l-5-4H3zM16 9a5 5 0 0 1 0 6"/>'
  ,speed_1: '<path d="M4 17a9 9 0 1 1 16 0M12 13 7 9M8 19h8"/>'
  ,speed_125: '<path d="M4 17a9 9 0 1 1 16 0M12 13V7M8 19h8"/>'
  ,speed_15: '<path d="M4 17a9 9 0 1 1 16 0M12 13l4-5M8 19h8"/>'
  ,speed_2: '<path d="M4 17a9 9 0 1 1 16 0M12 13l6-1M8 19h8"/>'
  ,text_small: '<path d="M8 10h8M12 10v9"/>'
  ,text_medium: '<path d="M5.5 7.5h13M12 7.5V20"/>'
  ,timer: '<path d="M4 13a8 8 0 1 0 16 0a8 8 0 1 0-16 0M12 9v4l2.5 2M9.5 3h5M12 3v2"/>'
  ,clock: '<path d="M3.5 12a8.5 8.5 0 1 0 17 0a8.5 8.5 0 1 0-17 0M12 7.5V12l3 2"/>'
  ,bell: '<path d="M6 16V11a6 6 0 0 1 12 0v5l1.5 2h-15zM10 20.5h4"/>'
  ,plus_one: '<path d="M4 12h8M8 8v8M16 9l2-1.5V17"/>'
  ,minus_one: '<path d="M4 12h8M16 9l2-1.5V17"/>'
  ,restart: '<path d="M5 12a7 7 0 1 0 2-5M5 4v4h4"/>'
  ,snooze: '<path d="M5 5h5l-5 6h5M13 13h6l-6 7h6"/>'
  ,bookmark: '<path d="M6 4h12v16l-6-4-6 4z"/>'
  ,view_list: '<path d="M5 7h14M5 12h14M5 17h9"/>'
  ,view_day: '<path d="M6.5 5h11A2.5 2.5 0 0 1 20 7.5v10a2.5 2.5 0 0 1-2.5 2.5h-11A2.5 2.5 0 0 1 4 17.5v-10A2.5 2.5 0 0 1 6.5 5zM8 10h8M8 14h5"/>'
  ,view_week: '<path d="M6 5h12a2.5 2.5 0 0 1 2.5 2.5v9A2.5 2.5 0 0 1 18 19H6a2.5 2.5 0 0 1-2.5-2.5v-9A2.5 2.5 0 0 1 6 5zM9 5v14M15 5v14"/>'
  ,view_month: '<path d="M6 5h12a2.5 2.5 0 0 1 2.5 2.5v10A2.5 2.5 0 0 1 18 20H6a2.5 2.5 0 0 1-2.5-2.5v-10A2.5 2.5 0 0 1 6 5zM3.5 10h17M8 3v4M16 3v4M8.5 14.5h.01M12 14.5h.01M15.5 14.5h.01"/>'
  ,dusk: '<path d="M4 17h16M7 17a5 5 0 0 1 10 0M12 6v3M5 10l1.5 1.5M19 10l-1.5 1.5"/>'
  ,night: '<path d="M12 3v3M12 18v3M4 12h3M17 12h3M9 12a3 3 0 1 0 6 0a3 3 0 1 0-6 0"/>'
  ,edit: '<path d="m4 20 4.5-1 11-11-3.5-3.5-11 11zM14 6l3.5 3.5"/>'
  ,note: '<path d="M5 3h14v18H5zM8 8h8M8 12h8M8 16h5"/>'
  ,trash: '<path d="M4 6h16M9 6V4h6v2M6 6l1 15h10l1-15M10 10v7M14 10v7"/>'
  ,expand: '<path d="M4 9V4h5M15 4h5v5M20 15v5h-5M9 20H4v-5"/>'
  ,collapse: '<path d="M9 4v5H4M15 4v5h5M20 15h-5v5M4 15h5v5"/>'
  ,device: '<rect x="7" y="2" width="10" height="20" rx="2"/><path d="M10 18h4"/>'
  ,palette: '<circle cx="12" cy="12" r="9"/><circle cx="8" cy="9" r="1"/><circle cx="12" cy="6" r="1"/><circle cx="17" cy="9" r="1"/><path d="M12 21a3 3 0 0 1 0-6h2"/>'
  ,system: '<rect x="3" y="4" width="18" height="16" rx="2"/><path d="M3 9h18M8 4v5"/>'
  ,text: '<path d="M3 5h18M12 5v15M8 20h8"/>'
  ,crop: '<path d="M4 2v16h16M2 4h16v16M6 8h10v8H6z"/>'
  ,fit: '<rect x="2" y="4" width="20" height="16" rx="2"/><path d="M6 8h12v8H6z"/>'
  ,image: '<rect x="2" y="3" width="20" height="18" rx="2"/><circle cx="8" cy="9" r="2"/><path d="m4 18 6-5 4 3 3-3 3 3"/>'
  ,clipboard: '<path d="M8 4h8v3H8zM6 6H4v16h16V6h-2M8 11h8M8 15h8"/>'
  ,fork: '<circle cx="6" cy="5" r="2"/><circle cx="6" cy="19" r="2"/><circle cx="18" cy="7" r="2"/><path d="M6 7v10M18 9c0 5-12 3-12 8"/>'
  ,archive: '<rect x="3" y="4" width="18" height="5" rx="1"/><path d="M5 9v11h14V9M9 13h6"/>'
  ,markdown: '<rect x="2" y="4" width="20" height="16" rx="2"/><path d="M5 16V9l3 3 3-3v7M15 10v6m-2-2 2 2 2-2"/>'
  ,help: '<circle cx="12" cy="12" r="10"/><path d="M9 9a3 3 0 1 1 5 2.2c-1.2.9-2 1.5-2 3M12 18h.01"/>'
  ,source: '<rect x="2" y="3" width="8" height="8" rx="1"/><rect x="14" y="13" width="8" height="8" rx="1"/><path d="M11 7h7v4M18 11l-3-3M13 17H6v-4M6 13l3 3"/>'
  ,cpu: '<rect x="6" y="6" width="12" height="12" rx="1.5"/><path d="M9.5 9.5h5v5h-5zM9 2v4M15 2v4M9 18v4M15 18v4M2 9h4M2 15h4M18 9h4M18 15h4"/>'
  ,ram: '<path d="M2 7h20v9H2zM6 10v3M10 10v3M14 10v3M18 10v3M5 16v3M9 16v3M15 16v3M19 16v3"/>'
  ,temp: '<path d="M10 5a2 2 0 0 1 4 0v9.3a4 4 0 1 1-4 0z"/><path d="M12 10v7"/>'
  ,pick_none: '<circle cx="12" cy="12" r="9"/>'
  ,pick_some: '<circle cx="12" cy="12" r="9"/><path d="M8 12h8"/>'
  ,effort_low: '<rect x="4" y="15" width="3.2" height="5" rx=".6"/><rect x="10.4" y="10" width="3.2" height="10" rx=".6" fill="none" stroke-width="1.3"/><rect x="16.8" y="4" width="3.2" height="16" rx=".6" fill="none" stroke-width="1.3"/>'
  ,effort_medium: '<rect x="4" y="15" width="3.2" height="5" rx=".6"/><rect x="10.4" y="10" width="3.2" height="10" rx=".6"/><rect x="16.8" y="4" width="3.2" height="16" rx=".6" fill="none" stroke-width="1.3"/>'
  ,effort_high: '<rect x="4" y="15" width="3.2" height="5" rx=".6"/><rect x="10.4" y="10" width="3.2" height="10" rx=".6"/><rect x="16.8" y="4" width="3.2" height="16" rx=".6"/>'
  ,effort_xhigh: '<path d="M12 2c1 4 6 6.5 6 12a6 6 0 0 1-12 0c0-3 1.8-5 3-6 0 2 .8 3.3 2 3.5 0-4-1-6.5 1-9.5z"/>'
  ,effort_max: '<path d="M13.5 2 4 14h7l-1.5 8L19 10h-7z"/>'
  ,effort_ultra: '<path d="M12 2c4 3 6 7.5 5 12.5L15.5 17h-7L7 14.5C6 9.5 8 5 12 2z"/><circle cx="12" cy="10" r="2" fill="var(--icon-cutout)"/><path d="M7.2 13.5 4 17v3.5l4.5-2.5zM16.8 13.5 20 17v3.5L15.5 18zM10 18.5h4l-2 3.5z"/>'
};

const filled = new Set(['share','camera','screen','settings','launcher','play','pause','stop','record','effort_low','effort_medium','effort_high','effort_xhigh','effort_max','effort_ultra']);
function icon(name, size=20) {
  const chosen = decisions.icons[name] || (filled.has(name) ? 'solid' : 'line');
  const fill = chosen==='solid' || (chosen==='geometric' && ['home','media','files','access'].includes(name));
  const attrs = fill ? 'fill="currentColor" stroke="none"' : 'fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"';
  return `<svg class="ico ico-${chosen}" viewBox="0 0 24 24" width="${size}" height="${size}" ${attrs} aria-hidden="true" focusable="false">${shapes[name]||shapes.info}</svg>`;
}
