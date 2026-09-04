from pathlib import Path
from PIL import Image

OUTPUT_DIR = Path("media/outputs")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def resize(source_path, target_width, target_height):
    img = Image.open(source_path)
    resized = img.resize((target_width, target_height))
    output_path = OUTPUT_DIR / Path(source_path).name
    resized.save(output_path)
    return str(output_path)

def thumbnail(source_path, target_width,  target_height):
    img = Image.open(source_path)
    width = target_width or 10_000_000
    height = target_height or 10_000_000
    img.thumbnail((width, height))
    output_path = OUTPUT_DIR / Path(source_path).name
    img.save(output_path)
    return str(output_path)

def convert(source_path, target_format):
    img = Image.open(source_path)
    if target_format == "jpeg" and img.mode in ("RGBA", "P", "LA"):
        img = img.convert("RGB")
    output_path = OUTPUT_DIR / f"{Path(source_path).stem}.{target_format}"
    img.save(output_path)
    return str(output_path)