#!/bin/sh
rm -rf dist
python setup.py sdist
python setup.py bdist_wheel
python setup.py bdist_egg
gpg  --detach-sign -a dist/*.gz
gpg  --detach-sign -a dist/*.egg
gpg  --detach-sign -a dist/*.whl
echo run: twine upload dist/\*

