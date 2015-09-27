import os.path
from setuptools import setup, find_packages
import pysnake


def long_description():
    here = os.path.dirname(os.path.abspath(__file__))
    return open(os.path.join(here, 'README.rst')).read()

version = pysnake.__version__

setup(
    name="pysnake",
    version=version,
    description='A curses-based cross-python version of Snake with zoom and rewind modes',
    long_description=long_description(),
    url='https://github.com/otov4its/pysnake',
    license='MIT',
    author='Stanislav Otovchits',
    author_email='otov4its@gmail.com',

    packages=find_packages(),
    entry_points={
        'console_scripts': ['pysnake = pysnake.__main__:main']
    },

    keywords=['snake', 'game', 'zoom', 'rewind'],
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Console :: Curses',
        'Intended Audience :: Developers',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: MIT License',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 3',
        'Topic :: Games/Entertainment',
    ],
)