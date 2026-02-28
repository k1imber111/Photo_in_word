"""Вспомогательные функции для расчёта размеров и сетки."""

from pathlib import Path

from docx.oxml import OxmlElement
from docx.oxml.ns import qn


def _is_portrait_dominant(photo_paths: list[Path]) -> bool:
    """
    Возвращает True, если большинство фото вертикальные (portrait).
    Порог: height/width > 1.05 → portrait.
    """
    from .image_loader import get_image_dimensions

    if not photo_paths:
        return False
    portrait_count = 0
    for path in photo_paths:
        dims = get_image_dimensions(path)
        if dims:
            w, h = dims
            if w > 0 and h / w > 1.05:
                portrait_count += 1
    return portrait_count > len(photo_paths) / 2


def get_grid_dimensions(
    photos_per_page: int,
    photo_paths: list[Path] | None = None,
) -> tuple[int, int]:
    """
    Возвращает (rows, cols) для сетки фотографий на альбомной странице.

    Для альбомной страницы (ширина > высоты):
    - Portrait (вертикальные фото): больше столбцов (1×2, 2×2, 2×3)
    - Landscape (горизонтальные фото): больше рядов (2×1, 3×1, 3×2)
    """
    portrait = _is_portrait_dominant(photo_paths) if photo_paths else False

    if photos_per_page <= 0:
        return 1, 1
    if photos_per_page == 1:
        return 1, 1
    if photos_per_page == 2:
        return (2, 1) if not portrait else (1, 2)
    if photos_per_page == 3:
        return (3, 1) if not portrait else (1, 3)
    if photos_per_page == 4:
        return 2, 2
    if photos_per_page == 5:
        return 2, 3  # одна ячейка пустая
    if photos_per_page == 6:
        return (3, 2) if not portrait else (2, 3)
    if photos_per_page == 7:
        return (2, 4) if portrait else (4, 2)
    if photos_per_page == 8:
        return (2, 4) if portrait else (4, 2)
    if photos_per_page == 9:
        return 3, 3
    if photos_per_page == 10:
        return (2, 5) if portrait else (5, 2)
    if photos_per_page == 11:
        return (2, 6) if portrait else (6, 2)
    if photos_per_page >= 12:
        return (3, 4) if portrait else (4, 3)
    return 1, photos_per_page


def calculate_image_size(
    cell_width_cm: float,
    cell_height_cm: float,
    img_width: int,
    img_height: int,
) -> tuple[float, float]:
    """
    Вычисляет размер изображения в см с сохранением пропорций (fit inside).

    Returns:
        (width_cm, height_cm)
    """
    if img_width <= 0 or img_height <= 0:
        return cell_width_cm, cell_height_cm

    img_ratio = img_width / img_height
    cell_ratio = cell_width_cm / cell_height_cm

    if img_ratio > cell_ratio:
        # Изображение шире — ограничиваем по ширине
        width_cm = cell_width_cm
        height_cm = cell_width_cm / img_ratio
    else:
        # Изображение выше — ограничиваем по высоте
        height_cm = cell_height_cm
        width_cm = cell_height_cm * img_ratio

    return width_cm, height_cm


def cm_to_dxa(cm: float) -> int:
    """Конвертирует см в dxa (twentieths of a point, 1/1440 inch)."""
    # 1 cm = 1/2.54 inch, 1 inch = 1440 dxa
    return int(cm / 2.54 * 1440)


def set_cell_margins(cell, top: float = 0, start: float = 0, bottom: float = 0, end: float = 0):
    """
    Устанавливает отступы ячейки таблицы.

    Args:
        cell: ячейка python-docx
        top, start, bottom, end: отступы в см
    """
    tc = cell._tc
    tc_pr = tc.get_or_add_tcPr()
    tc_mar = OxmlElement("w:tcMar")

    for margin_name, value in [("top", top), ("start", start), ("bottom", bottom), ("end", end)]:
        if value > 0:
            node = OxmlElement(f"w:{margin_name}")
            node.set(qn("w:w"), str(cm_to_dxa(value)))
            node.set(qn("w:type"), "dxa")
            tc_mar.append(node)

    tc_pr.append(tc_mar)


def add_page_number_field(run, field_code: str = "PAGE"):
    """Добавляет поле (PAGE) в run для нумерации страниц."""
    fld_char1 = OxmlElement("w:fldChar")
    fld_char1.set(qn("w:fldCharType"), "begin")

    instr_text = OxmlElement("w:instrText")
    instr_text.set(qn("xml:space"), "preserve")
    instr_text.text = field_code

    fld_char2 = OxmlElement("w:fldChar")
    fld_char2.set(qn("w:fldCharType"), "separate")

    fld_char3 = OxmlElement("w:fldChar")
    fld_char3.set(qn("w:fldCharType"), "end")

    r_element = run._r
    r_element.append(fld_char1)
    r_element.append(instr_text)
    r_element.append(fld_char2)
    r_element.append(fld_char3)
