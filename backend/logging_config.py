import logging


def configure_logging():
    """Configure backend logging once for application and CLI entry points."""
    root_logger = logging.getLogger()
    if not root_logger.handlers:
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s %(levelname)s %(name)s: %(message)s"
        )

    backend_logger = logging.getLogger("backend")
    backend_logger.setLevel(logging.INFO)


configure_logging()
