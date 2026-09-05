import pytest
from PIL import Image

from processing import image_ops


def test_resize_produces_exact_dimensions(tmp_path, sample_image_bytes):
    src = tmp_path / "in.png"
    src.write_bytes(sample_image_bytes(size=(1200, 800)).read())

    out = image_ops.resize(str(src), 400, 300)

    assert Image.open(out).size == (400, 300)


def test_thumbnail_with_only_width_preserves_aspect_ratio(tmp_path, sample_image_bytes):
    src = tmp_path / "in.png"
    src.write_bytes(sample_image_bytes(size=(1200, 800)).read())

    out = image_ops.thumbnail(str(src), 300, None)

    assert Image.open(out).size == (300, 200)


def test_thumbnail_with_only_height_preserves_aspect_ratio(tmp_path, sample_image_bytes):
    src = tmp_path / "in.png"
    src.write_bytes(sample_image_bytes(size=(1200, 800)).read())

    out = image_ops.thumbnail(str(src), None, 100)

    assert Image.open(out).size == (150, 100)


def test_convert_flattens_alpha_before_saving_as_jpeg(tmp_path, sample_image_bytes):
    src = tmp_path / "in.png"
    src.write_bytes(sample_image_bytes(mode="RGBA", color=(255, 0, 0, 128)).read())

    out = image_ops.convert(str(src), "jpeg")
    result = Image.open(out)

    assert result.mode == "RGB"
    assert out.endswith(".jpeg")


def test_convert_to_webp(tmp_path, sample_image_bytes):
    src = tmp_path / "in.png"
    src.write_bytes(sample_image_bytes().read())

    out = image_ops.convert(str(src), "webp")

    assert Image.open(out).format == "WEBP"


def test_resize_on_missing_file_raises(tmp_path):
    missing = tmp_path / "does_not_exist.png"

    with pytest.raises(FileNotFoundError):
        image_ops.resize(str(missing), 100, 100)


def test_resize_on_corrupt_file_raises(tmp_path):
    bad = tmp_path / "corrupt.png"
    bad.write_bytes(b"this is not a real image")

    with pytest.raises(Exception):
        image_ops.resize(str(bad), 100, 100)
