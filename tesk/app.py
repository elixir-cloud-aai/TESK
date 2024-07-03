"""API server entry point."""

import logging

from connexion import FlaskApp
from foca import Foca

from tesk.utils import get_config_path

logger = logging.getLogger(__name__)


def init_app() -> FlaskApp:
    """Initialize and return the FOCA app.

    This function initializes the FOCA app by loading the configuration
    from the environment variable `TESK_FOCA_CONFIG_PATH` if set, or from
    the default path if not. It raises a `FileNotFoundError` if the
    configuration file is not found.

    Returns:
        A Connexion application instance.

    Raises:
        FileNotFoundError: If the configuration file is not found.
    """
    config_path = get_config_path()

    # Check if the configuration file exists
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found at: {config_path}")

    foca = Foca(
        config_file=config_path,
    )
    return foca.create_app()


def main() -> None:
    """Run FOCA application."""
    app = init_app()
    app.run(port=app.port)


if __name__ == "__main__":
    main()
