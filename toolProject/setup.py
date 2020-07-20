
from setuptools import setup, find_packages
from distutils.core import setup

setup(
    name='xtool',
    version='1.0',
    # py_modules=['main'],
    packages = find_packages("src"),
    package_dir = {'':'src'},

    install_requires = [
        # 'python3>=3.4',
        'click>=5.1',
        'PyYaml==5.1',
        'Pillow>=6.0.0',
    ],

    entry_points = {
        'console_scripts': [
            'xtool = xtool.main:xmain',
            'xdo = xtool.main:xdo'
        ],
    },
)