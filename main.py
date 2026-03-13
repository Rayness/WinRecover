"""WinRecover — Помощник при переустановке Windows. Точка входа."""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from utils.helpers import setup_logging
from utils.i18n import load_language
_log_file = setup_logging()
load_language()

import logging
logger = logging.getLogger(__name__)


def main():
    logger.info("=" * 60)
    logger.info("WinRecover ЗАПУСК")
    logger.info("Python: %s", sys.version)
    logger.info("=" * 60)

    # Автодетект
    logger.info("Автодетект состояния...")
    t0 = time.time()
    from core.system_detector import check_startup_state
    state, config_path = check_startup_state()
    logger.info("Автодетект за %.2fс: state=%s, config=%s", time.time() - t0, state, config_path)

    # PySide6
    from PySide6.QtWidgets import QApplication
    from ui.app import App
    from ui.style import get_dark_stylesheet

    app = QApplication(sys.argv)
    app.setStyleSheet(get_dark_stylesheet())

    window = App(initial_state=state, config_path=config_path, log_file=_log_file)
    window.show()
    logger.info("Окно отображено, запускаю event loop")
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
