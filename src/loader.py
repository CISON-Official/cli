# Inside src/logger.py
import os
import logging
from datetime import datetime


class ChronologicalFolderHandler(logging.Handler):
    def __init__(self, base_dir="logs"):
        super().__init__()
        self.base_dir = base_dir

    def emit(self, record):
        try:
            msg = self.format(record)
            log_time = datetime.fromtimestamp(record.created)
            year_dir = log_time.strftime("%Y")
            month_dir = log_time.strftime("%m")
            day_file = log_time.strftime("%d.log")

            target_folder = os.path.join(self.base_dir, year_dir, month_dir)
            os.makedirs(target_folder, exist_ok=True)

            target_file_path = os.path.join(target_folder, day_file)
            with open(target_file_path, "a", encoding="utf-8") as f:
                f.write(msg + "\n")
        except Exception:
            self.handleError(record)


class LoggingManager:
    @staticmethod
    def setup_logging(base_dir: str = "logs", log_level: int = logging.INFO) -> None:
        root_logger = logging.getLogger()
        root_logger.setLevel(log_level)

        root_logger.handlers.clear()

        log_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

        console_handler = logging.StreamHandler()
        console_handler.setFormatter(log_formatter)
        console_handler.setLevel(log_level)
        root_logger.addHandler(console_handler)

        folder_file_handler = ChronologicalFolderHandler(base_dir=base_dir)
        folder_file_handler.setFormatter(log_formatter)
        folder_file_handler.setLevel(log_level)
        root_logger.addHandler(folder_file_handler)
