"""Build the browser guide from the single README source. Build-time only."""
from pathlib import Path
import re
import mistune

ROOT = Path(__file__).resolve().parents[2]


class Renderer(mistune.HTMLRenderer):
    def heading(self, text, level, **attrs):
        anchor = re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-')
        return f'<h{level} id="{anchor}">{text}</h{level}>\n'


def render():
    markdown = mistune.create_markdown(renderer=Renderer(escape=True), plugins=['table'])
    content = markdown((ROOT / 'README.md').read_text(encoding='utf-8'))
    content = content.replace('href="app/assets/', 'href="assets/')
    (ROOT / 'README.html').write_text('''<!doctype html><html lang="en"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>VH Embodiment Server — User guide</title>
<style>body{max-width:900px;margin:48px auto;padding:0 24px;font:16px/1.65 system-ui;color:#233446;background:#f6f8fa}h1,h2,h3{line-height:1.3}h2{margin-top:48px}a{color:#006c90}pre{padding:18px;background:#142334;color:#e9f5ff;border-radius:12px;overflow:auto}code{font-size:.9em}table{border-collapse:collapse;width:100%;font-size:14px}td,th{padding:10px;border-bottom:1px solid #ccd5df;text-align:left}img{max-width:100%;border-radius:12px}</style>
<main>''' + content + '</main></html>', encoding='utf-8')


if __name__ == '__main__':
    render()
