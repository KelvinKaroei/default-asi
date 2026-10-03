import logging
from logging.handlers import RotatingFileHandler


def local_logger(data_dir):
    """Eventos operacionais apenas: sem prompts, tokens, cabeçalhos ou respostas."""
    folder = data_dir / "logs"
    folder.mkdir(exist_ok=True)
    logger = logging.Logger("cyberai", level=logging.INFO)
    handler = RotatingFileHandler(folder / "backend.log", maxBytes=1_000_000,
                                  backupCount=3, encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    logger.addHandler(handler)
    return logger
