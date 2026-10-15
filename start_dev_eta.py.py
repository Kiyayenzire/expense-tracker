from __future__ import annotations

import logging
import os
import platform
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

# ============================================================
# CONFIGURATION
# ============================================================
PROJECT_DIR = Path(__file__).resolve().parent
LOGS_DIR = PROJECT_DIR / "logs"

# Maximum time to wait for Docker Engine (in seconds)
DOCKER_TIMEOUT = 180

# Seconds between Docker readiness checks
DOCKER_CHECK_INTERVAL = 3

# ============================================================
# PLATFORM-SPECIFIC APPLICATION LOCATIONS
# ============================================================
# Windows
WINDOWS_DOCKER_DESKTOP = Path(
    r"C:\Program Files\Docker\Docker\Docker Desktop.exe"
)
WINDOWS_FIREFOX_PATHS = [
    Path(r"C:\Program Files\Mozilla Firefox\firefox.exe"),
    Path(r"C:\Program Files (x86)\Mozilla Firefox\firefox.exe"),
    Path(os.path.expandvars(r"%LOCALAPPDATA%\Mozilla Firefox\firefox.exe")),
]

# macOS
MACOS_DOCKER_DESKTOP = Path("/Applications/Docker.app")
MACOS_FIREFOX = Path("/Applications/Firefox.app")

# Linux
LINUX_FIREFOX_COMMAND = "firefox"

# VS Code is expected to be available through PATH
VSCODE_COMMAND = "code"


# ============================================================
# LOGGING
# ============================================================
def create_loggers() -> tuple[logging.Logger, logging.Logger]:
    """Create separate log files for startup operations and errors."""
    LOGS_DIR.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    startup_log = LOGS_DIR / f"startup_{timestamp}.log"
    error_log = LOGS_DIR / f"errors_{timestamp}.log"

    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")

    # Main startup logger
    startup_logger = logging.getLogger("startup")
    startup_logger.setLevel(logging.INFO)
    startup_logger.propagate = False

    startup_file_handler = logging.FileHandler(startup_log, encoding="utf-8")
    startup_file_handler.setFormatter(formatter)

    startup_console_handler = logging.StreamHandler()
    startup_console_handler.setFormatter(formatter)

    startup_logger.addHandler(startup_file_handler)
    startup_logger.addHandler(startup_console_handler)

    # Error logger
    error_logger = logging.getLogger("errors")
    error_logger.setLevel(logging.WARNING)
    error_logger.propagate = False

    error_file_handler = logging.FileHandler(error_log, encoding="utf-8")
    error_file_handler.setFormatter(formatter)

    error_logger.addHandler(error_file_handler)

    startup_logger.info("Startup log initialized: %s", startup_log)
    startup_logger.info("Error log initialized: %s", error_log)

    return startup_logger, error_logger


logger, error_logger = create_loggers()


# ============================================================
# GENERAL UTILITIES
# ============================================================
def get_operating_system() -> str:
    """Return a normalized operating-system name."""
    system = platform.system()
    if system == "Windows":
        return "Windows"
    if system == "Darwin":
        return "macOS"
    if system == "Linux":
        return "Linux"

    raise RuntimeError(f"Unsupported operating system: {system}")


def command_exists(command: str) -> bool:
    """Return True if a command exists in PATH."""
    return shutil.which(command) is not None


def launch_gui_app(cmd: list[str | Path]) -> None:
    """Launch a GUI application as a completely detached background process."""
    cmd_str = [str(c) for c in cmd]
    kwargs: dict[str, int | bool | None] = {
        "stdout": subprocess.DEVNULL,
        "stderr": subprocess.DEVNULL,
    }

    if sys.platform == "win32":
        # Ensure Windows GUI apps don't lock the console process
        detached = getattr(subprocess, "DETACHED_PROCESS", 0x00000008)
        new_group = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0x00000200)
        kwargs["creationflags"] = detached | new_group

    subprocess.Popen(cmd_str, **kwargs)


def run_command(command: list[str]) -> subprocess.CompletedProcess[str]:
    """Run a command from the project directory and log STDOUT/STDERR."""
    logger.info("Running command: %s", " ".join(command))

    try:
        result = subprocess.run(
            command,
            cwd=PROJECT_DIR,
            capture_output=True,
            text=True,
            shell=False,
        )
    except Exception as exc:
        logger.exception("Failed to execute command.")
        error_logger.error("Failed to execute command: %s", " ".join(command))
        error_logger.error("Exception: %s", exc)
        raise

    if result.stdout.strip():
        logger.info("STDOUT:\n%s", result.stdout.strip())

    if result.stderr.strip():
        logger.warning("STDERR:\n%s", result.stderr.strip())
        error_logger.warning("Command stderr:\n%s", result.stderr.strip())

    return result


# ============================================================
# STEP 1: START DOCKER
# ============================================================
def start_docker(os_name: str) -> None:
    """Start Docker Desktop on Windows/macOS."""
    logger.info("[1] Starting Docker...")

    if os_name == "Windows":
        if not WINDOWS_DOCKER_DESKTOP.exists():
            raise FileNotFoundError(
                f"Docker Desktop was not found at: {WINDOWS_DOCKER_DESKTOP}"
            )
        launch_gui_app([WINDOWS_DOCKER_DESKTOP])
        logger.info("Docker Desktop process started.")

    elif os_name == "macOS":
        if not MACOS_DOCKER_DESKTOP.exists():
            raise FileNotFoundError(
                f"Docker Desktop was not found at: {MACOS_DOCKER_DESKTOP}"
            )
        launch_gui_app(["open", "-a", "Docker"])
        logger.info("Docker Desktop process started.")

    elif os_name == "Linux":
        logger.info(
            "Linux detected. Docker is expected to be managed by system services."
        )


# ============================================================
# STEP 2: OPEN VS CODE
# ============================================================
def open_vscode(os_name: str) -> None:
    """Open VS Code targeting the current project directory."""
    logger.info("[2] Opening VS Code...")

    try:
        if os_name == "Windows":
            vscode_command = shutil.which("code.cmd") or shutil.which("code")
            if vscode_command is None:
                raise FileNotFoundError(
                    "VS Code command 'code.cmd' or 'code' was not found in PATH."
                )
            logger.info("VS Code command found at: %s", vscode_command)
            launch_gui_app([vscode_command, PROJECT_DIR])
        else:
            if not command_exists(VSCODE_COMMAND):
                raise FileNotFoundError(
                    "VS Code command 'code' was not found in PATH."
                )
            launch_gui_app([VSCODE_COMMAND, PROJECT_DIR])

        logger.info("VS Code opened successfully.")

    except Exception:
        logger.exception("Failed to open VS Code.")
        error_logger.exception("Failed to open VS Code.")


# ============================================================
# STEP 3: OPEN FIREFOX
# ============================================================
def open_firefox(os_name: str) -> None:
    """Open Firefox browser."""
    logger.info("[3] Opening Firefox...")

    try:
        if os_name == "Windows":
            firefox_path = None
            for path in WINDOWS_FIREFOX_PATHS:
                if path.exists():
                    firefox_path = str(path)
                    break

            if not firefox_path:
                firefox_path = shutil.which("firefox")

            if not firefox_path:
                raise FileNotFoundError("Firefox executable was not found on Windows.")

            launch_gui_app([firefox_path])

        elif os_name == "macOS":
            if not MACOS_FIREFOX.exists():
                raise FileNotFoundError(
                    f"Firefox was not found at: {MACOS_FIREFOX}"
                )
            launch_gui_app(["open", "-a", "Firefox"])

        elif os_name == "Linux":
            if not command_exists(LINUX_FIREFOX_COMMAND):
                raise FileNotFoundError("Firefox command was not found in PATH.")
            launch_gui_app([LINUX_FIREFOX_COMMAND])

        logger.info("Firefox opened successfully.")

    except Exception:
        logger.exception("Failed to open Firefox.")
        error_logger.exception("Failed to open Firefox.")


# ============================================================
# STEP 4: WAIT FOR DOCKER
# ============================================================
def wait_for_docker() -> bool:
    """Wait until Docker Engine responds successfully."""
    logger.info("[4] Waiting for Docker Engine...")
    logger.info("Docker timeout: %s seconds", DOCKER_TIMEOUT)

    start_time = time.monotonic()

    while time.monotonic() - start_time < DOCKER_TIMEOUT:
        result = subprocess.run(
            ["docker", "info"],
            capture_output=True,
            text=True,
            shell=False,
        )

        if result.returncode == 0:
            logger.info("Docker Engine is ready.")
            return True

        logger.info(
            "Docker Engine is not ready yet. Retrying in %s seconds...",
            DOCKER_CHECK_INTERVAL,
        )
        time.sleep(DOCKER_CHECK_INTERVAL)

    logger.error(
        "Docker Engine did not become ready within %s seconds.", DOCKER_TIMEOUT
    )
    error_logger.error(
        "Docker Engine did not become ready within %s seconds.", DOCKER_TIMEOUT
    )
    return False


# ============================================================
# STEP 5: VERIFY DOCKER COMPOSE
# ============================================================
def verify_compose_available() -> bool:
    """Check that Docker Compose V2 is available."""
    logger.info("Checking Docker Compose...")

    result = run_command(["docker", "compose", "version"])

    if result.returncode != 0:
        logger.error("Docker Compose is not available.")
        error_logger.error("Docker Compose is not available.")
        return False

    logger.info("Docker Compose is available.")
    return True


# ============================================================
# STEPS 6 & 7: REMOVE ORPHANS + START CONTAINERS
# ============================================================
def start_compose_with_orphan_cleanup() -> bool:
    """Reconcile the Compose project and remove orphan containers."""
    logger.info("[5] Removing orphan containers...")
    logger.info(
        "Orphan cleanup will be performed by 'docker compose up --remove-orphans'."
    )

    logger.info("[6] Starting/reconciling Docker Compose containers...")
    result = run_command(["docker", "compose", "up", "-d", "--remove-orphans"])

    if result.returncode != 0:
        logger.error("Docker Compose failed to start/reconcile the containers.")
        error_logger.error("Docker Compose failed to start/reconcile the containers.")
        return False

    logger.info("Docker Compose containers are started/reconciled.")
    return True


# ============================================================
# STEP 8: CHECK CONTAINER STATUS
# ============================================================
def check_container_status() -> bool:
    """Check Docker Compose container status."""
    logger.info("[7] Checking container status...")

    result = run_command(["docker", "compose", "ps"])

    if result.returncode != 0:
        logger.error("Unable to retrieve container status.")
        error_logger.error("Unable to retrieve container status.")
        return False

    return True


# ============================================================
# STEPS 9 & 10: COLLECT LOGS + DETECT ERRORS
# ============================================================
def check_container_logs() -> bool:
    """Collect recent container logs and detect common error indicators."""
    logger.info("[8] Collecting recent container logs...")

    result = run_command(["docker", "compose", "logs", "--tail", "100"])

    if result.returncode != 0:
        logger.error("Unable to retrieve container logs.")
        error_logger.error("Unable to retrieve container logs.")
        return False

    logs = result.stdout.strip()

    if not logs:
        logger.info("No container logs were returned.")
        return True

    logger.info("Container logs:\n%s", logs)

    logger.info("[9] Checking logs for potential errors...")
    error_keywords = [
        "error",
        "exception",
        "fatal",
        "failed",
        "traceback",
        "critical",
    ]

    found_errors: list[str] = []

    for line in logs.splitlines():
        lower_line = line.lower()
        if any(keyword in lower_line for keyword in error_keywords):
            found_errors.append(line)

    if found_errors:
        logger.warning("Potential errors detected in container logs.")
        error_logger.warning("Potential errors detected in container logs:")
        for error in found_errors:
            error_logger.warning(error)
        return False

    logger.info("No obvious errors detected in recent logs.")
    return True


# ============================================================
# MAIN EXECUTION FLOW
# ============================================================
def main() -> int:
    logger.info("=" * 70)
    logger.info("DEVELOPMENT ENVIRONMENT STARTUP")
    logger.info("=" * 70)
    logger.info("Project directory: %s", PROJECT_DIR)

    try:
        os_name = get_operating_system()
        logger.info("Operating system: %s", os_name)

        if not command_exists("docker"):
            logger.error("Docker command was not found in PATH.")
            error_logger.error("Docker command was not found in PATH.")
            return 1

        start_docker(os_name)
        open_vscode(os_name)
        open_firefox(os_name)

        if not wait_for_docker():
            logger.error("Docker is not available. Startup aborted.")
            return 1

        if not verify_compose_available():
            logger.error("Docker Compose is not available. Startup aborted.")
            return 1

        if not start_compose_with_orphan_cleanup():
            logger.error("Docker Compose startup failed.")
            return 1

        status_ok = check_container_status()
        logs_ok = check_container_logs()

        if status_ok and logs_ok:
            logger.info("=" * 70)
            logger.info("DEVELOPMENT ENVIRONMENT STARTUP COMPLETE")
            logger.info("=" * 70)
            return 0

        logger.warning("=" * 70)
        logger.warning("STARTUP COMPLETED WITH WARNINGS/ERRORS")
        logger.warning("=" * 70)
        return 1

    except KeyboardInterrupt:
        logger.warning("Startup interrupted by user.")
        error_logger.warning("Startup interrupted by user.")
        return 130

    except Exception:
        logger.exception("Unexpected error during startup.")
        error_logger.exception("Unexpected error during startup.")
        return 1


# ============================================================
# ENTRY POINT
# ============================================================
if __name__ == "__main__":
    sys.exit(main())