import importlib.util
import os
import sys

from streamlit.logger import get_logger

logger = get_logger(__name__)


def main():
    fixed_setup_script_path = os.path.abspath("./stgo.py")
    module_name = "streamlitgo.override"
    if os.path.exists(fixed_setup_script_path):
        logger.info(f"loading setup script at {fixed_setup_script_path}")
        spec = importlib.util.spec_from_file_location(module_name, fixed_setup_script_path)
        override_mod = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = override_mod
        spec.loader.exec_module(override_mod)
    else:
        logger.info(f"No fixed setup script found at {fixed_setup_script_path}, skipping")

    from streamlit.web.cli import main as stmain  # isort:skip

    stmain()


if __name__ == "__main__":
    main()
