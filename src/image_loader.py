"""Загрузка и валидация изображений из папки."""

import logging
from pathlib import Path

from PIL import Image

SUPPORTED_EXTENSIONS = (
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".bmp",
    ".tiff",
    ".tif",
    ".webp",
    ".heic",
    ".heif",
)

# Регистрация pillow-heif для поддержки HEIC (iPhone)
try:
    import pillow_heif

    pillow_heif.register_heif_opener()
    HEIC_SUPPORTED = True
except ImportError:
    HEIC_SUPPORTED = False

logger = logging.getLogger(__name__)


def _natural_sort_key(path: Path) -> tuple:
    """Ключ для естественной сортировки (IMG_1, IMG_2, IMG_10)."""
    import re

    parts = re.split(r"(\d+)", path.name.lower())
    return tuple(int(p) if p.isdigit() else p for p in parts)


def load_images_from_folder(folder_path: str | Path) -> list[Path]:
    """
    Загружает список путей к изображениям из папки.

    Returns:
        Отсортированный список путей к поддерживаемым изображениям.
    """
    folder = Path(folder_path).resolve()
    if not folder.is_dir():
        return []

    result: list[Path] = []
    for file_path in folder.iterdir():
        if not file_path.is_file():
            continue

        ext = file_path.suffix.lower()
        if ext not in SUPPORTED_EXTENSIONS:
            continue

        if ext in (".heic", ".heif") and not HEIC_SUPPORTED:
            logger.warning("Пропуск %s: для HEIC установите pillow-heif", file_path.name)
            continue

        if _is_valid_image(file_path):
            result.append(file_path)
        else:
            logger.warning("Пропуск повреждённого файла: %s", file_path.name)

    result.sort(key=_natural_sort_key)
    return result


def _is_valid_image(path: Path) -> bool:
    """Проверяет, можно ли открыть изображение."""
    try:
        with Image.open(path) as img:
            _ = img.size  # Загрузка для проверки
        return True
    except Exception as e:
        logger.debug("Ошибка при проверке %s: %s", path.name, e)
        return False


def group_images_by_orientation(paths: list[Path]) -> tuple[list[Path], list[Path]]:
    """
    Группирует фото по ориентации (ТЗ): книжная (portrait) — высота ≥ ширины;
    альбомная (landscape) — ширина > высоты. Квадрат считается portrait.

    Returns:
        (portrait_paths, landscape_paths)
    """
    portrait: list[Path] = []
    landscape: list[Path] = []

    for path in paths:
        dims = get_image_dimensions(path)
        if dims:
            w, h = dims
            if h >= w:
                portrait.append(path)
            else:
                landscape.append(path)
        else:
            landscape.append(path)  # при ошибке — в landscape

    return (portrait, landscape)


def get_image_dimensions(path: Path) -> tuple[int, int] | None:
    """
    Возвращает размеры изображения (width, height).

    Returns:
        (width, height) или None при ошибке.
    """
    try:
        with Image.open(path) as img:
            return img.size
    except Exception as e:
        logger.warning("Не удалось получить размеры %s: %s", path.name, e)
        return None
