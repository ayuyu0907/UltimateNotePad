/**
 * UltimateNotePad UI controller
 * Search, dialogs, and date display share a single DOM-ready entry point.
 * Autosave remains a separate module because it owns its retry/queue lifecycle.
 */
(() => {
  "use strict";

  const select = (selector, scope = document) => scope.querySelector(selector);
  const selectAll = (selector, scope = document) => scope.querySelectorAll(selector);

  // Keep the modal's animation and focus behavior in one place.
  function bindDialog({ id, openers, closers, initialFocus, resetOnOpen = false, animateClose = false }) {
    const dialog = select(id);
    if (!dialog) return;

    const form = select("form", dialog);
    const openButtons = openers.map((id) => select(id)).filter(Boolean);
    const closeButtons = closers.map((id) => select(id)).filter(Boolean);
    const reduceMotion = window.matchMedia?.("(prefers-reduced-motion: reduce)");
    let closeTimer = null;
    let lastOpener = null;

    function openDialog(opener) {
      if (dialog.open) return;
      if (closeTimer !== null) {
        window.clearTimeout(closeTimer);
        closeTimer = null;
      }
      delete dialog.dataset.closing;
      if (resetOnOpen) form?.reset();
      lastOpener = opener;
      dialog.showModal();
      select(initialFocus, dialog)?.focus();
    }

    function closeDialog() {
      if (!dialog.open || Object.hasOwn(dialog.dataset, "closing")) return;
      if (!animateClose || reduceMotion?.matches) {
        dialog.close();
        return;
      }
      dialog.dataset.closing = "";
      closeTimer = window.setTimeout(() => {
        closeTimer = null;
        if (dialog.open) dialog.close();
      }, 200);
    }

    openButtons.forEach((button) => {
      button.addEventListener("click", () => openDialog(button));
    });
    closeButtons.forEach((button) => {
      button.addEventListener("click", closeDialog);
    });

    // Only a click outside the dialog's visible rectangle closes it.
    dialog.addEventListener("click", (event) => {
      if (event.target !== dialog) return;
      const rect = dialog.getBoundingClientRect();
      const outside = event.clientX < rect.left || event.clientX > rect.right ||
        event.clientY < rect.top || event.clientY > rect.bottom;
      if (outside) closeDialog();
    });

    if (animateClose) {
      dialog.addEventListener("cancel", (event) => {
        event.preventDefault();
        closeDialog();
      });
    }
    dialog.addEventListener("close", () => {
      if (closeTimer !== null) {
        window.clearTimeout(closeTimer);
        closeTimer = null;
      }
      delete dialog.dataset.closing;
      lastOpener?.focus();
    });
  }

  function initDialogs() {
    bindDialog({
      id: "#create-note-dialog",
      openers: ["#create-note-open", "#welcome-create-note"],
      closers: ["#create-note-close", "#create-note-cancel"],
      initialFocus: "#create-title",
      resetOnOpen: true,
      animateClose: true
    });
    bindDialog({
      id: "#delete-note-dialog",
      openers: ["#delete-note-open"],
      closers: ["#delete-note-cancel"],
      initialFocus: "#delete-note-cancel"
    });
  }

  function initSearch() {
    const form = select("#note-search-form");
    const sort = select("#note-sort");
    if (!form || !sort) return;
    sort.addEventListener("change", () => form.requestSubmit());
  }

  // Existing DB values are interpreted as UTC, and displayed in Tokyo time.
  const jstFormatter = new Intl.DateTimeFormat("ja-JP", {
    timeZone: "Asia/Tokyo",
    year: "numeric", month: "2-digit", day: "2-digit",
    hour: "2-digit", minute: "2-digit", hourCycle: "h23"
  });

  function parseUTC(value) {
    if (!value) return null;
    const match = String(value).trim().match(
      /^(\d{4})-(\d{2})-(\d{2})[ T](\d{2}):(\d{2})(?::(\d{2}))?(?:Z)?$/
    );
    if (!match) return null;
    const [, year, month, day, hour, minute, second = "00"] = match;
    const date = new Date(`${year}-${month}-${day}T${hour}:${minute}:${second}Z`);
    if (!Number.isFinite(date.getTime())) return null;
    if (date.getUTCFullYear() !== Number(year) ||
        date.getUTCMonth() + 1 !== Number(month) ||
        date.getUTCDate() !== Number(day) ||
        date.getUTCHours() !== Number(hour) ||
        date.getUTCMinutes() !== Number(minute) ||
        date.getUTCSeconds() !== Number(second)) return null;
    return date;
  }

  function formatJST(date) {
    const parts = Object.fromEntries(jstFormatter.formatToParts(date)
      .filter((part) => part.type !== "literal")
      .map((part) => [part.type, part.value]));
    return `${parts.year}/${parts.month}/${parts.day} ${parts.hour}:${parts.minute}`;
  }

  function initDates() {
    for (const element of selectAll("[data-utc]")) {
      const date = parseUTC(element.dataset.utc);
      if (!date) continue;
      const display = formatJST(date);
      element.textContent = element.classList.contains("last-updated")
        ? `最終更新：${display}` : display;
      if (element.tagName === "TIME") element.dateTime = date.toISOString();
      element.title = `${display} (JST)`;
    }
  }

  function init() {
    initDialogs();
    initSearch();
    initDates();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init, { once: true });
  } else {
    init();
  }
})();

/* UNP_SETTINGS_MODULE_BEGIN */
/*
 * UltimateNotePad — Preferences, theme, locale, and settings UI (v1)
 * Bundled into static/js/app.js by install_settings.py. No new runtime JS files.
 * Account sync is intentionally NOT implemented. Preferences remain local-only.
 */
(() => {
  'use strict';

  const KEY = 'unp.preferences.v1';
  const DEFAULT = Object.freeze({
    version: 1,
    theme: 'system',
    language: 'ja',
    editor: { autosave: true, compact: false }
  });

  const messages = {
    ja: {
      'settings.open':'設定を開く', 'settings.title':'設定',
      'settings.subtitle':'UltimateNotePadの使い方をカスタマイズ',
      'settings.close':'設定を閉じる',
      'settings.appearance':'外観と言語', 'settings.editor':'エディター',
      'settings.data':'データと同期',
      'theme.heading':'テーマ', 'theme.help':'画面の配色を選択します。',
      'theme.system':'システム設定', 'theme.light':'ライト', 'theme.dark':'ダーク',
      'language.heading':'表示言語', 'language.help':'画面の固定メッセージに適用されます。メモの内容は翻訳しません。',
      'language.ja':'日本語', 'language.en':'English（英語）',
      'editor.autosave':'自動保存',
      'editor.autosaveHelp':'入力停止から約1秒後に保存します。無効の場合は手動保存してください。',
      'editor.compact':'コンパクトな編集画面',
      'editor.compactHelp':'右側の編集領域の余白を小さくします。',
      'editor.notes':'編集設定はこの端末のみに保存されます。',
      'data.local':'現在はローカル設定',
      'data.localDesc':'設定はこのブラウザにのみ保存されます。メモ本体は既存のSQLiteデータベースに保存されます。',
      'data.export':'設定をエクスポート',
      'data.import':'設定をインポート',
      'data.reset':'初期設定に戻す',
      'data.sync':'将来のアカウント同期',
      'data.syncDesc':'アカウント・端末間同期は未実装です。ログイン、クラウド同期、メモのバックアップが有効になったわけではありません。',
      'data.exportSuccess':'設定ファイルを出力しました。',
      'data.importSuccess':'設定を読み込みました。',
      'data.importError':'設定ファイルを読み込めません。有効なJSONを選択してください。',
      'data.resetSuccess':'設定を初期化しました。',
      'data.resetConfirm':'すべての表示設定を初期状態に戻しますか？（メモは削除されません）',
      'settings.saved':'設定を保存しました。',
      'nav.all':'すべてのメモ', 'nav.notes':'メモ',
      'nav.emptyTitle':'メモはまだありません',
      'nav.emptyDesc':'右上の「＋」から最初のメモを作成しましょう。',
      'nav.emptySearchTitle':'該当するメモはありません',
      'nav.emptySearchDesc':'検索条件を変更してもう一度お試しください。',
      'nav.searchLabel':'メモを検索', 'nav.searchPlaceholder':'タイトル・本文を検索...',
      'nav.search':'検索', 'nav.sortLabel':'並べ替え',
      'nav.sortNew':'更新日時が新しい順','nav.sortOld':'更新日時が古い順', 'nav.sortTitle':'タイトル順',
      'nav.selectNote':'メモを選択してください',
      'editor.lastUpdated':'最終更新：',
      'editor.titleLabel':'メモのタイトル','editor.titlePlaceholder':'無題のメモ',
      'editor.contentLabel':'メモの本文','editor.contentPlaceholder':'ここにメモを書き始めましょう...',
      'editor.delete':'メモを削除','editor.save':'変更を保存',
      'editor.welcomeTitle':'書き留める、整理する。',
      'editor.welcomeBody':'左側からメモを選ぶか、新しいメモを作成してください。',
      'editor.welcomeCreate':'＋ 新しいメモを作成',
      'editor.footer':'入力内容は自動的に保存されます。手動保存も利用できます。',
      'editor.footerManual':'自動保存は無効です。変更は「変更を保存」で保存してください。',
      'create.title':'新しいメモ','create.subtitle':'アイデアを書き留めましょう。',
      'create.labelTitle':'タイトル','create.labelContent':'本文（任意）',
      'create.placeholderTitle':'例：今日の授業ノート','create.placeholderContent':'メモの内容を入力...',
      'create.cancel':'キャンセル','create.submit':'＋ メモを作成',
      'delete.title':'メモを削除しますか？','delete.description':'「{title}」を削除します。この操作は元に戻せません。',
      'delete.cancel':'キャンセル','delete.confirm':'削除する',
      'save.saved':'保存済み','save.saving':'保存中...','save.dirty':'未保存の変更',
      'save.error':'保存失敗','save.retry':'再試行中 ({number}/{max})',
      'save.reconnected':'再接続しました','save.emptyTitle':'タイトルを入力してください',
      'accessibility.openSettings':'設定',
      'accessibility.newNote':'新しいメモを作成', 'accessibility.close':'閉じる',
      'accessibility.noteList':'メモ一覧', 'accessibility.editor':'メモ編集画面',
      'accessibility.bold':'太字（後日実装）','accessibility.italic':'斜体（後日実装）',
      'accessibility.underline':'下線（後日実装）','accessibility.heading':'見出し（後日実装）',
      'accessibility.list':'箇条書き（後日実装）',
    },
    en: {
      'settings.open':'Open settings', 'settings.title':'Settings',
      'settings.subtitle':'Customize your UltimateNotePad experience',
      'settings.close':'Close settings',
      'settings.appearance':'Appearance & language','settings.editor':'Editor',
      'settings.data':'Data & sync',
      'theme.heading':'Theme','theme.help':'Choose the color scheme for the app.',
      'theme.system':'Use system setting','theme.light':'Light','theme.dark':'Dark',
      'language.heading':'Display language','language.help':'Changes interface labels only. Your note contents are never translated.',
      'language.ja':'日本語 (Japanese)','language.en':'English',
      'editor.autosave':'Autosave',
      'editor.autosaveHelp':'Save about one second after typing stops. When off, use Save changes.',
      'editor.compact':'Compact editor layout',
      'editor.compactHelp':'Reduce padding inside the editor panel.',
      'editor.notes':'Editor preferences are stored on this device only.',
      'data.local':'Local settings only',
      'data.localDesc':'Preferences are saved only in this browser. Notes still live in the existing SQLite database.',
      'data.export':'Export preferences',
      'data.import':'Import preferences',
      'data.reset':'Reset preferences',
      'data.sync':'Future account sync',
      'data.syncDesc':'Accounts and cross-device sync are not implemented. This does not enable login, cloud sync or note backups.',
      'data.exportSuccess':'Preferences file exported.',
      'data.importSuccess':'Preferences imported.',
      'data.importError':'Cannot read this preferences file. Select a valid JSON file.',
      'data.resetSuccess':'Preferences reset to defaults.',
      'data.resetConfirm':'Reset display preferences to defaults? (Notes will not be deleted.)',
      'settings.saved':'Settings saved.',
      'nav.all':'All notes','nav.notes':'Notes',
      'nav.emptyTitle':'No notes yet',
      'nav.emptyDesc':'Use the + button above to create your first note.',
      'nav.emptySearchTitle':'No matching notes',
      'nav.emptySearchDesc':'Try changing your search filters.',
      'nav.searchLabel':'Search notes','nav.searchPlaceholder':'Search titles and content...',
      'nav.search':'Search','nav.sortLabel':'Sort by',
      'nav.sortNew':'Most recently updated','nav.sortOld':'Least recently updated','nav.sortTitle':'Title (ascending)',
      'nav.selectNote':'Select a note',
      'editor.lastUpdated':'Last updated: ',
      'editor.titleLabel':'Note title','editor.titlePlaceholder':'Untitled note',
      'editor.contentLabel':'Note content','editor.contentPlaceholder':'Start writing your note...',
      'editor.delete':'Delete note','editor.save':'Save changes',
      'editor.welcomeTitle':'Capture it. Organize it.',
      'editor.welcomeBody':'Choose a note on the left or create a new note.',
      'editor.welcomeCreate':'+ Create a new note',
      'editor.footer':'Your changes are saved automatically. You can also save manually.',
      'editor.footerManual':'Autosave is off. Use “Save changes” to save edits.',
      'create.title':'New note','create.subtitle':'Capture an idea while it is fresh.',
      'create.labelTitle':'Title','create.labelContent':'Content (optional)',
      'create.placeholderTitle':'e.g. Today’s class notes','create.placeholderContent':'Write a note...',
      'create.cancel':'Cancel','create.submit':'+ Create note',
      'delete.title':'Delete this note?','delete.description':'Delete “{title}”? This cannot be undone.',
      'delete.cancel':'Cancel','delete.confirm':'Delete',
      'save.saved':'Saved','save.saving':'Saving...','save.dirty':'Unsaved changes',
      'save.error':'Save failed','save.retry':'Retrying ({number}/{max})',
      'save.reconnected':'Reconnected','save.emptyTitle':'Please enter a title',
      'accessibility.openSettings':'Settings',
      'accessibility.newNote':'Create new note','accessibility.close':'Close',
      'accessibility.noteList':'Notes list', 'accessibility.editor':'Note editor',
      'accessibility.bold':'Bold (planned)','accessibility.italic':'Italic (planned)',
      'accessibility.underline':'Underline (planned)','accessibility.heading':'Heading (planned)',
      'accessibility.list':'Bulleted list (planned)',
    }
  };

  // This adapter is the only persistence boundary. Future API-based account
  // synchronization can replace this implementation without changing UI logic.
  const storage = {
    read() {
      try { return JSON.parse(window.localStorage.getItem(KEY) || 'null'); }
      catch { return null; }
    },
    write(value) {
      try { window.localStorage.setItem(KEY, JSON.stringify(value)); return true; }
      catch { return false; }
    }
  };
  function normalize(value) {
    const v = value && typeof value === 'object' && !Array.isArray(value) ? value : {};
    const e = v.editor && typeof v.editor === 'object' && !Array.isArray(v.editor) ? v.editor : {};
    return {
      version: 1,
      theme: ['system', 'light', 'dark'].includes(v.theme) ? v.theme : DEFAULT.theme,
      language: ['ja', 'en'].includes(v.language) ? v.language : DEFAULT.language,
      editor: {
        autosave: typeof e.autosave === 'boolean' ? e.autosave : DEFAULT.editor.autosave,
        compact: typeof e.compact === 'boolean' ? e.compact : DEFAULT.editor.compact
      }
    };
  }
  let prefs = normalize(storage.read());
  const t = (key, params = {}) => {
    const entry = messages[prefs.language][key] ?? messages.ja[key] ?? key;
    return entry.replace(/\{(\w+)\}/g, (_, name) => String(params[name] ?? ''));
  };
  function updateAppearance() {
    const osDark = window.matchMedia?.('(prefers-color-scheme: dark)')?.matches ?? false;
    const dark = prefs.theme === 'dark' || (prefs.theme === 'system' && osDark);
    document.documentElement.dataset.theme = dark ? 'dark' : 'light';
    document.documentElement.dataset.density = prefs.editor.compact ? 'compact' : 'comfortable';
    document.documentElement.lang = prefs.language;
    document.documentElement.style.colorScheme = dark ? 'dark' : 'light';
  }
  function statusText(state, original = '') {
    const retryMatch = /(?:再試行中|Retrying)\s*\((\d+)\/(\d+)\)/.exec(original);
    if (retryMatch) return t('save.retry', { number: retryMatch[1], max: retryMatch[2] });
    if (/再接続|Reconnected/.test(original)) return t('save.reconnected');
    if (/タイトルを入力|enter a title/.test(original)) return t('save.emptyTitle');
    return t({saved:'save.saved',saving:'save.saving',dirty:'save.dirty',error:'save.error'}[state] || 'save.saved');
  }
  function get() { return normalize(prefs); }
  function broadcast() {
    updateAppearance();
    updateTranslatedUI();
    window.dispatchEvent(new CustomEvent('unp:preferenceschange', {detail: get()}));
  }
  function set(value) {
    prefs = normalize(value);
    storage.write(prefs);
    broadcast();
  }
  window.UNPSettings = Object.freeze({ get, set, translate:t, statusText, storageVersion:1 });

  const $ = (query, parent = document) => parent.querySelector(query);
  const $$ = (query, parent = document) => [...parent.querySelectorAll(query)];
  const labels = [
    ['.section-heading > span:first-child','nav.all'],
    ['.search-wrap label[for="note-search"]','nav.searchLabel'],
    ['.note-filter__label[for="note-search"]','nav.searchLabel'],
    ['.note-filter__button','nav.search'],
    ['.search-wrap label[for="note-sort"]','nav.sortLabel'],
    ['.note-filter__label[for="note-sort"]','nav.sortLabel'],
    ['#note-sort option[value="new"]','nav.sortNew'],
    ['#note-sort option[value="old"]','nav.sortOld'],
    ['#note-sort option[value="title"]','nav.sortTitle'],
    ['.mode-label','nav.selectNote'],
    ['.note-edit-form label[for="note-title"]','editor.titleLabel'],
    ['.note-edit-form label[for="note-content"]','editor.contentLabel'],
    ['#delete-note-open','editor.delete'],
    ['.note-edit-form .save-button','editor.save'],
    ['.welcome-editor h1','editor.welcomeTitle'],
    ['.welcome-editor p','editor.welcomeBody'],
    ['#welcome-create-note','editor.welcomeCreate'],
    ['#create-note-heading','create.title'],
    ['.dialog-header p','create.subtitle'],
    ['.dialog-field label[for="create-title"]','create.labelTitle'],
    ['.dialog-field label[for="create-content"]','create.labelContent'],
    ['#create-note-cancel','create.cancel'],
    ['.dialog-submit','create.submit'],
    ['#delete-note-heading','delete.title'],
    ['#delete-note-cancel','delete.cancel'],
    ['.delete-confirm','delete.confirm'],
  ];
  const placeholders = [
    ['#note-search','nav.searchPlaceholder'],
    ['#note-title','editor.titlePlaceholder'],
    ['#note-content','editor.contentPlaceholder'],
    ['#create-title','create.placeholderTitle'],
    ['#create-content','create.placeholderContent'],
  ];

  let currentDeletionTitle = null;
  function updateTranslatedUI() {
    for (const [selector, key] of labels) {
      const el = $(selector);
      if (!el) continue;
      // Retain markup (e.g. the required-field asterisk in create title labels).
      if (el.matches('label') && el.querySelector('span')) {
        const node = [...el.childNodes].find(n => n.nodeType === Node.TEXT_NODE);
        if (node) node.textContent = t(key) + ' ';
      } else {
        el.textContent = t(key);
      }
    }
    for (const [selector, key] of placeholders) {
      const el = $(selector);
      if (el) el.placeholder = t(key);
    }
    const open = $('#unp-settings-open');
    if (open) { open.setAttribute('aria-label', t('settings.open')); open.title=t('settings.open'); }
    const close = $('#unp-settings-close');
    if (close) close.setAttribute('aria-label', t('settings.close'));
    const noteOpen = $('#create-note-open');
    if (noteOpen) {
      noteOpen.setAttribute('aria-label', t('accessibility.newNote'));
      noteOpen.title = t('accessibility.newNote');
    }
    const createClose = $('#create-note-close');
    if (createClose) createClose.setAttribute('aria-label', t('accessibility.close'));
    const sidebar = $('.sidebar');
    if (sidebar) sidebar.setAttribute('aria-label', t('accessibility.noteList'));
    const noteList = $('.note-list');
    if (noteList) noteList.setAttribute('aria-label', t('nav.notes'));
    const editorPanel = $('.editor-panel');
    if (editorPanel) editorPanel.setAttribute('aria-label', t('accessibility.editor'));
    $$('.editor-toolbar button[title]').forEach((button, i) => {
      const keys = ['accessibility.bold','accessibility.italic','accessibility.underline',
                    'accessibility.heading','accessibility.list'];
      if (keys[i]) button.title = t(keys[i]);
    });
    for (const el of $$('[data-unp-i18n]')) {
      el.textContent = t(el.dataset.unpI18n);
    }
    const crumb = $('.breadcrumb');
    if (crumb) {
      const tail = [...crumb.childNodes].reverse().find(n => n.nodeType === Node.TEXT_NODE);
      if (tail) tail.textContent = ` ${t('nav.notes')}`;
    }
    const empty = $('.empty-list');
    if (empty) {
      const hasSearch = Boolean($('#note-search')?.value.trim());
      const heading = $('strong', empty);
      const hint = $('span:last-child', empty);
      if (heading) heading.textContent = t(hasSearch ? 'nav.emptySearchTitle' : 'nav.emptyTitle');
      if (hint) hint.textContent = t(hasSearch ? 'nav.emptySearchDesc' : 'nav.emptyDesc');
    }
    const status = $('#save-status');
    if (status) status.textContent = statusText(status.dataset.state || 'saved', status.textContent);
    const updated = $('.last-updated');
    if (updated) {
      const display = updated.textContent.replace(/^(最終更新[：:]|Last updated:)\s*/, '').trim();
      updated.textContent = t('editor.lastUpdated') + display;
    }
    const footer = $('.workspace-footer');
    if (footer && $('.note-edit-form')) footer.textContent = t(prefs.editor.autosave ? 'editor.footer' : 'editor.footerManual');
    const deleteDescription = $('#delete-note-description');
    if (deleteDescription) {
      if (currentDeletionTitle === null) {
        const original = deleteDescription.textContent.trim();
        const match = original.match(/^「([\s\S]*)」を削除します/);
        currentDeletionTitle = match ? match[1] : '';
      }
      if (currentDeletionTitle) deleteDescription.textContent = t('delete.description', {title:currentDeletionTitle});
    }
    $$('input[name="unp-theme"]').forEach(el => {el.checked = el.value === prefs.theme;});
    const language = $('#unp-language');
    if (language) language.value = prefs.language;
    const autosave = $('#unp-autosave');
    if (autosave) autosave.checked = prefs.editor.autosave;
    const compact = $('#unp-compact');
    if (compact) compact.checked = prefs.editor.compact;
  }

  function init() {
    updateAppearance();
    updateTranslatedUI();
    const dialog = $('#unp-settings-dialog');
    const open = $('#unp-settings-open');
    const close = $('#unp-settings-close');
    if (!dialog || !open || !close) return;
    let lastFocus = null;
    open.addEventListener('click', () => {
      lastFocus = document.activeElement;
      dialog.showModal();
      const selectedTab = $('[role="tab"][aria-selected="true"]', dialog);
      selectedTab?.focus();
    });
    close.addEventListener('click', () => dialog.close());
    dialog.addEventListener('close', () => lastFocus?.focus?.());
    dialog.addEventListener('click', (event) => {
      if (event.target !== dialog) return;
      const rect = dialog.getBoundingClientRect();
      if (event.clientX < rect.left || event.clientX > rect.right || event.clientY < rect.top || event.clientY > rect.bottom) dialog.close();
    });

    const tabs = $$('[role="tab"]', dialog);
    function selectTab(tab, focus = false) {
      tabs.forEach(item => {
        const active = item === tab;
        item.setAttribute('aria-selected', String(active));
        item.tabIndex = active ? 0 : -1;
      });
      $$('[role="tabpanel"]', dialog).forEach(panel => {panel.hidden = panel.id !== tab.getAttribute('aria-controls');});
      if (focus) tab.focus();
    }
    tabs.forEach((tab, i) => {
      tab.addEventListener('click', () => selectTab(tab));
      tab.addEventListener('keydown', (event) => {
        const next = event.key === 'ArrowRight' || event.key === 'ArrowDown' ? i + 1 :
          event.key === 'ArrowLeft' || event.key === 'ArrowUp' ? i - 1 :
          event.key === 'Home' ? 0 : event.key === 'End' ? tabs.length - 1 : null;
        if (next === null) return;
        event.preventDefault();
        selectTab(tabs[(next + tabs.length) % tabs.length], true);
      });
    });

    $$('input[name="unp-theme"]',dialog).forEach(input => input.addEventListener('change', () => {
      if (input.checked) set({...prefs, theme: input.value});
    }));
    $('#unp-language')?.addEventListener('change', event => set({...prefs, language: event.target.value}));
    $('#unp-autosave')?.addEventListener('change', event => set({...prefs, editor:{...prefs.editor, autosave:event.target.checked}}));
    $('#unp-compact')?.addEventListener('change', event => set({...prefs, editor:{...prefs.editor, compact:event.target.checked}}));

    const feedback = $('#unp-settings-feedback');
    const notify = key => {if (feedback) feedback.textContent=t(key);};
    $('#unp-reset')?.addEventListener('click', () => {
      if (!window.confirm(t('data.resetConfirm'))) return;
      set(DEFAULT);
      notify('data.resetSuccess');
    });
    $('#unp-export')?.addEventListener('click', () => {
      const blob = new Blob([JSON.stringify(get(), null, 2) + '\n'], {type:'application/json'});
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'UltimateNotePad-preferences.json';
      document.body.append(a);
      a.click();
      a.remove();
      window.setTimeout(() => URL.revokeObjectURL(url), 1000);
      notify('data.exportSuccess');
    });
    const file = $('#unp-import-file');
    $('#unp-import')?.addEventListener('click', () => file?.click());
    file?.addEventListener('change', async () => {
      const candidate = file.files?.[0];
      file.value='';
      if (!candidate) return;
      if (candidate.size > 100_000) { notify('data.importError'); return; }
      try {
        const json = JSON.parse(await candidate.text());
        if (!json || json.version !== 1 || typeof json !== 'object' || Array.isArray(json)) throw new Error('schema version');
        set(json);
        notify('data.importSuccess');
      } catch (error) {
        console.warn('Preferences import failed', error);
        notify('data.importError');
      }
    });

    const mq = window.matchMedia?.('(prefers-color-scheme: dark)');
    mq?.addEventListener?.('change', () => {if (prefs.theme === 'system') updateAppearance();});
    window.addEventListener('storage', event => {
      if (event.key === KEY) {prefs = normalize(storage.read()); broadcast();}
    });
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init, {once:true});
  else init();
})();
/* UNP_SETTINGS_MODULE_END */
