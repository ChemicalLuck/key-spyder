del dist\* /q
py -m build
del build\* /q
pip install --upgrade pip
pip install -force-reinstall -vvv .
twine upload dist/*