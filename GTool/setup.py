
from setuptools import setup, find_packages
from distutils.core import setup
# 'python3==3.7.0'

setup(
    name='gtool',
    version='1.0',
    packages = find_packages("src"),
    package_dir = {'':'src'},

    install_requires = [
        'click>=5.1',
        'PyYaml==5.4',
        # 'Pillow>=6.0.0',
        'dataTools>=1.0.1',
        'doit==0.32.0',
    ],

    dependency_links = [
        'http://10.0.4.168:8135/packages/',
    ],

    entry_points = {
        'console_scripts': [
            'gtool = gtool.main:gmain',
            'gdo = gtool.main:gdo',
            'gdataset = gtool.main:gdataset',
        ],
    },
)