"""Photo in Word — размещение фотографий в Word-документе."""

import logging
import math
import sys
from pathlib import Path

# Добавляем src в путь для запуска как скрипт
sys.path.insert(0, str(Path(__file__).parent))

from src.config import (
    DocumentConfig,
    create_config,
    validate_folder,
    validate_photos_per_page,
    validate_margin_cm,
    validate_group_by_orientation,
    DEFAULT_MARGIN_CM,
    PHOTOS_PER_PAGE_MIN,
    PHOTOS_PER_PAGE_MAX,
)
from src.image_loader import load_images_from_folder, group_images_by_orientation
from src.document_builder import PhotoDocumentBuilder

logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
)
logger = logging.getLogger(__name__)


def get_user_input() -> DocumentConfig | None:
    """Запрашивает ввод у пользователя и возвращает конфигурацию."""
    print("=" * 50)
    print("  Photo in Word — размещение фотографий в документе")
    print("=" * 50)

    # 1. Путь к папке с фотографиями
    while True:
        folder_input = input("\nВведите путь к папке с фотографиями: ").strip()
        if not folder_input:
            print("Путь не может быть пустым.")
            continue
        is_valid, msg = validate_folder(folder_input)
        if is_valid:
            folder_path = Path(folder_input).resolve()
            break
        print(f"Ошибка: {msg}")

    # 2. Количество фото на страницу
    while True:
        default_photos = 4
        prompt = f"\nКоличество фото на страницу ({PHOTOS_PER_PAGE_MIN}-{PHOTOS_PER_PAGE_MAX}) [по умолчанию {default_photos}]: "
        photos_input = input(prompt).strip() or str(default_photos)
        is_valid, value, msg = validate_photos_per_page(photos_input)
        if is_valid and value is not None:
            photos_per_page = value
            break
        print(f"Ошибка: {msg}")

    # 3. Размер отступов между фото
    while True:
        prompt = f"\nОтступы между фото в см (по умолчанию {DEFAULT_MARGIN_CM}) [Enter для значения по умолчанию]: "
        margin_input = input(prompt).strip()
        is_valid, value, msg = validate_margin_cm(margin_input)
        if is_valid and value is not None:
            margin_cm = value
            break
        print(f"Ошибка: {msg}")

    # 4. Группировка по ориентации
    while True:
        prompt = "\nГруппировать фото по ориентации (вертикальные и горизонтальные на разных страницах)? [y/n] [по умолчанию n]: "
        group_input = input(prompt).strip() or "n"
        is_valid, group_by_orientation = validate_group_by_orientation(group_input)
        if is_valid:
            break
        print("Введите y или n")

    return create_config(
        folder_path=folder_path,
        photos_per_page=photos_per_page,
        margin_cm=margin_cm,
        group_by_orientation=group_by_orientation,
    )


def main() -> int:
    """Основная функция."""
    try:
        config = get_user_input()
        if config is None:
            return 1

        print("\nЗагрузка фотографий...")
        images = load_images_from_folder(config.folder_path)

        if not images:
            print("Ошибка: в указанной папке нет поддерживаемых изображений.")
            print("Поддерживаемые форматы: JPG, PNG, GIF, BMP, TIFF, WebP, HEIC (iPhone)")
            return 1

        print(f"Найдено фотографий: {len(images)}")

        builder = PhotoDocumentBuilder(config)
        photos_per_page = config.photos_per_page

        if config.group_by_orientation:
            portrait_paths, landscape_paths = group_images_by_orientation(images)
            grouped_pages = math.ceil(len(portrait_paths) / photos_per_page) + math.ceil(
                len(landscape_paths) / photos_per_page
            )
            ungrouped_pages = math.ceil(len(images) / photos_per_page)
            if grouped_pages > ungrouped_pages:
                for i in range(0, len(images), photos_per_page):
                    chunk = images[i : i + photos_per_page]
                    builder.add_page_with_photos(chunk)
            else:
                for group in (portrait_paths, landscape_paths):
                    for i in range(0, len(group), photos_per_page):
                        chunk = group[i : i + photos_per_page]
                        builder.add_page_with_photos(chunk)
        else:
            for i in range(0, len(images), photos_per_page):
                chunk = images[i : i + photos_per_page]
                builder.add_page_with_photos(chunk)

        output_path = config.output_file_path
        builder.save(output_path)

        print(f"\nГотово! Документ сохранён: {output_path}")
        return 0

    except KeyboardInterrupt:
        print("\n\nПрервано пользователем.")
        return 130
    except Exception as e:
        logger.exception("Критическая ошибка")
        print(f"\nОшибка: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
