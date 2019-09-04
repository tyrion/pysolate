#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright 2019 Germano Gabbianelli <git@germano.dev>
import glob
import hashlib
import logging
import operator
import os
import re
import sys

if sys.version_info < (3, 6):
    sys.stderr.write("Python 3.6 or greater is required\n")
    sys.exit(1)

from pathlib import Path

if __name__ == "__main__":
    EXC_PATH = Path(sys.executable).resolve()

    try:
        _f  # FIXME not solid
    except NameError:
        # We are being called with a shebang
        SRC_PATH = Path(sys.argv[1]).resolve()
        BIN_PATH = Path(__file__).resolve()
        EXEC = False
    else:
        # We are being `exec`uted inside a script
        SRC_PATH = Path(sys.argv[0]).resolve()
        BIN_PATH = SRC_PATH
        EXEC = True

    try:
        PYS_HOME = Path(os.environ["PYS_HOME"]).resolve()
    except KeyError:
        PYS_HOME = Path.home() / ".local" / "share" / "pysolate"

    try:
        PYS_VENV = Path(os.environ["PYS_VENV"]).resolve()
    except KeyError:
        _hash = hashlib.sha1(str(SRC_PATH).encode("utf-8")).hexdigest()[:6]
        PYS_VENV = PYS_HOME / "-".join((str(SRC_PATH.name), _hash))
else:
    BIN_PATH = Path(sys.argv[0])


def restore_var(var):
    try:
        os.environ[var] = os.environ[f"_OLD_VIRTUAL_{var}"]
    except KeyError:
        pass


def print_env(env=os.environ):
    for k, v in env.items():
        if (
            k.startswith("PYENV")
            or k in {"PATH", "VIRTUAL_ENV"}
            or k.startswith("_OLD_VIRTUAL")
        ):
            print(k, v)


def restart(python="python", bin_path=BIN_PATH):
    os.execlp(python, python, bin_path, *sys.argv[1:])


def parse_version(v: str):
    return tuple(int(x) for x in v.rsplit("/", 1)[-1].split("."))


def find_py(version, op=operator.eq):
    if "PYENV_ROOT" in os.environ:
        version_t = parse_version(version)
        PYENV_ROOT = os.environ["PYENV_ROOT"]

        for v in glob.glob(f"{PYENV_ROOT}/versions/3.*"):
            n = parse_version(v)[:2]
            if op(version_t, n):
                break
        else:
            print("Could not find a suitable python version")
            sys.exit(1)

        PYTHON = Path(v) / "bin" / "python"
    else:
        PYTHON = f"python{version}"

    return PYTHON


if __name__ == "__main__":

    LOG_LEVEL = os.environ.get("PYS_LOGGING", "INFO")
    LOG_LEVEL = logging.getLevelName(
        int(LOG_LEVEL) if LOG_LEVEL.isdigit() else LOG_LEVEL.upper()
    )

    logging.basicConfig(
        level=LOG_LEVEL,
        format="%(asctime)s %(levelname)5s | %(message)s",
        datefmt="%I:%M:%S",
    )

    logger = logging.getLogger()
    # logger.debug(f"   sys.executable | {sys.executable}")

    try:
        VIRTUAL_ENV = Path(os.environ["VIRTUAL_ENV"]).resolve()
    except KeyError:
        logging.debug(f"   No active venv | {sys.executable}")

        if not PYS_VENV.exists():
            logging.info(f"    Creating venv | {PYS_VENV}")
            import venv

            venv.create(PYS_VENV, symlinks=True, with_pip=True)

        # os.environ["PATH"] = ":".join((str(PYS_VENV / "bin"), os.environ["PATH"]))

        # Activate the correct venv and restart the script
        os.environ["VIRTUAL_ENV"] = str(PYS_VENV)
        PYTHON = PYS_VENV / "bin" / "python"
        restart(PYTHON)

    else:
        # We are running inside a wrong virtualenv. Try to exit.
        if VIRTUAL_ENV != PYS_VENV:
            logging.debug(f"Wrong active venv | {VIRTUAL_ENV}")
            del os.environ["VIRTUAL_ENV"]

            if "PYENV_VIRTUAL_ENV" in os.environ:
                del os.environ["PYENV_VIRTUAL_ENV"]

                os.environ.pop("PYENV_VERSION", None)
                os.environ.pop("PYENV_DIR", None)
                os.environ.pop("PYENV_ACTIVATE_SHELL", None)

                PYENV_ROOT = os.environ["PYENV_ROOT"]
                pattern = (
                    rf"^[^:]+:[^:]+(:{PYENV_ROOT}/plugins/[^/]+/bin)*:(.*)$"
                )
                os.environ["PATH"] = re.match(
                    pattern, os.environ["PATH"]
                ).group(2)
            else:
                restore_var("PATH")
                restore_var("PYTHONHOME")

            restart(find_py("3.6", op=operator.le))
        else:
            logger.debug(f" Good active venv | {VIRTUAL_ENV}")

    ### Start script

    os.environ["PYS_HOME"] = str(PYS_HOME)
    os.environ["PYS_VENV"] = str(PYS_VENV)

    # TODO: de-initialize logging

    PYS_DEPS = os.environ.get("PYS_DEPS", "")

    if PYS_DEPS:
        import shlex
        import subprocess

        logger.debug(f"  Installing deps | {PYS_DEPS}")

        subprocess.check_call(
            [
                sys.executable,
                "-mpip",
                "-q",
                "--disable-pip-version-check",
                "install",
                *shlex.split(PYS_DEPS),
            ]
        )
        os.environ["PYS_DEPS"] = ""

        logger.debug(f"  Starting script | {SRC_PATH}")
        restart(sys.executable, SRC_PATH)
    else:

        if EXEC:
            # Unset all global variables
            for var in list(globals().keys()):
                if not var.startswith("__"):
                    del globals()[var]
            del globals()["var"]
        else:
            logger.debug(f"  Starting script | {SRC_PATH}")
            restart(sys.executable, SRC_PATH)
