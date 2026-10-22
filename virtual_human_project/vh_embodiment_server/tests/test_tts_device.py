from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

PROJECT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(PROJECT / 'app'), str(PROJECT / 'build/common')]
import tts_device
from schemas import Settings


class VoiceDeviceTests(unittest.TestCase):
    def setUp(self):
        tts_device.reset()
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.target = Path(self.temp.name) / 'voice.wav'
        self.cpu = Mock()
        self.cpu.synthesize_wav.side_effect = lambda text, output: (output.setnchannels(1), output.setsampwidth(2), output.setframerate(16000), output.writeframes(b'\0\0' * 100))
        self.gpu = Mock()
        self.gpu.synthesize_wav.side_effect = RuntimeError('CUDA out of memory')

    def test_auto_retries_cpu_and_remembers_failure(self):
        with patch.object(tts_device, 'availability', return_value=(True, None)), patch.object(tts_device, 'load_voice') as load:
            load.side_effect = lambda path, device: self.gpu if device == 'cuda' else self.cpu
            stats = tts_device.synthesize('test', 'model', self.target, Settings(tts_device='auto'))
            self.assertEqual(stats['device'], 'cpu')
            self.assertIn('memory', stats['fallback_reason'])
            self.assertGreater(self.target.stat().st_size, 44)
            load.reset_mock()
            tts_device.synthesize('test', 'model', self.target, Settings(tts_device='auto'))
            load.assert_called_once_with('model', 'cpu')

    def test_forced_gpu_errors_without_fallback(self):
        with patch.object(tts_device, 'availability', return_value=(True, None)), patch.object(tts_device, 'load_voice', return_value=self.gpu):
            with self.assertRaises(tts_device.SpeechDeviceError):
                tts_device.synthesize('test', 'model', self.target, Settings(tts_device='cuda'))
        self.assertFalse(self.target.exists())

    def test_cpu_does_not_probe_cuda(self):
        with patch.object(tts_device, 'availability') as probe, patch.object(tts_device, 'load_voice', return_value=self.cpu):
            stats = tts_device.synthesize('test', 'model', self.target, Settings(tts_device='cpu'))
        probe.assert_not_called(); self.assertEqual(stats['device'], 'cpu')

    def test_gpu_runtime_missing_has_actionable_error(self):
        with patch.object(tts_device, 'availability', return_value=(False, 'Esegui Installa.cmd')):
            with self.assertRaisesRegex(tts_device.SpeechDeviceError, 'Installa.cmd'):
                tts_device.synthesize('test', 'model', self.target, Settings(tts_device='cuda'))


if __name__ == '__main__':
    unittest.main()
