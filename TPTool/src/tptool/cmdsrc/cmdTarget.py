#!/usr/bin/env python
# coding=utf-8
# Filename: cmdTarget.py
# :   

import os
import click
import shutil

from . import predefs, logutil, ToolConfig
logger = logutil.getLogger()

@click.group()
@click.pass_context
def main(ctx, **arguments):
    '''Target管理'''
    pass

# @click.command()
# def _new(**args):
#     u'''创建新Target'''
#     pass

# main.add_command(_new, "new")

@click.command()
@click.argument('target')
def _switch(**args):
    '''切换Target'''
    xcfg = ToolConfig.getToolConfig()
    oldTarget = xcfg.getValue("tptool", "target", predefs.DEFAULT_TARGET)
    newTarget = args["target"]
    if oldTarget==newTarget:
        logutil.echo("Already under the target '%s'" % (oldTarget))
    else:
        if xcfg.setValue("tptool", "target", newTarget):
            shutil.rmtree(os.path.join(xcfg.getCachedir(), oldTarget), True)
            logutil.echo("delete old target cache dir: %s" % oldTarget)
            xcfg.saveConfigs()
            logutil.echo("Switched to target '%s'" % (newTarget))
        else:
            logutil.echo("Failed to switch target. Current target: '%s'" % (oldTarget))

main.add_command(_switch, "switch")

@click.command()
def _status(**args):
    '''查看当前Target信息'''
    xcfg = ToolConfig.getToolConfig()
    target = xcfg.getValue("tptool", "target", predefs.DEFAULT_TARGET)
    logutil.echo(target)

main.add_command(_status, "status")

@click.command()
def _list(**args):
    '''查看当前可选target'''
    logutil.echo(ToolConfig.getToolConfig().getProjectSettings("target"))

main.add_command(_list, "list")
