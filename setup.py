#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
    setup
    ~~~~
    rain-shell-scripter 用Python加持Linux Shell脚本，编写CSV文件即可完美解决脚本中的返回值、数值运算、错误处理、流程控制难题~
    :copyright: (c) 2020 by Fifi Lyu.
    :license: MIT, see LICENSE for more details.
"""

from setuptools import setup
from os.path import join, dirname
from rain_shell_scripter import __version__

with open(join(dirname(__file__), 'requirements.txt'), 'r', encoding='utf-8') as f:
    pkgs = f.read()
    print('pkgs', pkgs)
    install_requires = pkgs.split("\n")

setup(
    name='rain-shell-scripter',
    version=__version__,
    url='https://github.com/fifilyu/rain-shell-scripter',
    license='MIT',
    author='Fifi Lyu',
    author_email='fifilyu@gmail.com',
    description="用Python加持Linux Shell脚本，编写CSV文件即可完美解决脚本中的返回值、数值运算、错误处理、流程控制难题~",
    long_description=open('README.md', encoding='utf-8').read(),
    long_description_content_type="text/markdown",
    py_modules=['rain_shell_scripter'],
    entry_points={
        "console_scripts": [
            "rain_shell_scripter=rain_shell_scripter:main"
        ],
    },
    zip_safe=False,
    include_package_data=True,
    platforms='Linux',
    install_requires=install_requires,
    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ]
)
