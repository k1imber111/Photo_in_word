"""Конфигурация и валидация ввода для PhotoReportGenerator."""

from datetime import datetime
from pathlib import Path
from dataclasses import dataclass

OUTPUT_FILENAME_TEMPLATE = "PhotoReport_YYYY-MM-DD_HH-MM.docx"
DEFAULT_MARGIN_CM = 0.5
MARGIN_MIN_CM = 0.1
MARGIN_MAX_CM = 5.0
PHOTOS_PER_PAGE_MIN = 1
PHOTOS_PER_PAGE_MAX = 12


def generate_output_filename() -> str:
    """Генерирует имя файла по шаблону PhotoReport_YYYY-MM-DD_HH-MM.docx."""
    return datetime.now().strftime("PhotoReport_%Y-%m-%d_%H-%M.docx")


@dataclass
class DocumentConfig:
    """Конфигурация документа."""

    folder_path: Path
    photos_per_page: int
    margin_cm: float
    output_path: Path  # каталог для сохранения или полный путь к файлу
    group_by_orientation: bool = True  # по ТЗ: строгое разделение по ориентации

    @property
    def output_file_path(self) -> Path:
        """Полный путь к выходному файлу. Если output_path — каталог, имя генерируется по шаблону."""
        p = Path(self.output_path)
        if p.suffix.lower() == ".docx" and p.name:
            return p.resolve()
        base = p.resolve() if p.is_dir() else p
        return base / generate_output_filename()


def validate_folder(path: str | Path) -> tuple[bool, str]:
    """
    Проверяет, что путь существует и является директорией.

    Returns:
        (is_valid, error_message). При ошибке — «Папка не найдена» (критерий приёмки ТЗ).
    """
    try:
        p = Path(path).resolve()
        if not p.exists() or not p.is_dir():
            return False, "Папка не найдена"
        return True, ""
    except Exception:
        return False, "Папка не найдена"


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


def create_config(
    folder_path: Path,
    photos_per_page: int,
    margin_cm: float = DEFAULT_MARGIN_CM,
    output_path: Path | None = None,
) -> DocumentConfig:
    """
    Создаёт конфигурацию документа.
    output_path: каталог для сохранения или полный путь к .docx; если None — сохраняем в папке с фото.
    """
    folder_path = Path(folder_path).resolve()
    out = Path(output_path).resolve() if output_path is not None else folder_path
    return DocumentConfig(
        folder_path=folder_path,
        photos_per_page=photos_per_page,
        margin_cm=margin_cm,
        output_path=out,
        group_by_orientation=True,
    )
