from pathlib import Path
import sys
import unittest

PROJECT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(PROJECT / 'app'), str(PROJECT / 'build/common')]
import server
from fastapi.testclient import TestClient


class ModelDocsTests(unittest.TestCase):
    def test_only_public_model_contract_is_in_document(self):
        with TestClient(server.app) as client:
            schema = client.get('/model-openapi.json').json()
            self.assertEqual(set(schema['paths']), server.MODEL_API_PATHS)
            self.assertNotIn('Settings', schema['components']['schemas'])
            self.assertIn('SpeakRequest', schema['components']['schemas'])
            definitions = schema['components']['schemas']
            self.assertNotIn('description', definitions['SpeakRequest']['properties']['gesture'])
            self.assertIn('\U0001f609', definitions['SpeakRequest']['properties']['expression']['anyOf'][0]['enum'])
            self.assertIn('handup', definitions['SpeakRequest']['properties']['gesture']['anyOf'][0]['enum'])
            self.assertEqual(client.get('/model-api').status_code, 404)
            self.assertEqual(client.get('/model-api.md').status_code, 404)
            self.assertEqual(client.get('/readme').status_code, 404)
            self.assertIn('expressions', client.get('/api/catalog').json())


if __name__ == '__main__':
    unittest.main()
