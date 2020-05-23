# SPDX-License-Identifier: Apache-2.0
# Example pysolate script: example.py

# 1) Import required libs
import os, hashlib

try:
    from urllib.request import urlretrieve
except ImportError:  # support Python 2.7
    from urllib import urlretrieve

# 2) Load pysolate
_f = os.path.join(os.path.expanduser("~"), ".pysolate")
_u = "https://raw.githubusercontent.com/tyrion/pysolate/master/pysolate.py"
_, _c = os.path.exists(_f) or urlretrieve(_u, _f), open(_f).read()

# 3) Ensure we are not getting hacked
_h = "8fca8cafe236be350fcc029b22a3f60a8a65e9957e358efc9ded0afd90c4e9fd"
assert hashlib.sha256(_c.encode("utf-8")).hexdigest() == _h, "SHA256 Mismatch"

# 4) Configure and execute pysolate
exec(
    compile(_c, "load_pysolate", "exec"),
    {"dependencies": ["click >=7.0"], "python": "3.7"},
)

# 5) Run your script
import sys
import click

click.secho("Hello from Python %d.%d o/" % sys.version_info[:2], bold=True)
