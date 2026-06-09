# Wallbox Contents Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an editable contents list (items + quantities) to each Wallbox marker, with a side panel UI, autocomplete combobox, and an item-count badge on the marker.

**Architecture:** Extend the existing `markers[]` data structure with a new `contents: [{name, qty}]` field on `wb` markers. Add a single `<aside>` panel element (position:fixed) that gets shown/hidden when the user clicks a WB. All UI logic stays inside the single `marker-tool.html` file — no new files, no dependencies. Persistence rides on the existing `save()` to localStorage.

**Tech Stack:** Vanilla HTML/CSS/JavaScript inside one file. No build, no test runner. **Verification is manual in the browser** (the project's existing convention).

**Spec reference:** `docs/superpowers/specs/2026-06-09-wallbox-contents-design.md`

**Out of scope:** Rendering contents in the exported PDF (`render_from_json.py`) — this is a separate later task in the roadmap.

---

## File Structure

Single file modified: `marker-tool.html`. Changes by region:

| Region | Lines (approx.) | Adding |
|---|---|---|
| `<style>` | ~7–135 | Panel + badge + combobox CSS |
| `<body>` markup | after `</main>` (~190) | `<aside id="contentsPanel">` skeleton |
| State vars | ~205–220 | `DEFAULT_CONTENT_ITEMS`, `openContentsWbId`, migration loop |
| `renderMarkers()` | ~426–476 | Badge element + click-to-open handler |
| `renderList()` | ~591–622 | Replace `prompt()` rename with panel open |
| New section at end of script | before `renderMarkers()` final call (~781) | Contents panel functions |

---

## Verification convention

This project has no automated tests. Each task ends with **manual verification in the browser**: open `marker-tool.html`, perform the listed steps, observe the listed outcomes. If an observation fails, fix before committing.

Open browser via:
```bash
open marker-tool.html
```

For a clean slate during testing, in DevTools console: `localStorage.clear(); location.reload();`

---

## Task 1: Data model + migration

**Goal:** Add `contents: []` to every WB marker. Ensure old localStorage loads cleanly.

**Files:**
- Modify: `marker-tool.html` near line 213 (after `let markers = [];`)
- Modify: `marker-tool.html` near line 288 (`markers.push(...)` for drag-drop add)
- Modify: `marker-tool.html` near line 421 (`markers.push(m)` for click-add)

- [ ] **Step 1: Add the default-items constant**

Find the line `let mode = null; // 'wb' | 'cam' | 'cable' | null` (~line 205). On the line above it, add:

```javascript
const DEFAULT_CONTENT_ITEMS = ['Camera', 'BNC', 'XLR', 'Lemo', 'Coax', 'Network', 'Fiber LC', 'Fiber SC', 'Power Outlet'];
```

- [ ] **Step 2: Migrate loaded markers**

Find the block (around line 213–220):

```javascript
let markers = [];
// migration: old format was an array of markers
if (Array.isArray(stored)) {
  markers = stored;
} else if (stored) {
  markers = stored.markers || [];
  cables  = stored.cables  || [];
}
```

Right after the `if/else` block, add:

```javascript
// migration: ensure every WB has a contents array
for (const m of markers) {
  if (m.type === 'wb' && !Array.isArray(m.contents)) m.contents = [];
}
```

- [ ] **Step 3: Initialize contents on new WB (drag-drop add)**

Find the line (around 288):

```javascript
markers.push({ id: Date.now() + Math.random(), type: 'wb', name: dragName, x, y });
```

Change to:

```javascript
markers.push({ id: Date.now() + Math.random(), type: 'wb', name: dragName, x, y, contents: [] });
```

- [ ] **Step 4: Initialize contents on new WB (click-add)**

Find the click-add block (around 413–421). The `markers.push(m)` line is preceded by a construction of `m`. Locate it and change the WB branch so the constructed `m` object includes `contents: []` when `mode === 'wb'`.

Specifically find:

```javascript
const name = (mode === 'wb')
```

and trace down to where `m` is built. Add `contents: []` to the WB-shaped object. If the current code uses one `m` object for both types, conditionally append:

```javascript
if (mode === 'wb') m.contents = [];
```

immediately before the `markers.push(m)` line.

- [ ] **Step 5: Manually verify**

1. Run: `open marker-tool.html`
2. In DevTools console: `localStorage.clear(); location.reload();`
3. Upload any PDF, click "וולבוקס" mode, click on the plan to add a WB.
4. In console: `markers[0].contents` → expect `[]` (array, not undefined).
5. In console: `DEFAULT_CONTENT_ITEMS` → expect the array of 9 items.
6. Refresh the page. In console: `markers[0].contents` → still `[]` (survived round-trip through localStorage).

- [ ] **Step 6: Commit**

```bash
git add marker-tool.html
git commit -m "WB contents: שדה contents על WB + פריטים דיפולטיים"
```

---

## Task 2: Panel skeleton (HTML + CSS), hidden by default

**Goal:** Add the `<aside>` panel element and styles. Not yet wired up — invisible until manually shown.

**Files:**
- Modify: `marker-tool.html` `<style>` section (around line 7–135)
- Modify: `marker-tool.html` markup, after the `</main>` closing tag (around line 190)

- [ ] **Step 1: Add CSS for the panel**

At the end of the `<style>` block (just before `</style>`), add:

```css
  /* Wallbox contents panel */
  #contentsPanel {
    position: fixed;
    top: 0; right: 0;
    width: 320px; height: 100vh;
    background: #fff;
    border-left: 2px solid #b00;
    box-shadow: -4px 0 12px rgba(0,0,0,0.15);
    z-index: 100;
    display: flex;
    flex-direction: column;
    font-family: -apple-system, "Arial Hebrew", Arial, sans-serif;
  }
  #contentsPanel[hidden] { display: none; }
  .cp-header {
    background: #b00; color: #fff;
    padding: 10px 12px;
    display: flex; align-items: center; gap: 8px;
  }
  .cp-header input.cp-name {
    flex: 1; padding: 6px 8px; font-size: 15px;
    border: 0; border-radius: 4px;
    background: rgba(255,255,255,0.95); color: #b00;
    font-weight: bold;
  }
  .cp-header button.cp-close {
    background: transparent; color: #fff; border: 0;
    font-size: 22px; cursor: pointer; padding: 0 4px;
  }
  .cp-body {
    flex: 1; overflow-y: auto;
    padding: 10px 12px;
  }
  .cp-empty {
    color: #999; font-style: italic; text-align: center;
    padding: 20px 0; font-size: 13px;
  }
  .cp-row {
    display: flex; align-items: center; gap: 6px;
    padding: 6px 0; border-bottom: 1px solid #eee;
  }
  .cp-row .cp-item-name {
    flex: 1; padding: 4px 6px; font-size: 14px;
    border: 1px solid transparent; border-radius: 3px;
    background: transparent;
  }
  .cp-row .cp-item-name:focus, .cp-row .cp-item-name:hover {
    background: #fafafa; border-color: #ddd;
  }
  .cp-stepper { display: flex; align-items: center; gap: 2px; }
  .cp-stepper button {
    width: 24px; height: 24px; border: 1px solid #bbb;
    background: #f5f5f5; cursor: pointer; border-radius: 3px;
    font-size: 14px; padding: 0;
  }
  .cp-stepper input {
    width: 40px; text-align: center; padding: 4px 0;
    border: 1px solid #bbb; border-radius: 3px; font-size: 13px;
  }
  .cp-row .cp-remove {
    background: transparent; border: 0; color: #c33;
    font-size: 18px; cursor: pointer; padding: 0 4px;
  }
  .cp-footer {
    padding: 10px 12px; border-top: 1px solid #ddd;
    background: #f8f8f8;
  }
  .cp-combobox { position: relative; }
  .cp-combobox input {
    width: 100%; padding: 8px 10px; font-size: 14px;
    border: 1px solid #bbb; border-radius: 4px;
  }
  .cp-combobox .cp-options {
    position: absolute; bottom: 100%; left: 0; right: 0;
    margin-bottom: 2px;
    background: #fff; border: 1px solid #bbb; border-radius: 4px;
    max-height: 180px; overflow-y: auto;
    box-shadow: 0 -2px 8px rgba(0,0,0,0.1);
    z-index: 1;
  }
  .cp-combobox .cp-options div {
    padding: 6px 10px; cursor: pointer; font-size: 14px;
  }
  .cp-combobox .cp-options div:hover,
  .cp-combobox .cp-options div.cp-opt-active {
    background: #ffe5e5;
  }
  .cp-delete-wb {
    margin-top: 10px; width: 100%;
    background: #fff; color: #c33; border: 1px solid #c33;
    padding: 7px; border-radius: 4px; cursor: pointer;
    font-size: 13px;
  }
  .cp-delete-wb:hover { background: #fee; }

  /* Badge on WB marker */
  .marker.wb .qty-badge {
    position: absolute;
    top: -6px; right: -6px;
    background: #222; color: #fff;
    font-size: 10px; font-weight: bold;
    min-width: 16px; height: 16px;
    border-radius: 8px;
    border: 1.5px solid #fff;
    display: flex; align-items: center; justify-content: center;
    padding: 0 3px;
    pointer-events: none;
  }
```

- [ ] **Step 2: Add the panel HTML element**

In the markup, after the `</main>` closing tag (around line 190), before `<script>`, add:

```html
<aside id="contentsPanel" dir="rtl" hidden>
  <div class="cp-header">
    <input type="text" class="cp-name" placeholder="שם Wallbox" />
    <button class="cp-close" title="סגור">×</button>
  </div>
  <div class="cp-body">
    <div class="cp-empty">אין פריטים ב-Wallbox זה. הוסף פריט למטה.</div>
    <div class="cp-list"></div>
  </div>
  <div class="cp-footer">
    <div class="cp-combobox">
      <input type="text" class="cp-add" placeholder="+ הוסף פריט (BNC, XLR, ...)" />
      <div class="cp-options" hidden></div>
    </div>
    <button class="cp-delete-wb">מחק Wallbox זה</button>
  </div>
</aside>
```

- [ ] **Step 3: Manually verify**

1. Open `marker-tool.html` in browser.
2. The panel should NOT be visible.
3. In DevTools console: `document.getElementById('contentsPanel').hidden = false;`
4. Panel slides into view from the right, 320px wide, RTL, red header with empty name input.
5. The "אין פריטים" message visible in the body.
6. Combobox and "מחק Wallbox" button visible in the footer.
7. Hide it again: `document.getElementById('contentsPanel').hidden = true;`

- [ ] **Step 4: Commit**

```bash
git add marker-tool.html
git commit -m "WB contents: שלד פאנל צד + CSS"
```

---

## Task 3: Open/close panel — click WB to open, X / ESC / outside to close

**Goal:** Wire the panel: click on a WB opens it with that WB's name; X button, ESC, or click on background closes it; clicking another WB switches content.

**Files:**
- Modify: `marker-tool.html` near `renderMarkers()` click handler (~line 466)
- Modify: `marker-tool.html` near keydown handler (~line 321)
- Modify: `marker-tool.html` add new section before `renderMarkers()` final call (~line 781)

- [ ] **Step 1: Add panel state + open/close functions**

In the script section, before the final `renderMarkers();` call (line ~781), add:

```javascript
// --- Contents panel ---
let openContentsWbId = null;
const contentsPanel = document.getElementById('contentsPanel');
const cpNameInput   = contentsPanel.querySelector('.cp-name');
const cpCloseBtn    = contentsPanel.querySelector('.cp-close');
const cpDeleteBtn   = contentsPanel.querySelector('.cp-delete-wb');
const cpList        = contentsPanel.querySelector('.cp-list');
const cpEmpty       = contentsPanel.querySelector('.cp-empty');
const cpAddInput    = contentsPanel.querySelector('.cp-add');
const cpOptions     = contentsPanel.querySelector('.cp-options');

function openContentsPanel(wbId, focusName = false) {
  const m = markers.find(mm => mm.id === wbId && mm.type === 'wb');
  if (!m) return;
  openContentsWbId = wbId;
  cpNameInput.value = m.name || '';
  contentsPanel.hidden = false;
  renderContentsList();  // defined in Task 4
  if (focusName) cpNameInput.focus();
}

function closeContentsPanel() {
  openContentsWbId = null;
  contentsPanel.hidden = true;
  cpOptions.hidden = true;
  cpAddInput.value = '';
}

cpCloseBtn.onclick = closeContentsPanel;

cpDeleteBtn.onclick = () => {
  if (openContentsWbId == null) return;
  const id = openContentsWbId;
  closeContentsPanel();
  deleteMarker(id);
};

// Placeholder so Task 3 verification works before Task 4 fills it in.
function renderContentsList() {
  cpEmpty.style.display = 'block';
  cpList.innerHTML = '';
}
```

- [ ] **Step 2: Wire the click on a WB marker to open the panel**

Find in `renderMarkers()` (around line 466):

```javascript
    el.addEventListener('click', ev => {
      if (mode !== 'cable') return;
      if (ev.target.classList.contains('x')) return;
      if (ev.target.classList.contains('rot-handle')) return;
      handleCableClick(m.id);
    });
```

Replace with:

```javascript
    el.addEventListener('click', ev => {
      if (ev.target.classList.contains('x')) return;
      if (ev.target.classList.contains('rot-handle')) return;
      if (mode === 'cable') { handleCableClick(m.id); return; }
      if (mode == null && m.type === 'wb') {
        ev.stopPropagation();
        openContentsPanel(m.id);
      }
    });
```

- [ ] **Step 3: ESC closes the panel**

Find the existing keydown handler (around line 321):

```javascript
document.addEventListener('keydown', e => {
```

Inside that handler, at the top of the function body, add:

```javascript
  if (e.key === 'Escape' && !contentsPanel.hidden) {
    // Don't intercept if user is in an input field — let them blur naturally first.
    if (document.activeElement && document.activeElement.tagName === 'INPUT') {
      document.activeElement.blur();
      return;
    }
    closeContentsPanel();
    return;
  }
```

- [ ] **Step 4: Clicking background / cam / cable area closes the panel**

Find the existing click handler on `origImgWrap` (around line 404):

```javascript
origImgWrap.addEventListener('click', e => {
```

At the top of that handler's body, add:

```javascript
  if (!contentsPanel.hidden && !contentsPanel.contains(e.target)) {
    closeContentsPanel();
    // continue processing this click as normal (it may still add a marker, etc.)
  }
```

- [ ] **Step 5: Manually verify**

1. `localStorage.clear(); location.reload();`
2. Upload PDF, add 2 WBs (give them names "A" and "B"), add 1 camera.
3. Click on WB "A" — panel opens, header shows "A".
4. Click on WB "B" — panel still open, header shows "B" (switched).
5. Click the X — panel closes.
6. Click WB "A" again — opens.
7. Press ESC — panel closes.
8. Click WB "A" again — opens. Click anywhere on the plan background — panel closes.
9. Click WB "A" again. Click on the camera — panel closes (camera click bubbled to background or didn't open panel).
10. Click on a name in the existing right-side list — panel does NOT open yet (rename is still the old `prompt`; that's wired in Task 7).

- [ ] **Step 6: Commit**

```bash
git add marker-tool.html
git commit -m "WB contents: פתיחה/סגירה של פאנל + click handlers"
```

---

## Task 4: Render contents list, item add/update/remove

**Goal:** Real `renderContentsList()` showing items as rows with stepper and remove. Functions to add/update/remove items.

**Files:**
- Modify: `marker-tool.html` — replace the placeholder `renderContentsList()` from Task 3

- [ ] **Step 1: Replace `renderContentsList` with real implementation and add helpers**

Find the placeholder added in Task 3:

```javascript
// Placeholder so Task 3 verification works before Task 4 fills it in.
function renderContentsList() {
  cpEmpty.style.display = 'block';
  cpList.innerHTML = '';
}
```

Replace with:

```javascript
function getOpenWb() {
  return markers.find(m => m.id === openContentsWbId && m.type === 'wb');
}

function renderContentsList() {
  const m = getOpenWb();
  cpList.innerHTML = '';
  if (!m) return;
  const items = m.contents || [];
  cpEmpty.style.display = items.length === 0 ? 'block' : 'none';
  items.forEach((item, idx) => {
    const row = document.createElement('div');
    row.className = 'cp-row';

    const nameIn = document.createElement('input');
    nameIn.type = 'text';
    nameIn.className = 'cp-item-name';
    nameIn.value = item.name;
    nameIn.onchange = () => updateContentItem(idx, { name: nameIn.value.trim() || item.name });

    const stepper = document.createElement('div');
    stepper.className = 'cp-stepper';
    const minus = document.createElement('button');
    minus.textContent = '−';
    minus.onclick = () => updateContentItem(idx, { qty: Math.max(1, (item.qty | 0) - 1) });
    const qtyIn = document.createElement('input');
    qtyIn.type = 'number';
    qtyIn.min = '1';
    qtyIn.value = item.qty;
    qtyIn.onchange = () => updateContentItem(idx, { qty: Math.max(1, parseInt(qtyIn.value, 10) || 1) });
    const plus = document.createElement('button');
    plus.textContent = '+';
    plus.onclick = () => updateContentItem(idx, { qty: (item.qty | 0) + 1 });
    stepper.append(minus, qtyIn, plus);

    const rm = document.createElement('button');
    rm.className = 'cp-remove';
    rm.textContent = '×';
    rm.title = 'מחק פריט';
    rm.onclick = () => removeContentItem(idx);

    row.append(nameIn, stepper, rm);
    cpList.appendChild(row);
  });
}

function addContentItem(name, qty = 1) {
  const m = getOpenWb();
  if (!m) return;
  if (!Array.isArray(m.contents)) m.contents = [];
  m.contents.push({ name: name.trim(), qty: Math.max(1, qty | 0) });
  save();
  renderContentsList();
  renderMarkers();  // refresh badge
}

function updateContentItem(idx, patch) {
  const m = getOpenWb();
  if (!m) return;
  Object.assign(m.contents[idx], patch);
  save();
  renderContentsList();
  renderMarkers();  // refresh badge
}

function removeContentItem(idx) {
  const m = getOpenWb();
  if (!m) return;
  m.contents.splice(idx, 1);
  save();
  renderContentsList();
  renderMarkers();  // refresh badge
}
```

- [ ] **Step 2: Manually verify**

1. `localStorage.clear(); location.reload();`
2. Upload PDF, add a WB, click it. Panel opens.
3. In DevTools console: `addContentItem('BNC', 4)` — row appears with "BNC", stepper showing 4, × button.
4. Click `+` on the row — qty becomes 5; reload page → still 5.
5. Click `−` four times — qty goes 4 → 3 → 2 → 1. Click again — stays at 1 (minimum).
6. Type "7" in the number field, blur — qty becomes 7.
7. Edit the name to "BNC-X", blur — name updates; reload page → still "BNC-X".
8. Click × on the row — row disappears, empty message returns.

- [ ] **Step 3: Commit**

```bash
git add marker-tool.html
git commit -m "WB contents: רינדור רשימה + stepper + add/update/remove"
```

---

## Task 5: Combobox with autocomplete

**Goal:** Typing in the "+ הוסף פריט" input shows suggestions from the 9 defaults (filtered, excluding items already in this WB). Click a suggestion → adds. Enter with a name not in suggestions → adds as custom.

**Files:**
- Modify: `marker-tool.html` — add combobox logic in the same Contents panel section

- [ ] **Step 1: Add combobox handlers**

Right after the helper functions added in Task 4, append:

```javascript
let cpOptActiveIdx = -1;

function cpRenderOptions() {
  const m = getOpenWb();
  const used = new Set((m?.contents || []).map(c => c.name.toLowerCase()));
  const q = cpAddInput.value.trim().toLowerCase();
  const matches = DEFAULT_CONTENT_ITEMS
    .filter(name => !used.has(name.toLowerCase()))
    .filter(name => q === '' || name.toLowerCase().startsWith(q));
  cpOptions.innerHTML = '';
  if (matches.length === 0) { cpOptions.hidden = true; cpOptActiveIdx = -1; return; }
  matches.forEach((name, i) => {
    const opt = document.createElement('div');
    opt.textContent = name;
    if (i === cpOptActiveIdx) opt.classList.add('cp-opt-active');
    opt.onmousedown = (ev) => {
      ev.preventDefault();  // keep input focused; prevent blur
      addContentItem(name);
      cpAddInput.value = '';
      cpRenderOptions();
    };
    cpOptions.appendChild(opt);
  });
  cpOptions.hidden = false;
}

cpAddInput.addEventListener('focus', () => { cpOptActiveIdx = -1; cpRenderOptions(); });
cpAddInput.addEventListener('input', () => { cpOptActiveIdx = -1; cpRenderOptions(); });
cpAddInput.addEventListener('blur',  () => { setTimeout(() => { cpOptions.hidden = true; }, 120); });
cpAddInput.addEventListener('keydown', (e) => {
  const opts = Array.from(cpOptions.querySelectorAll('div'));
  if (e.key === 'ArrowDown') {
    cpOptActiveIdx = Math.min(opts.length - 1, cpOptActiveIdx + 1);
    cpRenderOptions();
    e.preventDefault();
  } else if (e.key === 'ArrowUp') {
    cpOptActiveIdx = Math.max(-1, cpOptActiveIdx - 1);
    cpRenderOptions();
    e.preventDefault();
  } else if (e.key === 'Enter') {
    e.preventDefault();
    if (cpOptActiveIdx >= 0 && opts[cpOptActiveIdx]) {
      addContentItem(opts[cpOptActiveIdx].textContent);
    } else if (cpAddInput.value.trim()) {
      addContentItem(cpAddInput.value);
    }
    cpAddInput.value = '';
    cpOptActiveIdx = -1;
    cpRenderOptions();
  } else if (e.key === 'Escape') {
    cpOptions.hidden = true;
    cpAddInput.value = '';
    cpOptActiveIdx = -1;
    e.preventDefault();
    e.stopPropagation();  // don't close the whole panel
  }
});
```

- [ ] **Step 2: Manually verify**

1. `localStorage.clear(); location.reload();`
2. Upload PDF, add a WB, click it.
3. Click in the "+ הוסף פריט" field — suggestions list appears showing all 9 defaults.
4. Type "B" — list filters to just "BNC".
5. Click "BNC" — row added with qty 1, input clears.
6. Click in input again — list now shows 8 items (BNC excluded).
7. Type "Power" — only "Power Outlet" suggested. Press Enter — added.
8. Type "מתאם מיוחד" (something not in defaults) — list empty. Press Enter — added as a custom row with that name, qty 1.
9. Click input → ArrowDown → ArrowDown → Enter — adds the second visible suggestion.
10. Click input → press ESC — suggestion list closes; panel stays open. Input cleared.

- [ ] **Step 3: Commit**

```bash
git add marker-tool.html
git commit -m "WB contents: combobox עם autocomplete + מקלדת"
```

---

## Task 6: Badge on WB marker

**Goal:** Small dark badge in the top-right corner of each WB circle, showing the sum of quantities. Tooltip on hover lists items.

**Files:**
- Modify: `marker-tool.html` — `renderMarkers()` function (around line 426–476), inside the WB rendering branch

- [ ] **Step 1: Render the badge in `renderMarkers()`**

Find in `renderMarkers()` the block that builds the WB marker. Just before the `if (m.name) {` block (line ~448), add:

```javascript
    if (m.type === 'wb' && Array.isArray(m.contents) && m.contents.length) {
      const sumQty = m.contents.reduce((acc, c) => acc + (c.qty | 0), 0);
      if (sumQty > 0) {
        const badge = document.createElement('span');
        badge.className = 'qty-badge';
        badge.textContent = String(sumQty);
        badge.title = m.contents.map(c => `${c.name} ×${c.qty}`).join(', ');
        el.appendChild(badge);
      }
    }
```

- [ ] **Step 2: Manually verify**

1. `localStorage.clear(); location.reload();`
2. Upload PDF, add a WB. No badge yet (contents is empty).
3. Click the WB. In the panel, add "BNC" → qty 1. Badge appears showing "1".
4. Click `+` on the BNC row → qty 2. Badge updates to "2".
5. Add "XLR" with default qty 1. Badge updates to "3".
6. Hover the badge — tooltip shows "BNC ×2, XLR ×1".
7. Remove BNC row entirely. Badge updates to "1".
8. Remove XLR — badge disappears (contents empty again).

- [ ] **Step 3: Commit**

```bash
git add marker-tool.html
git commit -m "WB contents: badge על המרקר עם סכום הכמויות"
```

---

## Task 7: Name editing via panel, remove the old prompt

**Goal:** Editing the name in the panel header writes it back to the WB. The old rename `prompt()` in the right-side list is replaced with "open the panel focused on the name". Double-click on the WB circle also opens the panel with focus on the name field.

**Files:**
- Modify: `marker-tool.html` near the contents-panel section — add `cpNameInput` change handler
- Modify: `marker-tool.html` `renderList()` (around line 607–613) — replace `prompt()`
- Modify: `marker-tool.html` `renderMarkers()` (around line 465) — add `dblclick` handler on WB

- [ ] **Step 1: Wire the name field to save on change**

In the Contents panel section, after `cpCloseBtn.onclick = closeContentsPanel;`, add:

```javascript
cpNameInput.addEventListener('change', () => {
  const m = getOpenWb();
  if (!m) return;
  m.name = cpNameInput.value.trim();
  save();
  renderMarkers();
  renderList();
});
```

- [ ] **Step 2: Replace the old rename `prompt()`**

In `renderList()`, find (around line 607–613):

```javascript
    const renameBtn = document.createElement('button');
    renameBtn.textContent = '✎';
    renameBtn.onclick = () => {
      const v = prompt("שנה שם:", m.name);
      if (v != null) { m.name = v; save(); }
    };
    li.appendChild(renameBtn);
```

Replace the `renameBtn.onclick` body:

```javascript
    const renameBtn = document.createElement('button');
    renameBtn.textContent = '✎';
    renameBtn.onclick = () => {
      if (m.type === 'wb') {
        openContentsPanel(m.id, /*focusName=*/true);
      } else {
        const v = prompt("שנה שם:", m.name);
        if (v != null) { m.name = v; save(); renderMarkers(); renderList(); }
      }
    };
    li.appendChild(renameBtn);
```

(Cameras still use `prompt` — they don't have a panel, and that's fine; rename via prompt was already the convention for non-WB.)

- [ ] **Step 3: Double-click on a WB → open panel focused on name**

In `renderMarkers()`, just after the existing `el.addEventListener('click', ...)` block (around line 471), add:

```javascript
    if (m.type === 'wb') {
      el.addEventListener('dblclick', ev => {
        ev.preventDefault();
        ev.stopPropagation();
        openContentsPanel(m.id, /*focusName=*/true);
      });
    }
```

- [ ] **Step 4: Manually verify**

1. `localStorage.clear(); location.reload();`
2. Upload PDF, add a WB named "Test".
3. Click the WB — panel opens, name field shows "Test".
4. Edit name in the panel to "Renamed", tab out — the marker's label on the canvas updates to "Renamed", and the right-side list entry updates.
5. Refresh page — name persists.
6. In the right-side list, click the ✎ icon next to the WB — panel reopens with the name field focused (cursor blinking inside the input). No `prompt()` dialog.
7. For a camera, click ✎ — the OLD `prompt()` still appears (intentional; cameras don't have a panel).
8. Double-click the WB circle — panel opens with the name field focused.
9. Camera still works fine: drag, rotate, click in cable mode.

- [ ] **Step 5: Commit**

```bash
git add marker-tool.html
git commit -m "WB contents: עריכת שם דרך הפאנל + הסרת prompt + dblclick"
```

---

## Task 8: End-to-end verification + STATUS update

**Goal:** Confirm the whole spec works end-to-end. Update STATUS.md.

- [ ] **Step 1: Full spec verification (from spec section "בדיקות ידניות")**

Open browser, `localStorage.clear(); location.reload();`. Upload PDF. Walk through:

1. ✅ Add a WB → click it → panel opens, empty, with name field.
2. ✅ Type "BNC" in combobox → suggestion appears → click → added with qty=1.
3. ✅ Click `+` → qty=2. Badge on marker shows "2".
4. ✅ Type "מותאם" (custom name) → press Enter → added as custom row.
5. ✅ Edit item name inline → blur → persists.
6. ✅ Close panel → reload → click same WB → contents preserved.
7. ✅ Click "שמור JSON" → downloaded file contains `contents` field on the WB.
8. ✅ Manually edit localStorage to a pre-feature shape (WB without `contents`), reload — no errors, panel works.

For step 8 specifically: open DevTools console, run:
```javascript
localStorage.setItem('markerToolState_v2', JSON.stringify({
  markers: [{ id: 1, type: 'wb', x: 100, y: 100, name: 'Legacy' }],
  cables: []
}));
location.reload();
```
Click the Legacy WB. Panel should open with empty contents and no errors in console.

- [ ] **Step 2: Update STATUS.md**

Edit `STATUS.md`: change the section about "תכולת Wallbox" to be marked ✓ done, update the "איפה אנחנו עכשיו" section to reflect that this feature is shipped and the next feature (Room) is up.

- [ ] **Step 3: Final commit**

```bash
git add marker-tool.html STATUS.md
git commit -m "WB contents: סיום פיצ'ר + עדכון STATUS"
```

---

## Self-review notes

- **Spec coverage:** All 8 spec sections mapped to tasks. Default items list (Task 1), panel position/structure (Tasks 2–3), item rows with stepper (Task 4), combobox with autocomplete + custom items (Task 5), badge with sum and tooltip (Task 6), name editing via panel (Task 7), close behaviors (Task 3), backward-compat migration (Task 1, verified Task 8).
- **Out-of-scope items:** PDF rendering of contents (`render_from_json.py`) intentionally deferred to a separate plan, as noted in the spec.
- **Verification convention:** Manual browser verification (no test runner), consistent with project's existing pattern.
