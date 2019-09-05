<!--
# SPDX-License-Identifier: CC-BY-SA-4.0
# Copyright 2019 Germano Gabbianelli <git@germano.dev>
-->
# pysolate

Easily run your standalone script in an isolated virtual environment

[![](https://img.shields.io/pypi/v/pysolate.svg)](https://pypi.python.org/pypi/fsfe-reuse)
[![](https://reuse.software/badge/reuse-compliant.svg)](https://reuse.software/)

## Features
* Ensures your script **always** runs in its own virtual environment
* Ensures your script has the required dependencies to run
* Ensures your script runs with the correct Python version

## Requirements

pysolate currently requires python 3.6 or greater in order to run.

## Why

pysolate is useful in case you have a python script that requires
some dependencies and needs to run in a private virtual environment.

For example, you may want to distribute a standalone python script to perform
some system administration task which requires some external dependencies (e.g
click and requests), but you do not want to ask your users to
manually install them in the system, or to have to deal with setting up virtual
environments.

An other example, is if you are developing a Python project that needs some
supporting scripts (e.g. to build the project or run tests) but you do not
want to add the dependencies of those scripts to your project.

## How does it work

Every time a pysolate script runs it will

* detect if it is running in a (wrong) virtual environment and deactivate it
* detect if its own private virtual environment exists, otherwise create it
* activate its own private virtual environment
* ensure that dependencies are installed
* run the script

## Usage

In order to use pysolate in your script, you need to make sure it loads before
your script executes. Here is an example script that shows how that can be
accomplished:


```python
# SPDX-License-Identifier: Apache-2.0
# Example pysolate script: hello.py
import os, pathlib, urllib.request

# Declare your dependencies here:
# NOTE: you *must* keep `setdefault`
os.environ.setdefault("PYS_DEPS", "click requests")

# Load pysolate either from the local filesystem or by downloading the
# latest version.
# NOTE: you *must not* edit the variable names `_f` and `_u`
_f = pathlib.Path.home() / ".pysolate"
_u = "https://germano.dev/pysolate.py"
_f.exists() or urllib.request.urlretrieve(_u, _f)
exec(compile(open(_f).read(), "load_pysolate", "exec")

# Write your script here. You can now import your dependencies.
# NOTE: the variables declared before this line are not in scope anymore.
import click
click.echo("Hello o/")
```

By running this script you obtain:
```bash
$ python hello.py
11:59:16  INFO |     Creating venv | ~/.pys_home/hello.py-ef2ff4
Hello o/
```

Or you can run in debug mode, to see everything that happens
```
$ PYS_LOGGING=DEBUG python hello.py
12:04:05 DEBUG | Wrong active venv | ~/.pyenv/versions/3.7.2/envs/tutorial
12:04:05 DEBUG |    No active venv | ~/.pyenv/versions/3.7.2/bin/python
12:04:05  INFO |     Creating venv | ~/.pys_home/hello.py-ef2ff4
12:04:07 DEBUG |  Good active venv | ~/.pys_home/hello.py-ef2ff4
12:04:07 DEBUG |   Installing deps | click requests
12:04:09 DEBUG |   Starting script | ~/src/hello.py
12:04:07 DEBUG |  Good active venv | ~/.pys_home/hello.py-ef2ff4
Hello o/
```


## Options

### `PYS_DEPS`

(*optional*, default: `""`)

The dependencies your script needs in order to run, separated by space.

### `PYS_LOGGING`
(*optional*, default: `INFO`)

The logging level you want pysolate to run with.

### `PYS_HOME`
(*optional*, default: `~/.local/share/pysolate`)

The location where pysolate will store all the private repositories by default.
This directory will be created if it does not exist.

### `PYS_VENV`

The location of the private virtual environment for the current script.
By default the environment will be located inside `PYS_HOME` and its name based
upon the name of the script plus its sha1 hash.
Setting this option enables you to store the private virtual environment
outside `PYS_HOME`.
