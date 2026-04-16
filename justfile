set shell := ["nu", "-c"]

main *args:
    @ python dome/main.py {{args}}

test:
    @ pytest

install:
    @ pip install -e .

release version:
    @ git commit -am {{version}}
    @ git tag {{version}}
    @ rm -rf dist
    @ python -m build
    @ python -m twine upload dist/* --verbose