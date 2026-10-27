"""Render the repository-native routing mark. Requires Pillow for maintainers only."""
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[2] / "assist_ai_router"
SCALE = 4
image = Image.new("RGBA", (256 * SCALE, 256 * SCALE), (0, 0, 0, 0))
d = ImageDraw.Draw(image)
def point(x, y):
    return x * SCALE, y * SCALE
def line(points, color, width):
    d.line([point(x, y) for x, y in points], fill=color, width=width * SCALE, joint="curve")
def dot(x, y, color, radius=12):
    d.ellipse((*point(x-radius, y-radius), *point(x+radius, y+radius)), fill=color)
d.rounded_rectangle((0, 0, 1023, 1023), radius=60*SCALE, fill="#111f2d")
line([(59, 129), (112, 129), (151, 72), (194, 72)], "#62ddc2", 10)
line([(112, 129), (151, 184), (194, 184)], "#8faeff", 10)
line([(112, 129), (194, 129)], "#3c586d", 8)
for x, y, color in ((59,129,"#e8f4ff"),(194,72,"#62ddc2"),(194,129,"#3c586d"),(194,184,"#8faeff")):
    dot(x,y,color)
image.resize((256,256), Image.Resampling.LANCZOS).save(ROOT / "icon.png")
image.resize((512,512), Image.Resampling.LANCZOS).save(ROOT / "logo.png")
