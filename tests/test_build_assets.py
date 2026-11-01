"""Packaging checks use temporary source trees, with no Git or device access."""
import json
from pathlib import Path
import tempfile
import unittest
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from build_assets import declared_assets, stage_assets
from build import ABIS, selected_libraries

ROOT = Path(__file__).resolve().parents[1]

class Assets(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)/'source'
        self.out = Path(self.tmp.name)/'package'
        for name in declared_assets(ROOT):
            path = self.root/'assets'/name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes((ROOT/'assets'/name).read_bytes() if name in ('index.html', 'provenance.json') else b'fixture')
        (self.root/'deps').mkdir()
        (self.root/'deps/checksums.json').write_bytes((ROOT/'deps/checksums.json').read_bytes())

    def test_source_archive_and_notices(self):
        stage_assets(self.root, self.out)
        expected = declared_assets(self.root)
        self.assertEqual({p.relative_to(self.out).as_posix() for p in self.out.rglob('*') if p.is_file()}, expected)
        for name in expected:
            self.assertEqual((self.root/'assets'/name).read_bytes(), (self.out/name).read_bytes())
        self.assertFalse((self.root/'.git').exists())
        self.assertIn('licenses/THIRD_PARTY.md', expected)
        self.assertIn('models/ONNXRuntime-ThirdPartyNotices.txt', expected)
        self.assertIn('models/u2netp.onnx', expected)

    def test_private_file_rejected_before_staging(self):
        self.out.mkdir(); (self.out/'previous').write_text('safe')
        (self.root/'assets/private.json').write_text('private fixture')
        with self.assertRaisesRegex(ValueError, 'unexpected: private.json'):
            stage_assets(self.root, self.out)
        self.assertEqual((self.out/'previous').read_text(), 'safe')
        self.assertFalse((self.out/'private.json').exists())

    def test_missing_asset_rejected(self):
        (self.root/'assets/app.js').unlink()
        with self.assertRaisesRegex(ValueError, 'missing: app.js'):
            stage_assets(self.root, self.out)

    def test_symlink_file_and_directory_rejected(self):
        source = self.root/'assets/sample.svg'
        source.unlink(); source.symlink_to(self.root/'assets/index.html')
        with self.assertRaisesRegex(ValueError, 'Symlink'):
            stage_assets(self.root, self.out)
        source.unlink(); source.write_text('fixture')
        (self.root/'assets/private-dir').symlink_to(self.root/'deps', target_is_directory=True)
        with self.assertRaisesRegex(ValueError, 'Symlink'):
            stage_assets(self.root, self.out)

    def test_new_entry_script_included(self):
        entry = self.root/'assets/index.html'
        entry.write_text(entry.read_text()+"<script src='new-template.js'></script>")
        (self.root/'assets/new-template.js').write_text('fixture')
        stage_assets(self.root, self.out)
        self.assertEqual((self.out/'new-template.js').read_text(), 'fixture')

    def test_paths_cannot_escape(self):
        entry = self.root/'assets/index.html'
        original = entry.read_text()
        for value in ('../private.json', '/private.json', 'https://example.test/x.js'):
            entry.write_text(original+f'<script src="{value}"></script>')
            with self.assertRaisesRegex(ValueError, 'Invalid asset path'):
                stage_assets(self.root, self.out)
        entry.write_text(original)
        for out in (self.root, self.root/'assets', self.root/'assets/stage', self.root.parent):
            with self.assertRaisesRegex(ValueError, 'Invalid asset staging'):
                stage_assets(self.root, out)

    def test_manifest_path_cannot_escape(self):
        path = self.root/'assets/provenance.json'
        path.write_text(json.dumps([{'path':'assets/../private.json'}]))
        with self.assertRaises(ValueError):stage_assets(self.root, self.out)

    def test_previous_staging_is_replaced(self):
        self.out.mkdir(); (self.out/'old-secret.txt').write_text('fixture')
        stage_assets(self.root, self.out)
        self.assertFalse((self.out/'old-secret.txt').exists())

class Runtime(unittest.TestCase):
    def test_default_and_device_architectures(self):
        names = [f'jni/{abi}/{lib}.so' for abi in ABIS for lib in ('libonnxruntime', 'libonnxruntime4j_jni')]
        names += ['classes.jar', 'jni/arm64-v8a/../private.so']
        self.assertEqual(len(selected_libraries(names)), 8)
        self.assertEqual(selected_libraries(names, 'arm64-v8a'), ['jni/arm64-v8a/libonnxruntime.so', 'jni/arm64-v8a/libonnxruntime4j_jni.so'])
        with self.assertRaises(RuntimeError):selected_libraries(['classes.jar'], 'arm64-v8a')

if __name__ == '__main__':unittest.main()
