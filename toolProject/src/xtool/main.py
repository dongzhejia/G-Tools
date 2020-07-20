#!/usr/bin/env python
# coding=utf-8
# Filename: main.py
# :   

# http://www.infoq.com/cn/articles/Python-writing-module

# xtool = ..

import os
import sys
import pkg_resources
import importlib

importlib.reload(sys)
# sys.setdefaultencoding("utf-8")

# Append `external` sub-directory to the import search path
sys.path.append(pkg_resources.resource_filename(__name__, "external"))

from .cmda import logutil, XConfig, cmdInit, cmdConfig, cmdTarget, cmdDotask, cmdCleanup
logger = logutil.getLogger()

# Preload configs if it exists.
# Logger format may change if "xtool.logger.format" is defined.
xcfg = XConfig.getXConfig(".", True)

############################################################

import click
from .version import VERSION

@click.group()
@click.help_option('--help', '-h', help='显示帮助信息并退出')
@click.version_option(VERSION, '--version', '-v', help='显示版本信息并退出')
@click.pass_context
def xmain(ctx, **arguments):
    pass

xmain.add_command(cmdInit.main, "init")
xmain.add_command(cmdConfig.main, "config")
xmain.add_command(cmdTarget.main, "target")
xmain.add_command(cmdDotask.main, "dotask")
xmain.add_command(cmdCleanup.main, "clean")

# alias xdo="xtool dotask"
xdo = cmdDotask.main

############################################################

# Inject 'xtool' into the python builtins
import builtins

# Import all builtin actions
# from actions import *

cmdDotask.setupTaskCommands()
############################################################

if __name__ == '__main__':
    # outputdir = xcfg.getValue("xtool", "outputdir")
    # if not outputdir or not os.path.isabs(outputdir):
    #     cmdInit.main()

    xmain()
    # xmain(prog_name="xtool")
