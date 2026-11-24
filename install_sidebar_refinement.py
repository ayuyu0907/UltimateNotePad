#!/usr/bin/env python3
"""UltimateNotePad compact search & UI motion. Back up and patch only 3 frontend files."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import zipfile
import sys

PATHS = ('templates/index.html', 'static/css/app.css', 'static/js/app.js')
MARKER = 'UNP_SIDEBAR_REFINEMENT_V1'
OLD_HTML = '''        <div class="search-wrap">
          <form
            id="note-search-form"
            class="note-filter"
            method="get"
            action="{{ url_for('index') }}"
            role="search"
          >
            <label class="note-filter__label" for="note-search">
              メモを検索
            </label>

            <div class="note-filter__search">
              <input
                id="note-search"
                class="note-filter__input"
                type="search"
                name="q"
                placeholder="タイトル・本文を検索..."
                value="{{ keyword }}"
                autocomplete="off"
              >

              <button class="note-filter__button" type="submit">
                検索
              </button>
            </div>

            <label class="note-filter__label" for="note-sort">
              並べ替え
            </label>

            <select
              id="note-sort"
              class="note-filter__select"
              name="sort"
            >
              <option value="new"
                {% if sort == "new" %}selected{% endif %}>
                更新日時が新しい順
              </option>

              <option value="old"
                {% if sort == "old" %}selected{% endif %}>
                更新日時が古い順
              </option>

              <option value="title"
                {% if sort == "title" %}selected{% endif %}>
                タイトル順
              </option>
            </select>
          </form>
        </div>
        <div class="section-heading">
          <span>すべてのメモ</span>
          <span class="count">{{ notes|default([])|length }}</span>
        </div>'''
NEW_HTML = '''        <!-- UNP_SIDEBAR_REFINEMENT_V1: search field and compact list toolbar -->
        <div class="search-wrap unp-search-compact">
          <form id="note-search-form" class="note-filter" method="get"
                action="{{ url_for('index') }}" role="search">
            {% if selected_note %}
            <input type="hidden" name="id" value="{{ selected_note.id }}">
            {% endif %}
            <label class="note-filter__label visually-hidden" for="note-search">メモを検索</label>
            <div class="note-filter__search">
              <input id="note-search" class="note-filter__input" type="search" name="q"
                     placeholder="メモを検索" value="{{ keyword }}" autocomplete="off"
                     enterkeyhint="search" aria-keyshortcuts="/">
              <button class="unp-search-clear" id="unp-search-clear" type="button" hidden
                      aria-label="検索をクリア" title="検索をクリア">
                <svg aria-hidden="true" focusable="false" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><path d="m6 6 12 12M18 6 6 18"/></svg>
              </button>
              <button class="note-filter__button" type="submit" title="検索">
                <svg aria-hidden="true" focusable="false" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><circle cx="10.5" cy="10.5" r="6.5"/><path d="m16 16 4 4"/></svg>
                <span class="visually-hidden unp-search-submit-label">検索</span>
              </button>
            </div>
          </form>
        </div>
        <div class="section-heading unp-list-heading">
          <span class="unp-list-title">すべてのメモ</span>
          <span class="count">{{ notes|default([])|length }}</span>
          <div class="unp-sort-wrap">
            <label class="note-filter__label visually-hidden" for="note-sort">並べ替え</label>
            <select id="note-sort" class="note-filter__select" name="sort" form="note-search-form"
                    title="並べ替え">
              <option value="new" {% if sort == "new" %}selected{% endif %}>新しい順</option>
              <option value="old" {% if sort == "old" %}selected{% endif %}>古い順</option>
              <option value="title" {% if sort == "title" %}selected{% endif %}>タイトル順</option>
            </select>
            <svg class="unp-sort-chevron" aria-hidden="true" focusable="false" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="m7 10 5 5 5-5"/></svg>
          </div>
        </div>'''
OLD_SEARCH = '''  function initSearch() {
    const form = select("#note-search-form");
    const sort = select("#note-sort");
    if (!form || !sort) return;
    sort.addEventListener("change", () => form.requestSubmit());
  }'''
NEW_SEARCH = '''  // UNP_SIDEBAR_REFINEMENT_V1: native GET form, no background search requests.
  function initSearch() {
    const form = select("#note-search-form");
    const sort = select("#note-sort");
    const input = select("#note-search");
    const clear = select("#unp-search-clear");
    if (!form || !sort || !input || !clear) return;
    const appliedQuery = input.defaultValue;
    form.dataset.enhanced = "true";
    const updateClear = () => { clear.hidden = input.value.length === 0; };
    updateClear();
    input.addEventListener("input", updateClear);
    sort.addEventListener("change", () => form.requestSubmit());
    clear.addEventListener("click", () => {
      input.value = "";
      updateClear();
      input.focus({preventScroll: true});
      // Clear applied search results, not just the input. If the text was
      // only a draft, no navigation is required.
      if (appliedQuery !== "") form.requestSubmit();
    });
    document.addEventListener("keydown", event => {
      if (event.key !== "/" || event.defaultPrevented || event.isComposing ||
          event.repeat || event.ctrlKey || event.altKey || event.metaKey || event.shiftKey) return;
      if (document.querySelector("dialog[open]")) return;
      const target = event.target;
      if (target instanceof Element && (target.closest("input, textarea, select, button, a, [contenteditable]:not([contenteditable='false']), [role='textbox']") || target.isContentEditable)) return;
      event.preventDefault();
      input.focus();
      input.select();
    });
    window.addEventListener("pageshow", updateClear);
  }'''
CSS = '''/* ===== Note Search & Sort: compact toolbar ===== */
/* UNP_SIDEBAR_REFINEMENT_V1 */
/* Theme tokens are defined once in the settings section below. */
:root {--unp-sidebar-muted:#536176;}
:root[data-theme="dark"] {--unp-sidebar-muted:#a7b6cc;}
.sidebar-content > .search-wrap.unp-search-compact {
  display:block; padding:0; margin:0; min-width:0;
  background:transparent; border:0; border-radius:0;
}
.unp-search-compact .note-filter {width:100%; min-width:0; margin:0;}
.unp-search-compact .note-filter__search {
  display:flex; align-items:center; gap:0; min-width:0; min-height:44px;
  border:1px solid var(--unp-border); border-radius:12px;
  padding:0 3px 0 11px; background:var(--unp-panel); color:var(--unp-ink);
  transition:border-color var(--unp-motion-fast,140ms) ease, background-color var(--unp-motion-fast,140ms) ease;
}
.unp-search-compact .note-filter__search:focus-within {
  border-color:var(--unp-primary); outline:2px solid var(--unp-primary); outline-offset:1px;
}
.unp-search-compact .note-filter__search .note-filter__input {
  flex:1 1 0; width:0; min-width:0; min-height:42px;
  margin:0; padding:0 3px; border:0; border-radius:0; outline:0; box-shadow:none;
  background:transparent; color:var(--unp-ink); font:inherit; font-size:13px;
}
.unp-search-compact .note-filter__input::placeholder {color:var(--unp-sidebar-muted); opacity:1;}
.unp-search-compact .note-filter[data-enhanced] .note-filter__input::-webkit-search-cancel-button {display:none;}
.unp-search-compact .note-filter__button,
.unp-search-compact .unp-search-clear {
  display:grid; place-items:center; flex:0 0 38px; width:38px; height:38px;
  min-height:0; border:0; border-radius:8px; padding:0;
  background:transparent; color:var(--unp-sidebar-muted); cursor:pointer;
  transition:color var(--unp-motion-fast,140ms) ease,background-color var(--unp-motion-fast,140ms) ease,transform var(--unp-motion-fast,140ms) var(--unp-motion-ease,ease-out);
}
.unp-search-compact .note-filter__button {color:var(--unp-primary);}
.unp-search-compact .unp-search-clear[hidden] {display:none;}
.unp-search-compact button svg {width:18px;height:18px;pointer-events:none;}
.unp-search-compact .unp-search-clear svg {width:15px;height:15px;}
.unp-search-compact button:focus-visible {outline:2px solid var(--unp-primary);outline-offset:-2px;}
@media(hover:hover) and (pointer:fine) {
  .unp-search-compact button:hover {background:var(--unp-surface);color:var(--unp-primary);}
}
.section-heading.unp-list-heading {
  display:flex;align-items:center;justify-content:flex-start;gap:6px;
  padding:7px 3px 5px;min-width:0;color:var(--unp-sidebar-muted);
}
.unp-list-title {min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font-size:12px;font-weight:700;}
.unp-list-heading .count {flex:none;margin-right:auto;line-height:1.3;font-variant-numeric:tabular-nums;font-size:11px;padding:3px 7px;}
.unp-sort-wrap {position:relative;flex:0 1 auto;min-width:0;max-width:52%;}
.unp-list-heading .note-filter__select {
  appearance:none;display:block;width:auto;max-width:100%;min-width:0;min-height:36px;
  border:1px solid transparent;border-radius:8px;padding:0 22px 0 8px;
  background:transparent;color:var(--unp-sidebar-muted);cursor:pointer;font:inherit;font-size:12px;font-weight:650;
  text-overflow:ellipsis;
  transition:color var(--unp-motion-fast,140ms) ease, background-color var(--unp-motion-fast,140ms) ease, border-color var(--unp-motion-fast,140ms) ease;
}
.unp-list-heading .note-filter__select option {color:var(--unp-ink);background:var(--unp-surface);}
.unp-list-heading .note-filter__select:focus-visible {outline:2px solid var(--unp-primary);outline-offset:1px;}
.unp-sort-chevron {position:absolute;right:5px;top:50%;translate:0 -50%;width:16px;height:16px;pointer-events:none;color:var(--unp-sidebar-muted);}
@media(hover:hover) and (pointer:fine) {
  .unp-list-heading .note-filter__select:hover {background:var(--unp-panel);color:var(--unp-ink);border-color:var(--unp-border);}
}
.unp-sort-wrap:focus-within .unp-sort-chevron {color:var(--unp-primary);}
@media(pointer:coarse) {
  .unp-search-compact .note-filter__search {min-height:50px;}
  .unp-search-compact .note-filter__button,.unp-search-compact .unp-search-clear {width:44px;height:44px;flex-basis:44px;}
  .unp-search-compact .note-filter__search .note-filter__input {min-height:48px;}
  .unp-list-heading .note-filter__select {min-height:44px;}
}
@media(prefers-reduced-motion:reduce) {
  .unp-search-compact .note-filter__search,.unp-search-compact button,.unp-list-heading .note-filter__select {transition:none;}
}

'''
MOTION = '''
/* ===== Interaction motion: compact sidebar refinement ===== */
/* Prefer compositor-friendly transforms/opacity. No global transition:all,
   no animation of layout geometry, and no permanent will-change. */
:root { --unp-interaction-ease:cubic-bezier(.2,.75,.25,1); --unp-interaction-press:120ms; }
/* Keep keyboard outlines inside the clipped scrolling note list. */
.note-list .note-card:focus-visible {outline:2px solid var(--unp-primary);outline-offset:-3px;}
@media(prefers-reduced-motion:no-preference) {
  .unp-search-compact button:active:not(:disabled) {transform:scale(.93);}
  .unp-search-compact .unp-search-clear:not([hidden]) svg {animation:unp-panel-enter 120ms ease-out both;}
  .unp-pin-button,.unp-settings-trigger,.unp-settings-close,.delete-button,.delete-dialog-actions button,.unp-settings-actions button,.unp-settings-tabs [role="tab"] {
    transition:transform var(--unp-interaction-press) var(--unp-interaction-ease),color var(--unp-motion-fast) ease,background-color var(--unp-motion-fast) ease,border-color var(--unp-motion-fast) ease;
  }
  .unp-pin-button:active:not([aria-disabled="true"]),.unp-settings-trigger:active,.unp-settings-close:active,.delete-button:active,.delete-dialog-actions button:active,.unp-settings-actions button:active,.unp-settings-tabs [role="tab"]:active {transform:scale(.96);}
  /* Note hover uses color, rather than shifting the entire clickable area. */
  .note-card:hover:not(.active) {transform:none;}
  .note-card:active {transform:scale(.985);}
  /* Native dialogs remain usable if discrete transitions are unsupported. */
  #unp-settings-dialog[open],.delete-note-dialog[open] {animation:unp-dialog-enter 200ms var(--unp-interaction-ease) both;}
  #unp-settings-dialog[open]::backdrop,.delete-note-dialog[open]::backdrop {animation:unp-backdrop-enter 180ms ease-out both;}
  .unp-settings-content [role="tabpanel"]:not([hidden]) {animation:unp-panel-enter 170ms var(--unp-interaction-ease) both;}
  .save-status[data-state="saved"]::before {animation:unp-saved-dot 220ms var(--unp-interaction-ease) both;}
}
@keyframes unp-dialog-enter {from{opacity:0;transform:translateY(6px) scale(.985);}to{opacity:1;transform:none;}}
@keyframes unp-backdrop-enter {from{opacity:0;}to{opacity:1;}}
@keyframes unp-panel-enter {from{opacity:0;transform:translateY(4px);}to{opacity:1;transform:none;}}
@keyframes unp-saved-dot {0%{transform:scale(.75);opacity:.55;}55%{transform:scale(1.2);}100%{transform:scale(1);opacity:1;}}
@media(prefers-reduced-motion:reduce) {
  #unp-settings-dialog,.delete-note-dialog,.unp-settings-content [role="tabpanel"],.save-status[data-state="saved"]::before {animation:none;}
  .unp-settings-trigger,.unp-settings-close,.unp-pin-button,.delete-button,.delete-dialog-actions button,.unp-settings-actions button,.unp-settings-tabs [role="tab"] {transition:none;}
}
'''


def once(text, old, new, label):
    if text.count(old) != 1:
        raise ValueError(f'{label}: expected exactly one matching anchor; no update performed.')
    return text.replace(old, new, 1)


def patch(sources):
    html, css, js = (sources[p] for p in PATHS)
    flags = [MARKER in text for text in (html, css, js)]
    if all(flags): return sources.copy()
    if any(flags): raise ValueError('Partial sidebar update. Restore all three frontend files from backup first.')
    if not ('UNP_SETTINGS_DIALOG_BEGIN' in html and 'UNP_PIN_UI_V1' in html and
            'UNP_SETTINGS_CSS_END' in css and 'UNP_PIN_MOTION_V2' in css and
            'UNP_SETTINGS_MODULE_END' in js and 'UNP_PIN_MOTION_V2' in js):
        raise ValueError('Settings v1 and Pin Motion v2 are required. Existing files have not been changed.')
    html = once(html, OLD_HTML, NEW_HTML, 'search/list toolbar template')
    # Replace the existing dedicated search CSS section rather than stacking a second one.
    start = '/* ===== Note Search & Sort ===== */'
    end = '/* ===== Original: animations.css ===== */'
    if css.count(start) != 1 or css.count(end) != 1 or css.index(start) >= css.index(end):
        raise ValueError('Existing search CSS section not recognized.')
    a, b = css.index(start), css.index(end)
    css = css[:a] + CSS + css[b:]
    # Remove legacy CSS selectors that conflict with the new unified search control.
    for old in (
        '.search-wrap { display:flex;align-items:center;gap:10px;background:#f5f7f9;border:1px solid #f0f1f4;border-radius:10px;padding:11px 13px;color:#9aa4b3; }\n',
        '.search-wrap span { font-size:19px; line-height:14px; }\n',
        '.search-wrap input { width:100%; border:0;outline:0;background:transparent;font-size:12px;color:var(--muted); }\n',
        '.search-wrap input::placeholder { color:#a3acb8; }\n',
        ':root[data-theme="dark"] .search-wrap,\n',
        ':root[data-theme="dark"] .note-filter__input,\n',
        ':root[data-theme="dark"] .note-filter__select,\n',
        ':root[data-theme="dark"] .note-filter__button,\n',
        ':root[data-theme="dark"] .note-filter__input:focus,\n:root[data-theme="dark"] .note-filter__select:focus {border-color:#89a8ff;box-shadow:0 0 0 3px #536adc55;}\n',
    ):
        # For locally tweaked CSS, do not silently leave a conflicting legacy rule.
        if css.count(old) != 1:
            raise ValueError('Expected legacy CSS rule missing/duplicated: ' + old[:90])
        css = css.replace(old, '', 1)
    css = css.rstrip() + '\n' + MOTION
    js = once(js, OLD_SEARCH, NEW_SEARCH, 'search controller')
    # Preserve SVG children during locale updates. The labels array previously
    # assigned textContent to the whole search button, which would erase its icon.
    js = once(js, "['.note-filter__button','nav.search']", "['.unp-search-submit-label','nav.search']", 'search button locale binding')
    js = once(js, "['#note-search','nav.searchPlaceholder']", "['#note-search','nav.searchLabel']", 'search placeholder binding')
    js = once(js, "'nav.sortNew':'更新日時が新しい順','nav.sortOld':'更新日時が古い順', 'nav.sortTitle':'タイトル順',", "'nav.sortNew':'新しい順','nav.sortOld':'古い順', 'nav.sortTitle':'タイトル順',\n      'nav.sortHelp':'更新日時またはタイトルで並べ替え', 'nav.clear':'検索をクリア',", 'Japanese locale')
    js = once(js, "'nav.sortNew':'Most recently updated','nav.sortOld':'Least recently updated','nav.sortTitle':'Title (ascending)',", "'nav.sortNew':'Newest','nav.sortOld':'Oldest','nav.sortTitle':'Title',\n      'nav.sortHelp':'Sort by last update or title', 'nav.clear':'Clear search',", 'English locale')
    js = once(js, "    const open = $('#unp-settings-open');\n    if (open) { open.setAttribute", """    const searchSubmit = $('.note-filter__button');
    if (searchSubmit) searchSubmit.title = t('nav.search');
    const searchInput = $('#note-search');
    if (searchInput) searchInput.title = t('nav.searchPlaceholder');
    const searchClear = $('#unp-search-clear');
    if (searchClear) {
      searchClear.title = t('nav.clear');
      searchClear.setAttribute('aria-label', t('nav.clear'));
    }
    const searchSort = $('#note-sort');
    if (searchSort) searchSort.title = t('nav.sortHelp');
    const open = $('#unp-settings-open');
    if (open) { open.setAttribute""", 'localized tooltips')
    return dict(zip(PATHS, (html, css, js)))


def apply(root, dry_run=False):
    if not (root/'app.py').is_file(): raise ValueError('Run from the UltimateNotePad repository root.')
    originals = {p: (root/p).read_bytes() for p in PATHS}
    sources = {p: data.decode('utf-8').replace('\r\n','\n') for p,data in originals.items()}
    changed = patch(sources)
    if changed == sources:
        print('既に適用済みです。変更なし。'); return
    with tempfile.TemporaryDirectory() as directory:
        node = shutil.which('node')
        if node:
            check = Path(directory)/'app.js'; check.write_text(changed[PATHS[2]], encoding='utf-8')
            subprocess.run([node,'--check',str(check)],check=True)
        else: print('Node.jsなし：JS構文検証は省略します。')
    for p in PATHS: print('変更予定:', p)
    if dry_run:
        print('ドライラン成功。変更なし。'); return
    stamp=datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S-%f')
    backup=root/'.refactor-backups'/f'before-sidebar-refinement-{stamp}.zip'
    backup.parent.mkdir(exist_ok=True)
    with zipfile.ZipFile(backup,'x',zipfile.ZIP_DEFLATED) as z:
        for p,data in originals.items(): z.writestr(p,data)
    if any((root/p).read_bytes()!=originals[p] for p in PATHS):
        raise ValueError('Files changed concurrently; stop and run again.')
    staged={}; written=[]
    try:
        for p,new in changed.items():
            target=root/p
            with tempfile.NamedTemporaryFile(dir=target.parent,prefix='.unp-ui-',delete=False) as f:
                staged[p]=Path(f.name); f.write(new.encode('utf-8'))
            shutil.copymode(target,staged[p])
        for p,temp in staged.items():
            temp.replace(root/p); written.append(p)
    except BaseException:
        for p in written: (root/p).write_bytes(originals[p])
        raise
    finally:
        for temp in staged.values(): temp.unlink(missing_ok=True)
    print('適用完了。バックアップ:',backup.relative_to(root))
    print('Python・SQLite・autosave.js は変更していません。')

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo',default='.')
    parser.add_argument('--dry-run',action='store_true')
    args=parser.parse_args()
    try: apply(Path(args.repo).resolve(),args.dry_run)
    except (ValueError,OSError,subprocess.CalledProcessError) as e:
        print('エラー:',e,file=sys.stderr); sys.exit(1)
