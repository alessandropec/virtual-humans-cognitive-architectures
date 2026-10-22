"""Keep console output available in the browser log panels."""
import sys


def capture(path):
    output = path.open('a', encoding='utf-8', buffering=1)
    class Tee:
        def __init__(self, console): self.console = console
        def write(self, text):
            self.console.write(text);output.write(text);return len(text)
        def flush(self): self.console.flush();output.flush()
        def __getattr__(self, name): return getattr(self.console, name)
    sys.stdout = Tee(sys.stdout)
    sys.stderr = Tee(sys.stderr)


def tail(path):
    if not path.is_file(): return 'No output yet.'
    with path.open('rb') as source:
        source.seek(0, 2)
        source.seek(max(0, source.tell()-48000))
        return source.read().decode('utf-8', errors='replace')
