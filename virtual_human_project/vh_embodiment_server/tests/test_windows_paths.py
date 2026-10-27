"""Windows path length budget (259 characters without long path support), with no installation."""
from pathlib import Path
import re
import sys
import unittest

PROJECT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(PROJECT / 'build/common')]
from files import application_files

MAX_PATH = 259
SETUP = (PROJECT / 'build/win/src/Setup.cs').read_text(encoding='utf-8')
DEEPEST_ENVIRONMENT = int(re.search(r'DeepestEnvironmentPath=(\d+);', SETUP).group(1))
# The GitHub ZIP extracted with Windows into Downloads nests the repository folder twice.
DOWNLOADED = ('C:\\Users\\alex\\Downloads\\virtual-humans-cognitive-architectures-main'
              '\\virtual-humans-cognitive-architectures-main\\virtual_human_project\\')


class WindowsPathTests(unittest.TestCase):
    def test_application_files_fit_in_a_downloaded_repository(self):
        prefix = DOWNLOADED + 'installation\\'
        too_long = [name for _, name in application_files('win') if len(prefix + name + '.setup-new') > MAX_PATH]
        self.assertEqual(too_long, [])

    def test_installed_environment_fits_the_setup_budget(self):
        environment = PROJECT.parent / '.venv-vh-course'
        if not environment.is_dir():
            self.skipTest('No installed course environment to measure.')
        deepest = max(len(path.relative_to(PROJECT.parent).as_posix()) for path in environment.rglob('*'))
        self.assertLessEqual(deepest, DEEPEST_ENVIRONMENT)


if __name__ == '__main__':
    unittest.main()
