import os
from setuptools import setup, find_packages


exec(open('version.py').read())


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

# This repo keeps the package modules directly at the repo root (flat layout)
# rather than nested under a pydfs_lineup_optimizer/ subdirectory. package_dir
# maps the 'pydfs_lineup_optimizer' package name to '.' so it still installs
# and imports correctly as `import pydfs_lineup_optimizer`.
setup(
    name='pydfs-lineup-optimizer',
    version=__version__,
    packages=['pydfs_lineup_optimizer'] + ['pydfs_lineup_optimizer.' + p for p in find_packages(exclude=['tests*'])],
    package_dir={'pydfs_lineup_optimizer': '.'},
    url='https://github.com/DimaKudosh/pydfs-lineup-optimizer',
    license='MIT',
    author='Dima Kudosh',
    author_email='dimakudosh@gmail.com',
    description='Tool for creating optimal lineups for daily fantasy sports',
    keywords=['dfs', 'fantasy', 'sport', 'lineup', 'optimize', 'optimizer', 'nba', 'nfl', 'nhl', 'mlb'],
    # numpy/pandas/scipy added for the custom CorrelatedFantasyPointsStrategy
    install_requires=['PuLP==2.4', 'pytz>=2020.5', 'numpy', 'pandas', 'scipy'],
    long_description=read('README.md'),
    long_description_content_type='text/markdown',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: End Users/Desktop',
        'Intended Audience :: Developers',
        'Operating System :: POSIX',
        'Programming Language :: Python',
    ],
)
