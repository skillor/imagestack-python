rmdir /s /q build
rmdir /s /q dist
python setup.py sdist bdist_wheel
python -m twine upload "dist/*" -u "skillor"