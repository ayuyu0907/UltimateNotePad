"""Offline integration checks; no real user DB or repository is modified."""
import importlib.util
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
import zipfile

SOURCE = Path(__file__).resolve().parents[1]
LOCAL_PREVIOUS = Path('/mnt/data/UltimateNotePad-Refactor-v2')
OLD_TEMPLATE = Path('/mnt/data/unp_refactor_workspace/source/templates/index.html')
OLD_STYLE = Path('/mnt/data/unp_refactor_workspace/base/static/css/style.css')

spec = importlib.util.spec_from_file_location('settings_installer', SOURCE/'install_settings.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class SettingsInstallerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        for folder in ('templates','static/css','static/js','data'):
            (self.root/folder).mkdir(parents=True,exist_ok=True)
        (self.root/'app.py').write_text('APP = "must not change"\n')
        (self.root/'data/notes.db').write_bytes(b'secret-note-data-123')
        if OLD_TEMPLATE.exists():
            html=OLD_TEMPLATE.read_text()
            import re
            html=re.sub(r'<link\s+rel="stylesheet"\s+href="\{\{ url_for\(\'static\', filename=\'css/[^\']+\.css\'\) \}\}">',
                lambda m:'<link rel="stylesheet" href="{{ url_for(\'static\', filename=\'css/app.css\') }}">' if 'style.css' in m.group() else '',html)
            html=re.sub(r'<script src="\{\{ url_for\(\'static\', filename=\'js/[^\']+\.js\'\) \}\}"></script>',
                lambda m:'<script src="{{ url_for(\'static\', filename=\'js/app.js\') }}" defer></script>\n<script src="{{ url_for(\'static\', filename=\'js/autosave.js\') }}" defer></script>' if 'date-jst' in m.group() else '', html)
        else:
            html='''<!doctype html><html><head><meta name="viewport" content="width=device-width, initial-scale=1">
            <link rel="stylesheet" href="{{ url_for('static', filename='css/app.css') }}"></head><body>
            <header><button id="create-note-open">+</button></header>
            <script src="{{ url_for('static', filename='js/app.js') }}" defer></script></body></html>'''
        (self.root/'templates/index.html').write_text(html)
        (self.root/'static/css/app.css').write_text(OLD_STYLE.read_text() if OLD_STYLE.exists() else 'body {color:black;}')
        (self.root/'static/js/app.js').write_text((LOCAL_PREVIOUS/'static/js/app.js').read_text() if (LOCAL_PREVIOUS/'static/js/app.js').exists() else '(()=>{})();')
        (self.root/'static/js/autosave.js').write_text('''function initAutosave() {
    const status = { dataset: {} };
    function setStatus(state, message) {
        status.dataset.state = state;
        status.textContent = message;
    }
    const SAVE_DELAY=1000;
    let saveTimer=null, savedVersion=0, editVersion=0;
    function scheduleSave(wait = SAVE_DELAY) {
        clearTimeout(saveTimer);
        saveTimer=setTimeout(()=>{},wait);
    }
    // 未保存の変更があれば離脱前に警告
}
''')

    def tearDown(self):
        self.temp.cleanup()

    def test_apply_and_archive_without_user_data(self):
        before = (self.root/'app.py').read_bytes()
        changed=module.prepare(self.root)
        for file,content in changed.items():file.write_text(content,encoding='utf-8')
        output=module.make_full_zip(self.root)
        html=(self.root/'templates/index.html').read_text()
        self.assertLess(html.index('UNP_SETTINGS_BOOTSTRAP_BEGIN'),html.index("filename='css/app.css'"))
        self.assertIn('id="create-note-open"',html)
        self.assertIn('id="unp-settings-dialog"',html)
        self.assertIn('UNP_SETTINGS_MODULE_BEGIN',(self.root/'static/js/app.js').read_text())
        self.assertIn('UNP_SETTINGS_AUTOSAVE_HOOK',(self.root/'static/js/autosave.js').read_text())
        self.assertIn('UNP_SETTINGS_CSS_BEGIN',(self.root/'static/css/app.css').read_text())
        self.assertEqual((self.root/'data/notes.db').read_bytes(),b'secret-note-data-123')
        self.assertEqual((self.root/'app.py').read_bytes(),before)
        with zipfile.ZipFile(output) as z:
            names=z.namelist()
            self.assertNotIn('data/notes.db',names)
            for name in ('app.py','static/css/app.css','static/js/app.js','static/js/autosave.js','templates/index.html'):
                self.assertIn(name,names)
        with self.assertRaises(ValueError):module.prepare(self.root)

    def test_cli_dry_run_does_not_change_source(self):
        before=(self.root/'templates/index.html').read_bytes()
        run=subprocess.run(['python3',str(SOURCE/'install_settings.py'),'--repo',str(self.root),'--dry-run'],capture_output=True,text=True)
        self.assertEqual(run.returncode,0,run.stderr)
        self.assertEqual(before,(self.root/'templates/index.html').read_bytes())
        self.assertFalse((self.root/'UltimateNotePad-settings-complete.zip').exists())

if __name__=='__main__':
    unittest.main(verbosity=2)
