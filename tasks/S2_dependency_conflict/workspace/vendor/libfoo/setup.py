from setuptools import setup
setup(
    name="libfoo",
    version="1.2.0",
    py_modules=["libfoo_core"],
    install_requires=["utils>=2.0,<3.0"],
)
