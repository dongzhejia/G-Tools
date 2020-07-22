#!/usr/bin/env python
# coding=utf-8
# Filename: cmdCleanup.py
# :   

import os, sys, shutil
import click

from . import common
from . import logutil, ToolConfig

def cleanDirectory(rootdir):
    filelist = os.listdir(rootdir)
    for f in filelist:
        filepath = os.path.join(rootdir, f)
        if os.path.isfile(filepath):
            os.remove(filepath)
        elif os.path.isdir(filepath):
            shutil.rmtree(filepath, True)

@click.command()
@click.option("--all", is_flag=True, default=None, help='清空整个输出目录')
@click.option("--outputdir", default=None, help='重定义输出目录')
@click.option("--rm-dir", is_flag=True, default=False, help='删除目录而非清空目录')
@click.option("--path", "-p", multiple=True, help='清理指定路径')
def main(**arguments):
    '''清空图片输出目录'''

    xcfg = ToolConfig.getToolConfig()
    outputdir = common.ensure_outputdir(xcfg, arguments)
    if not os.path.isdir(outputdir):
        logutil.echo('ERROR: "%s"不存在(或不是目录)' % (outputdir))
        sys.exit(-1)

    cleanall = arguments["all"]
    cleanups = []
    if cleanall!=True:
        subdirs = arguments["path"]
        if subdirs:
            cleanups.extend(subdirs)
        if not cleanups:
            if not click.confirm('未指定子目录或清空任务。确定清除全部输出目录?', default=False):
                sys.exit(0)
            cleanall = True

    rmdir = arguments["rm_dir"]
    outputdir = os.path.abspath(outputdir)
    if cleanall:
        logutil.echo('清空整个输出目录(%s)...' % (outputdir,))
        if rmdir:
            shutil.rmtree(outputdir, True)
        else:
            cleanDirectory(outputdir)
    elif cleanups:
        for name in cleanups:
            fullpath = os.path.join(outputdir, name)
            if os.path.isfile(fullpath):
                logutil.echo('删除文件：%s (%s)' % (name,fullpath))
                os.remove(fullpath)
            elif os.path.isdir(fullpath):
                logutil.echo('清空目录：%s (%s)' % (name,fullpath))
                if rmdir:
                    shutil.rmtree(fullpath, True)
                else:
                    cleanDirectory(fullpath)
            else:
                logutil.echo('跳过不存在的路径：%s (%s)' % (name,fullpath))
