import os
import sys
from loguru import logger


def setup_logger():
    # 1. Удаляем стандартный обработчик Loguru (чтобы не было двойных логов)
    logger.remove()

    # 2. Добавляем красивый цветной вывод в консоль для разработки
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level="INFO"
    )

    # 3. Настраиваем запись в файл (Архивация)
    # Создаем папку logs, если ее нет
    os.makedirs("logs", exist_ok=True)

    logger.add(
        "logs/app.log",
        rotation="10 MB",  # Как только файл достигает 10 Мб, создается новый
        retention="30 days",  # Храним логи только за последний месяц, старые удаляем
        compression="zip",  # Старые логи сжимаем в zip для экономии места
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="INFO"
    )

    return logger


# Создаем готовый объект, который будем импортировать в другие файлы
log = setup_logger()