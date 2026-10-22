from pathlib import Path
import sys
import unittest
from unittest.mock import patch

PROJECT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(PROJECT / 'app'), str(PROJECT / 'build/common')]
from schemas import Settings
import stt_device
import tts_device
import importlib.util
_spec = importlib.util.spec_from_file_location('mac_builder', PROJECT / 'build/mac/build.py')
_builder = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_builder)
wheel_for = _builder.wheel_for


class MacPolicyTests(unittest.TestCase):
    def test_mac_normalizes_old_gpu_preferences(self):
        with patch.object(sys, 'platform', 'darwin'):
            settings = Settings(stt_device='cuda', tts_device='auto')
            self.assertEqual((settings.stt_device, settings.tts_device), ('cpu', 'cpu'))
            self.assertFalse(stt_device.availability()[0])
            self.assertFalse(tts_device.availability()[0])

    def test_windows_keeps_device_preferences(self):
        with patch.object(sys, 'platform', 'win32'):
            settings = Settings(stt_device='cuda', tts_device='auto')
            self.assertEqual((settings.stt_device, settings.tts_device), ('cuda', 'auto'))

    def test_wheel_selection_never_uses_wrong_architecture(self):
        entries = [{'filename': f'sample-1.0-cp312-cp312-macosx_14_0_{arch}.whl',
                    'url': arch, 'size': 1, 'digests': {'sha256': arch}} for arch in ('arm64', 'x86_64')]
        data = {'info': {'name': 'sample'}, 'urls': entries}
        for arch in ('arm64', 'x86_64'):
            self.assertEqual(wheel_for(data, arch)['url'], arch)
        data['urls'] = [entries[0]]
        with self.assertRaises(RuntimeError):
            wheel_for(data, 'x86_64')


if __name__ == '__main__':
    unittest.main()
