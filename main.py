"""PhotoReportGenerator — консольное приложение для генерации фотоотчетов в MS Word."""

import argparse
import logging
import sys
from pathlib import Path

# Добавляем корень проекта в путь для запуска как скрипт
sys.path.insert(0, str(Path(__file__).parent))

from src.config import (
    DocumentConfig,
    create_config,
    validate_folder,
    validate_photos_per_page,
    validate_margin_cm,
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


def parse_args():
    """Разбор аргументов командной строки. При отсутствии path/count запускается интерактивный режим."""
    parser = argparse.ArgumentParser(
        description="Генерация фотоотчёта в формате .docx из папки с изображениями."
    )
    parser.add_argument(
        "--path", "-p",
        type=str,
        help="Путь к папке с фотографиями",
    )
    parser.add_argument(
        "--count", "-c",
        type=int,
        help="Количество фото на одной странице (целое > 0)",
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        default=None,
        help="Путь для сохранения: каталог или полный путь к файлу .docx (необязательно)",
    )
    return parser.parse_args()


def get_user_input() -> DocumentConfig | None:
    """Запрашивает ввод у пользователя и возвращает конфигурацию (интерактивный режим)."""
    print("=" * 50)
    print("  PhotoReportGenerator — фотоотчёт в Word")
    print("=" * 50)

    while True:
        folder_input = input("\nВведите путь к папке с фотографиями: ").strip()
        if not folder_input:
            print("Путь не может быть пустым.")
            continue
        is_valid, msg = validate_folder(folder_input)
        if is_valid:
            folder_path = Path(folder_input).resolve()
            break
        print(msg)

    while True:
        default_photos = 4
        prompt = f"\nКоличество фото на страницу ({PHOTOS_PER_PAGE_MIN}-{PHOTOS_PER_PAGE_MAX}) [по умолчанию {default_photos}]: "
        photos_input = input(prompt).strip() or str(default_photos)
        is_valid, value, msg = validate_photos_per_page(photos_input)
        if is_valid and value is not None:
            photos_per_page = value
            break
        print(f"Ошибка: {msg}")

    while True:
        prompt = f"\nОтступы между фото в см (по умолчанию {DEFAULT_MARGIN_CM}) [Enter — по умолчанию]: "
        margin_input = input(prompt).strip()
        is_valid, value, msg = validate_margin_cm(margin_input)
        if is_valid and value is not None:
            margin_cm = value
            break
        print(f"Ошибка: {msg}")

    return create_config(
        folder_path=folder_path,
        photos_per_page=photos_per_page,
        margin_cm=margin_cm,
        output_path=None,  # по умолчанию — в папку с фото
    )


def run_with_config(config: DocumentConfig) -> int:
    """Формирует документ по конфигурации. Возвращает код выхода."""
    print("\nЗагрузка фотографий...")
    images = load_images_from_folder(config.folder_path)

    if not images:
        print("Ошибка: в указанной папке нет поддерживаемых изображений.")
        print("Поддерживаемые форматы: JPG, PNG, GIF, BMP, TIFF, WebP, HEIC")
        return 1

    print(f"Найдено фотографий: {len(images)}")

    portrait_paths, landscape_paths = group_images_by_orientation(images)
    photos_per_page = config.photos_per_page
    builder = PhotoDocumentBuilder(config)

    # По ТЗ: строгое разделение — на одной странице только одна ориентация
    if landscape_paths:
        print("Обработка альбомных фото...")
        for i in range(0, len(landscape_paths), photos_per_page):
            chunk = landscape_paths[i : i + photos_per_page]
            builder.add_page_with_photos(chunk)
    if portrait_paths:
        print("Обработка книжных фото...")
        for i in range(0, len(portrait_paths), photos_per_page):
            chunk = portrait_paths[i : i + photos_per_page]
            builder.add_page_with_photos(chunk)

    output_path = config.output_file_path
    try:
        builder.save(output_path)
    except PermissionError:
        print(f"Ошибка: нет прав на запись в «{output_path}».")
        return 1
    except OSError as e:
        print(f"Ошибка при сохранении файла: {e}")
        return 1

    print(f"\nГотово! Документ сохранён: {output_path}")
    return 0


def main() -> int:
    """Точка входа: CLI или интерактивный режим."""
    try:
        args = parse_args()

        if args.path is None and args.count is None:
            config = get_user_input()
        else:
            if args.path is None or args.count is None:
                print("Ошибка: укажите оба аргумента --path и --count или запустите без аргументов для интерактивного режима.")
                return 1
            is_valid, msg = validate_folder(args.path)
            if not is_valid:
                print(msg)
                return 1
            is_valid, count_val, count_msg = validate_photos_per_page(args.count)
            if not is_valid or count_val is None:
                print(f"Ошибка: {count_msg}")
                return 1
            output_path = Path(args.output) if args.output else None
            config = create_config(
                folder_path=Path(args.path).resolve(),
                photos_per_page=count_val,
                margin_cm=DEFAULT_MARGIN_CM,
                output_path=output_path,
            )

        if config is None:
            return 1

        return run_with_config(config)

    except KeyboardInterrupt:
        print("\n\nПрервано пользователем.")
        return 130
    except Exception as e:
        logger.exception("Критическая ошибка")
        print(f"\nОшибка: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
