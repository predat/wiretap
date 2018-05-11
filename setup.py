import os
from setuptools import setup, find_packages


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


setup(
    name="wiretap",
    version="0.1.0",
    author="Sylvain Maziere",
    author_email="sylvain@predat.fr",
    url="https://github.com/predat/wiretap",
    entry_points={'console_scripts': ['wiretap=wiretap.cli:run']},
    package_dir={'': 'src'},
    packages=find_packages('src', exclude=['*.tests.*', 'tests.*', 'tests']),
    description="Python wrapper to the Wiretap Client API",
    install_requires=['PyYAML'],
    long_description=read('README.md'),
    license="LICENSE.txt",
)
