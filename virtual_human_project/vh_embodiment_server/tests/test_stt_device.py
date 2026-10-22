"""Exercise lazy CUDA failures, explicit GPU policy, and CPU-only selection."""
from pathlib import Path
import sys
from types import SimpleNamespace
from unittest.mock import Mock, patch
import unittest

PROJECT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(PROJECT / 'app'), str(PROJECT / 'build/common')]
import speech
import stt_device
from schemas import Settings


class DevicePolicyTests(unittest.TestCase):
    def setUp(self):
        stt_device.gpu_failures.clear()
        self.cpu = Mock()
        self.cpu.transcribe.return_value = ([SimpleNamespace(text='Ciao')], SimpleNamespace(language='it'))
        self.gpu = Mock()
        def delayed_failure():
            yield from ()
            raise RuntimeError('CUDA out of memory')
        self.gpu.transcribe.side_effect = lambda *args, **kwargs: (delayed_failure(), None)

    def test_auto_retries_lazy_failure_and_remembers_it(self):
        with patch.object(stt_device, 'availability', return_value=(True, None)), \
             patch.object(speech, 'release_whisper'), \
             patch.object(speech, 'load_whisper', side_effect=lambda path, device: self.gpu if device == 'cuda' else self.cpu) as load:
            stats = {}
            text, _ = speech.recognize([], 'model', Settings(stt_device='auto'), {}, stats)
            self.assertEqual(text, 'Ciao')
            self.assertEqual(stats['device'], 'cpu')
            self.assertIn('memory', stats['fallback_reason'])
            self.assertEqual([call.args[1] for call in load.call_args_list], ['cuda','cpu'])
            load.reset_mock()
            speech.recognize([], 'model', Settings(stt_device='auto'), {}, {})
            load.assert_called_once_with('model','cpu')

    def test_explicit_gpu_never_silently_falls_back(self):
        with patch.object(stt_device, 'availability', return_value=(True,None)), \
             patch.object(speech, 'release_whisper'), \
             patch.object(speech, 'load_whisper', return_value=self.gpu) as load:
            with self.assertRaises(speech.SpeechDeviceError):
                speech.recognize([], 'model', Settings(stt_device='cuda'), {}, {})
            load.assert_called_once_with('model','cuda')

    def test_cpu_does_not_probe_or_use_gpu(self):
        with patch.object(stt_device, 'availability') as availability, \
             patch.object(speech, 'load_whisper', return_value=self.cpu) as load:
            speech.recognize([], 'model', Settings(stt_device='cpu'), {}, {})
            availability.assert_not_called()
            load.assert_called_once_with('model','cpu')

    def test_no_gpu_auto_and_forced(self):
        with patch.object(stt_device,'availability',return_value=(False,'No NVIDIA GPU')):
            self.assertEqual(stt_device.choose('model','auto'), ('cpu','No NVIDIA GPU'))
            with self.assertRaises(speech.SpeechDeviceError):
                stt_device.choose('model','cuda')


if __name__ == '__main__':
    unittest.main()
