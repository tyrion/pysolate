import logging
import os
import re
import subprocess
import sys
from os import path


logger = logging.getLogger()


def restart(python="python", bin_path=None):
    bin_path = bin_path or sys.argv[0]
    logger.debug("       Restarting | %s", python)
    os.execlp(python, python, bin_path, *sys.argv[1:])


def abspath(x):
    """
    Compute absolute path and resolve symlinks
    """
    return path.abspath(path.realpath(x))


def unpack_ver(v):
    return tuple(int(x) if x else 0 for x in v)


_fmt = {"alpha": "a", "beta": "b", "candidate": "rc", "final": ""}


def format_ver(v):
    ver = ".".join(map(str, v[:3]))
    return "%s%s%s" % (ver, _fmt[v[3]], v[4] or "") if len(v) == 5 else ver


def find_python_versions():
    ver_pat = re.compile(r"(\d)\.(\d)(?:\.(\d+).*)?(?:-.*)?$")
    dirs = map(abspath, os.environ["PATH"].split(":"))

    try:
        PYENV_ROOT = abspath(os.environ["PYENV_ROOT"])
    except KeyError:
        pass
    else:
        dir = path.join(PYENV_ROOT, "versions")

        try:
            entries = os.listdir(dir)
        except OSError:
            pass
        else:
            for entry in entries:
                m = ver_pat.match(entry)
                if m is not None:
                    yield unpack_ver(m.groups()), path.join(
                        dir, entry, "bin", "python"
                    )

        dirs = filter(lambda p: not p.startswith(PYENV_ROOT), dirs)

    exc_pat = re.compile(r"^python(?:\d(?:.\d))$")

    for dir in dirs:
        try:
            entries = os.listdir(dir)
        except OSError:
            continue

        for entry in filter(exc_pat.match, entries):
            py = path.join(dir, entry)
            try:
                out = subprocess.check_output([py, "-V"])
            except OSError:
                continue

            m = ver_pat.search(out.decode("utf-8"))
            if m is not None:
                yield unpack_ver(m.groups()), py


def find_python():
    """
    Finds a Python version compatible with the one requested by the user.
    If a compatible version cannot be found, it stops pysolate.
    """
    try:
        ver = get_var("python", env=False)
    except KeyError:
        logger.debug("  Good Python ver | %s", format_ver(sys.version_info))
        return sys.executable, sys.version_info

    ver = unpack_ver(ver.split(".")) if isinstance(ver, str) else ver
    fn = (lambda *v: v[: len(ver)] == ver) if not callable(ver) else ver

    if fn(*sys.version_info[:3]):
        logger.debug("  Good Python ver | %s", format_ver(sys.version_info))
        return sys.executable, sys.version_info

    for (v, py) in find_python_versions():
        if fn(*v):
            logger.debug(" Found Python ver | %s (%s)", py, format_ver(v))
            return (py, v)

    logger.error("Could not find matching Python version")
    sys.exit(1)


def run(args, **kwds):
    if logger.getEffectiveLevel() > 10:
        kwds["stdin"] = kwds["stdout"] = kwds["stderr"] = subprocess.DEVNULL

    try:
        subprocess.call(args, **kwds)
    except OSError:
        return False
    else:
        return True


def ensure_venv(venv, dependencies=()):
    PYTHON = path.join(venv, "bin", "python")

    if not path.exists(venv):
        py, ver = find_python()

        logger.info("    Creating venv | %s", venv)
        args = ["--symlinks", venv]
        if ver < (3, 3):
            success = (
                # Try global virtualenv and then with -m as fallback
                run(["virtualenv", "-p", py] + args)
                or run([py, "-mvirtualenv", "-p", py] + args)
            )
        else:
            success = run([py, "-mvenv"] + args)
        if not success:
            logger.error(
                "Failed to create venv. Ensure Py > 3.3 or virtualenv is"
                " installed"
            )
        if dependencies:
            logger.info("  Installing deps")
            deps = [
                dep if isinstance(dep, str) else ("%s%s" % dep)
                for dep in dependencies
            ]
            run(
                [PYTHON, "-mpip", "--disable-pip-version-check", "install"]
                + deps,
            )

    os.environ["VIRTUAL_ENV"] = venv
    return PYTHON


def get_var(name, default=None, env=True):
    try:
        return globals()[name]
    except KeyError:
        if default is not None:
            name = "PYS_{}".format(name.upper())
            return os.environ.get(name, default) if env else default
        raise


def main():
    log_level = get_var("log", "INFO")
    log_level = logging.getLevelName(
        int(log_level) if log_level.isdigit() else log_level.upper()
    )

    logging.basicConfig(
        level=log_level,
        format="%(asctime)s %(levelname)5s | %(message)s",
        datefmt="%I:%M:%S",
    )

    src = abspath(sys.argv[0])
    try:
        home = get_var("home")
    except KeyError:
        # TODO: improve
        home = path.join(path.expanduser("~"), ".local", "share", "pysolate")

    try:
        venv = abspath(get_var("venv"))
    except KeyError:
        import hashlib

        _hash = hashlib.sha1(src.encode("utf-8")).hexdigest()[:6]
        venv = path.join(home, "-".join((path.basename(src), _hash)))

    py = None
    dependencies = get_var("dependencies", (), env=False)
    try:
        current_venv = abspath(os.environ["VIRTUAL_ENV"])
    except KeyError:
        logger.debug("   No active venv | %s", sys.executable)
        py = ensure_venv(venv, dependencies)
    else:
        # We are running inside a wrong virtualenv. Try to exit.
        if current_venv != venv:
            logger.debug("Wrong active venv | %s", current_venv)
            del os.environ["VIRTUAL_ENV"]

            py = ensure_venv(venv, dependencies)
        else:
            logger.debug(" Good active venv | %s", current_venv)

    if py is not None:
        restart(py)

    logger.debug("  Starting script | %s", src)


if "dependencies" in globals():
    main()
