# Design system for the lab pages

One shell, three kinds of building block. Every page uses `shell.css` (layout and tokens) on top of `style.css` (components).

**Shell.** A fixed left sidebar (`shell.js`) holds the brand, the page list, and the test-set list for pages that have sets. Sets are grouped: current ones sit
under "Test sets"; anything old goes in a collapsible "History" group with a one-line warning. A group is data, so a new group or set is one entry in the list a page
passes to `mountShell({ groups, active, onSelect })`. Expanding a group only changes the sidebar, so the main area never moves.
The main area has one header (`.bar`: title, one-line description, and the notation control) at a fixed minimum height, then the page body.

**Tokens.** Spacing 4, 8, 12, 16, 24, 32. Radius 6 (chips, small buttons), 10 (segmented controls, banners), 14 (cards, panels). Type: 0.68, 0.78, 0.9 and 1.3 rem.
Colours: ink and green for emphasis, muted grey for captions, amber for caution and history, red only for wrong.

**Components.**
- Sidebar item: a title and one caption line (words and score). The active item has a white card and a green edge.
- Segmented control (`.segs`): one control per decision, used for notation, sort and filters. No loose pills for navigation.
- Chip (`.chip`, `.pill.tiny`): a small label or toggle inside content, never page navigation.
- Rank board, method card, word card, panel: unchanged content blocks.

**Rules.** Current work appears under "Test sets"; anything not comparable with the current system is History and says so. A page lists only what was run.
Captions carry numbers so the sidebar doubles as a status view. No state that is not in the sidebar or the header changes the page's frame.

**Navigation.** The four html files are identical shells; `web/router.js` loads the page module and its fragment from `web/views/` and swaps only the main area, so moving between pages never reloads the document. The router keeps every page alive: after the first page appears it loads, builds and caches all the others in the background, so a switch just re-attaches a finished page. A page module exports `load()` (fetch data once), `mount(options)` (build once; `options.preload` means do not read the URL), `activate()` and `deactivate()` (add and remove its own listeners, refresh the sidebar). New pages are one entry in `router.js`, one module and one fragment.
