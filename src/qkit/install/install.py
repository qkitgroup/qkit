import logging
from pathlib import Path
import platform
from types import ModuleType
from typing import Callable
import shutil
import sys

try:
    from importlib.resources import files, as_file
    from importlib.abc import Traversable
except ModuleNotFoundError:
    from importlib_resources import files, as_file
    from importlib.abc import Traversable

# Install Logging, Minimal Formatting
logging.basicConfig(level=logging.DEBUG, 
                    format='[%(levelname).1s] %(message)s')
logger = logging.getLogger(__name__)

def copy_named_template(source_cache: Traversable, target_path: Path, target_name: str, human_readable: str | None = None):
    package_file: Traversable = source_cache / f'{target_name}-tpl'
    logging.debug("Got reference %s: %s", human_readable if human_readable is not None else target_name, package_file)
    with as_file(package_file) as f:
        shutil.copyfile(f, target_path / target_name)

#################################
# Define Universal Scripts Here #
#################################

def create_base_structure(pwd: Path):
    """
    Check if the PWD exists and create the folders 'notebooks', 'data' and 'logs'.
    """
    assert pwd.exists(), "The current working directory must exist!"

    # Ensure Required Directories
    notebook_dir = pwd / "notebooks"
    notebook_dir.mkdir(exist_ok=True)

    data_dir = pwd / "data"
    data_dir.mkdir(exist_ok=True)
    
    log_dir = pwd / "logs"
    log_dir.mkdir(exist_ok=True)

    # Copy Files From Module
    from qkit import install
    install_files = files(install)

    copy_named_template(install_files, pwd, "jupyter_lab_config.py", "Jupyter Lab Config")
    copy_named_template(install_files, pwd, "qkit_local_config.py", "Qkit Local Config")



UNIVERSAL_SCRIPTS: list[Callable[[Path], None]] = [create_base_structure]

##############################
# Define System Scripts Here #
##############################

def windows_install_scripts(pwd: Path):
    from qkit.install import windows
    windows_script_files = files(windows)

    copy_named_template(windows_script_files, pwd, "launch_qviewkit.bat", "Qviewkit Launch Script")
    copy_named_template(windows_script_files, pwd, "launch.bat", "Launch Jupyter Lab Script")

def windows_associate_h5(pwd: Path):
    from qkit.install import windows
    windows_script_files = files(windows)
    association_script: Traversable = windows_script_files / 'associate_h5_windows.bat'
    logging.debug("Got association script: %s", association_script)
    with as_file(association_script) as f:
        logging.info("Running H5 association script")
        import os
        os.system(str(f))
        logging.info("Success!")

def windows_disable_smart_sorting(pwd: Path):
    from qkit.install import windows
    windows_script_files = files(windows)
    reg_file: Traversable = windows_script_files / 'Windows_UID_sorting.reg'
    with as_file(reg_file) as f:
        logging.info("Applying Registry Patch")
        import os
        os.system(f"regedit.exe /s {str(f)}")
        logging.info("Success!")

def windows_set_config_path(pwd: Path):
    import os
    config_path = pwd / "qkit_local_config.py"
    os.system(f'setx QKIT_LOCAL_CONFIG "{str(config_path.absolute())}"')

def linux_set_env(pwd: Path):
    import os
    if 'QKIT_LOCAL_CONFIG' in os.environ or 'QKIT_VENV' in os.environ:
        logger.warning("Qkit environment variables already set! Is qkit already installed?")
        return
    
    # Construct export command for local config and venv
    config_path = pwd / "qkit_local_config.py"
    venv_activate = Path(sys.executable).parent / "activate"
    var_export = f'\n#QKIT INSTALL\nQKIT_LOCAL_CONFIG="{str(config_path.absolute())}"\nQKIT_VENV="{str(venv_activate)}"\n\n'

    # Install Config for local user
    with open(Path.home() / ".profile", mode="a") as f:
        f.write(var_export)

def linux_install_desktop_files(pwd: Path):
    def install_file(fname):
        import os
        from qkit.install import linux
        linux_files = files(linux)
        tpl_file: Traversable = linux_files / fname
        desktop_file_target = Path.home() / '.local' / 'share' / 'applications'
        with as_file(tpl_file) as f:
            os.system(f"desktop-file-install --dir='{str(desktop_file_target)}' '{str(f)}'")
    
    install_file('qkit-qviewkit.desktop')
    install_file('qkit-qviewkit-url.desktop')

SYSTEM_SCRIPTS: dict[str, list[Callable[[Path], None]]] = {
    "Windows": [windows_install_scripts, windows_associate_h5, windows_set_config_path, windows_disable_smart_sorting],
    "Linux": [linux_set_env, linux_install_desktop_files],
    "Darwin": []
}

# Main Install Routine

def main():
    """
    Get and List Relevant paths (for diagnosis, should this fail) and setup for qkit usage.
    """
    logger.info("Qkit Setup")

    system = platform.system()
    logger.info("Operating System Type: %s", system)
    if system not in SYSTEM_SCRIPTS.keys():
        logger.error("Unsupported Operating System.")
        return

    pwd = Path.cwd()
    logger.info("User Install Path: %s", pwd)

    logger.info("Looking for qkit...")
    try:
        import qkit
        logger.info("Qkit installed, path: %s", qkit.__file__)
    except ImportError:
        logger.error("Qkit not importable, can't install.")
        return
    
    scripts = UNIVERSAL_SCRIPTS + SYSTEM_SCRIPTS[system]
    logger.info("Running %s install tasks...", len(scripts))
    for script in scripts:
        logger.info("Running task '%s'...", script.__name__)
        try:
            script(pwd)
        except:
            logger.exception("Setup step '%s' failed with the following Exception:", script.__name__)

    logging.info("Done.")

if __name__ == "__main__":
    main()