<!--
# SPDX-License-Identifier: CC-BY-SA-4.0
# Copyright 2019 Germano Gabbianelli <git@germano.dev>
-->

# pysolate

*Easily run your standalone script in an isolated virtual environment.*

[![](https://img.shields.io/pypi/v/pysolate.svg)](https://pypi.python.org/pypi/pysolate)
[![](https://reuse.software/badge/reuse-compliant.svg)](https://reuse.software/)

## Features

- Runs your script in its own virtual environment
- Automatically downloads dependencies
- Allows to specify a required Python version
- No external tools (e.g. pipx) required to run your script. Only Python.
- Discovers Python versions installed by `pyenv`

## Requirements

- Runs on both Python 2.7 and Python 3.
- When running on older systems (Python < 3.3), it needs `virtualenv` to be
  installed.

## Why

1) Distribute a script, without assuming your users have an external tool
   installed, such as `pipx`.
2) Distribute a script, without requiring your users to setup a
   virtual environment and manually install its dependencies.
3) Easily bundle a Python script in a non-Python project
4) Add a supporting script (e.g. build the project or run tests) avoiding
   potential conflicts with your project's dependencies.

## How does it work

Every time a pysolate script runs it will

- detect if the private virtual env has already been created
- otherwise:
  * try to find a version of Python compatible with the script
  * create the private virtual environment
  * install dependencies
- switch to the correct virtual environment
- run the script

## Usage

In order to use pysolate in your script, you need to make sure it loads before
your script executes. Here is an example script that shows how that can be
accomplished:

```python
# SPDX-License-Identifier: Apache-2.0
# Example pysolate script: example.py
# 1) Import required libs
import os, hashlib, pathlib, urllib.request

# 2) Load pysolate
_f = pathlib.Path.home() / ".pysolate"
_u = "https://raw.githubusercontent.com/tyrion/pysolate/v0.2.0/pysolate.py"
_, _c = _f.exists() or urllib.request.urlretrieve(_u, _f), open(_f).read()

# 3) Ensure we are not getting hacked
_h = "a62bb50cd98da1995897a9f97a5b8549a1e0090e67fff970f8025db7b1b45c82"
assert hashlib.sha256(_c.encode("utf-8")).hexdigest() == _h, "SHA256 Mismatch"

# 4) Configure and execute pysolate
exec(
    compile(_c, "load_pysolate", "exec"),
    {"dependencies": ["click >=7.0"], "python": "3.7"},
)

# 5) Run your script
import sys
import click

click.echo("Hello from Python %d.%d o/" % sys.version_info[:2])
```

By running this script for the first time you obtain:

```bash
$ python example.py
04:45:40  INFO |     Creating venv | ~/.local/share/pysolate/example.py-eb0e4f
04:45:42  INFO |   Installing deps
Hello from Python 3.7 o/
```

Subsequent runs do not recreate the env, or install the dependencies:

```bash
$ python example.py
Hello from Python 3.7 o/
```

Or you can run in debug mode, to see everything that happens

```
$ PYS_LOG=DEBUG python2 hello.py
04:47:04 DEBUG |    No active venv | ~/.local/share/pyenv/versions/3.7.5rc1/bin/python
04:47:04 DEBUG |   Good Python ver | 3.7.5rc1
04:47:04  INFO |     Creating venv | ~/.local/share/pysolate/example.py-eb0e4f
04:47:07  INFO |   Installing deps
Collecting click>=7.0
  Using cached https://files.pythonhosted.org/packages/d2/3d/fa76db83bf75c4f8d338c2fd15c8d33fdd7ad23a9b5e57eb6c5de26b430e/click-7.1.2-py2.py3-none-any.whl
Installing collected packages: click
Successfully installed click-7.1.2
04:47:07 DEBUG |        Restarting | ~/.local/share/pysolate/example.py-eb0e4f/bin/python
04:47:07 DEBUG |  Good active venv | ~/.local/share/pysolate/example.py-eb0e4f
04:47:07 DEBUG |   Starting script | ~/src/pysolate/example.py
Hello from Python 3.7 o/
```

Note that in this example we are using some features (`pathlib` and
`urllib.request`) that are not available on Python 2.7. If you wish to maintain
compatibility with legacy versions, have a look at example.py in the repo.

## Options

Configuration options can be specified by passing a dictionary object to
`exec`, like shown in the example above.
Most of them can also be configured with environment variables, by using the
prefix `PYS_`. For example `$PYS_LOG` or `$PYS_HOME`.

### `dependencies`

(_required_, *cannot be set by env*)

The dependencies your script needs in order to run, as a list of strings.
If your script has no dependencies, you must pass the value `()`, as pysolate
uses this variable to detect if is being `exec`uted.

### `log`

(_optional_, default: `INFO`)

The logging level you want pysolate to run with.

### `home`

(_optional_, default: `~/.local/share/pysolate`)

The location where pysolate will store all the private repositories by default.
This directory will be created if it does not exist.

### `venv`

(_optional_)

The location of the private virtual environment for the current script.
By default the environment will be located inside `PYS_HOME` and its name based
upon the name of the script plus its sha1 hash.
Setting this option enables you to store the private virtual environment
outside `PYS_HOME`.

### `python`

(_optional_, default: `None`, *cannot be set by env*)

Specifies the required Python version. Can be either a string or a callable.
If a callback is specified, it will receive a tuple (like `sys.version_info`)
and should return `True` for a compatible version.
