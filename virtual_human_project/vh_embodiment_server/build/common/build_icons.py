"""Export the same geometric icon for the browser, Windows and macOS."""
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[2]
DEST = ROOT / 'app/assets/branding'


def build():
    DEST.mkdir(parents=True, exist_ok=True)
    navy, blue, cyan = '#122b45', '#76b8ee', '#65e0cf'
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512">
<rect width="512" height="512" rx="108" fill="{navy}"/>
<rect x="76" y="80" width="360" height="352" rx="36" fill="none" stroke="{blue}" stroke-width="14"/>
<path d="M80 170H432" stroke="{blue}" stroke-width="12"/>
<g fill="{cyan}"><circle cx="116" cy="126" r="9"/><circle cx="148" cy="126" r="9"/><circle cx="180" cy="126" r="9"/>
<path d="M160 400C160 305 352 305 352 400Z"/><circle cx="256" cy="254" r="60"/></g>
<g fill="{navy}"><circle cx="235" cy="246" r="7"/><circle cx="277" cy="246" r="7"/></g>
<path d="M235 270Q256 290 277 270" fill="none" stroke="{navy}" stroke-width="7" stroke-linecap="round"/>
</svg>'''
    (DEST / 'vh-icon.svg').write_text(svg, encoding='utf-8')
    # Draw at 4x resolution for smooth edges; geometry matches the SVG above.
    image = Image.new('RGBA', (2048, 2048))
    draw = ImageDraw.Draw(image)
    box = lambda *values: tuple(round(value * 4) for value in values)
    draw.rounded_rectangle(box(0, 0, 512, 512), radius=432, fill=navy)
    draw.rounded_rectangle(box(69, 73, 443, 439), radius=172, outline=blue, width=56)
    draw.line(box(80, 170, 432, 170), fill=blue, width=48)
    for x in (116, 148, 180):
        draw.ellipse(box(x-9, 117, x+9, 135), fill=cyan)
    def curve(points):
        result=[]
        for step in range(101):
            t=step/100; q=1-t
            x=q**3*points[0][0]+3*q*q*t*points[1][0]+3*q*t*t*points[2][0]+t**3*points[3][0]
            y=q**3*points[0][1]+3*q*q*t*points[1][1]+3*q*t*t*points[2][1]+t**3*points[3][1]
            result.append((round(x*4),round(y*4)))
        return result
    draw.polygon(curve([(160,400),(160,305),(352,305),(352,400)]), fill=cyan)
    draw.ellipse(box(196,194,316,314), fill=cyan)
    for x in (235,277):
        draw.ellipse(box(x-7,239,x+7,253), fill=navy)
    mouth=curve([(235,270),(249,283.3333),(263,283.3333),(277,270)])
    draw.line(mouth, fill=navy, width=28)
    for x,y in (mouth[0],mouth[-1]):
        draw.ellipse((x-14,y-14,x+14,y+14),fill=navy)
    icon=image.resize((1024,1024),Image.Resampling.LANCZOS)
    icon.resize((512,512),Image.Resampling.LANCZOS).save(DEST / 'vh-icon.png')
    icon.save(DEST / 'vh-icon.ico', sizes=[(n,n) for n in (16,24,32,48,64,128,256)])
    icon.save(DEST / 'vh-icon.icns')


if __name__ == '__main__':
    build()
