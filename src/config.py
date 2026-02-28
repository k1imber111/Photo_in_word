"""Конфигурация и валидация ввода для Photo in Word."""

from pathlib import Path
from dataclasses import dataclass

DEFAULT_OUTPUT_FILENAME = "photos.docx"
DEFAULT_MARGIN_CM = 0.5
MARGIN_MIN_CM = 0.1
MARGIN_MAX_CM = 5.0
PHOTOS_PER_PAGE_MIN = 1
PHOTOS_PER_PAGE_MAX = 12


@dataclass
class DocumentConfig:
    """Конфигурация документа."""

    folder_path: Path
    photos_per_page: int
    margin_cm: float
    output_path: Path
    output_filename: str = DEFAULT_OUTPUT_FILENAME
    group_by_orientation: bool = False

    @property
    def output_file_path(self) -> Path:
        """Полный путь к выходному файлу."""
        return self.output_path / self.output_filename


def validate_folder(path: str | Path) -> tuple[bool, str]:
    """
    Проверяет, что путь существует и является директорией.

    Returns:
        (is_valid, error_message)
    """
    try:
        p = Path(path).resolve()
        if not p.exists():
            return False, f"Путь не существует: {p}"
        if not p.is_dir():
            return False, f"Путь не является папкой: {p}"
        return True, ""
    except Exception as e:
        return False, f"Ошибка при проверке пути: {e}"


def validate_photos_per_page(value: str | int) -> tuple[bool, int | None, str]:
    """
    Проверяет количество фото на страницу.

    Returns:
        (is_valid, value_or_none, error_message)
    """
    try:
        n = int(value)
        if PHOTOS_PER_PAGE_MIN <= n <= PHOTOS_PER_PAGE_MAX:
            return True, n, ""
        return False, None, f"Введите число от {PHOTOS_PER_PAGE_MIN} до {PHOTOS_PER_PAGE_MAX}"
    except (ValueError, TypeError):
        return False, None, "Введите целое число"


def validate_margin_cm(value: str | float) -> tuple[bool, float | None, str]:
    """
    Проверяет размер отступа в см.

    Returns:
        (is_valid, value_or_none, error_message)
    """
    if value is None or (isinstance(value, str) and value.strip() == ""):
        return True, DEFAULT_MARGIN_CM, ""

    try:
        v = float(value.replace(",", "."))
        if MARGIN_MIN_CM <= v <= MARGIN_MAX_CM:
            return True, v, ""
        return False, None, f"Введите число от {MARGIN_MIN_CM} до {MARGIN_MAX_CM} см"
    except (ValueError, TypeError):
        return False, None, "Введите число (например, 0.5)"


def validate_group_by_orientation(value: str) -> tuple[bool, bool]:
    """
    Проверяет ввод для группировки по ориентации.

    Returns:
        (is_valid, value)
    """
    v = value.strip().lower()
    if v in ("", "n", "no", "н", "нет"):
        return True, False
    if v in ("y", "yes", "д", "да"):
        return True, True
    return False, False


def create_config(
    folder_path: Path,
    photos_per_page: int,
    margin_cm: float = DEFAULT_MARGIN_CM,
    group_by_orientation: bool = False,
) -> DocumentConfig:
    """Создаёт конфигурацию документа."""
    folder_path = Path(folder_path).resolve()
    return DocumentConfig(
        folder_path=folder_path,
        photos_per_page=photos_per_page,
        margin_cm=margin_cm,
        output_path=folder_path,
        output_filename=DEFAULT_OUTPUT_FILENAME,
        group_by_orientation=group_by_orientation,
    )
