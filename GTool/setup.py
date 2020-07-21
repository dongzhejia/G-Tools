
from setuptools import setup, find_packages
from distutils.core import setup

setup(
    name='gtool',
    version='1.0',
    packages = find_packages("src"),
    package_dir = {'':'src'},

    install_requires = [
        # 'python3>=3.4',
        'click>=5.1',
        'PyYaml==3.11',
        'Pillow>=6.0.0',
    ],

    entry_points = {
        'console_scripts': [
            'gtool = gtool.main:tpmain',
            'gdo = gtool.main:gdo'
        ],
    },
)