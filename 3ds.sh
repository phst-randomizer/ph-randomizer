#!/bin/bash

set -e

shopt -s extglob

# Move all python, json, and logic files to temporary directory
mkdir -p 3ds/
find . -name '*.py' -exec cp --parents \{\} 3ds/ \;
find . -name '*.json' -exec cp --parents \{\} 3ds/ \;
find . -name '*.logic' -exec cp --parents \{\} 3ds/ \;

# Strip all type hints for compatability with python 3.6
pip install strip-hints autoflake
find 3ds/ -type f -name '*.py' ! -name "aux_models.py" -exec strip-hints --inplace {} \;
find 3ds/ -type f -name '*.py' -exec autoflake --in-place --remove-unused-variables {} \;

# Use backport of `from __future__ import annotations` for python 3.6 by adding
# its import statement to the top of every python file.
# The package itself will be installed at a later step.
find 3ds/ -type f -name '*.py' ! -name "aux_models.py" -print0  | xargs -0 sed -i -e '1i\import future_annotations;future_annotations.register()'

# Change supported python version to >=3.6 for 3ds build
sed -i 's/python_requires=">=3.10",/python_requires=">=3.6",/' 3ds/setup.py

# Install all pip dependencies to temporary directory
(cd 3ds/ && pip install -t . -e .)

# Remove `from __future__ import annotations` from all python files (doesn't exist in 3.6)
find 3ds/ -type f -name '*.py' -print0  | xargs -0 sed -i -e '/from __future__ import annotations/d'

# Install the backport of `from __future__ import annotations`
pip install -t "3ds" future-annotations

(cd C:\\Users\\Mike\\AppData\\Roaming\\Citra\\sdmc && rm -rf !(in.nds|lib|main.py))
mv 3ds/* "C:\\Users\\Mike\\AppData\\Roaming\\Citra\\sdmc"
