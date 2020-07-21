#!/usr/bin/env python
# coding=utf-8
# Filename: main.py
# :   

# http://www.infoq.com/cn/articles/Python-writing-module

# tptool = ..

import os
import sys
import pkg_resources
import importlib

importlib.reload(sys)
# sys.setdefaultencoding("utf-8")

# Append `external` sub-directory to the import search path
sys.path.append(pkg_resources.resource_filename(__name__, "external"))

from .cmdsrc import logutil, ToolConfig, cmdInit, cmdConfig, cmdTarget, cmdDotask, cmdCleanup
logger = logutil.getLogger()

# Preload configs if it exists.
# Logger format may change if "tptool.logger.format" is defined.
xcfg = ToolConfig.getToolConfig(".", True)

############################################################

import click
from .version import VERSION

@click.group()
@click.help_option('--help', '-h', help='显示帮助信息并退出')
@click.version_option(VERSION, '--version', '-v', help='显示版本信息并退出')
@click.pass_context
def tpmain(ctx, **arguments):
    pass

tpmain.add_command(cmdInit.main, "init")
tpmain.add_command(cmdConfig.main, "config")
tpmain.add_command(cmdTarget.main, "target")
tpmain.add_command(cmdDotask.main, "dotask")
tpmain.add_command(cmdCleanup.main, "clean")

# alias xdo="tptool dotask"
tpdo = cmdDotask.main

############################################################

# Inject 'tptool' into the python builtins
import builtins

# Import all builtin actions
# from actions import *

cmdDotask.setupTaskCommands()
############################################################

if __name__ == '__main__':
    tpmain()
    # tpmain(prog_name="tptool")