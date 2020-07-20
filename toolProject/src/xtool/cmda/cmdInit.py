#!/usr/bin/env python
# coding=utf-8
# Filename: cmdInit.py
# :   

import os, sys
import click
import pkg_resources

from . import logutil, XConfig
logger = logutil.getLogger()

def _updateXCfgWithArgs(xcfg, args):
    optnames = ("outputdir", "projroot", "cachedir")
    for name in optnames:
        if name in args and args[name]!="":
            xcfg.setValue("xtool", name, args[name])

@click.command()
@click.option('--preset', help='预置工具集名称。"?"可用于查询所有工具集', required=False)
@click.option('--outputdir', help='默认输出目录',)
@click.option('--projroot', help='默认项目目录',)
# @click.option('--cachedir', help='默认缓存目录',)
#     prompt=u'选择默认输出目录', default=u'%(XPROJROOT)s/Resources', show_default=False)
def main(**args):
    '''创建或重置资源库'''

    if not args["outputdir"]:
        args["outputdir"] = click.prompt('选择默认输出目录',)
    if not args["projroot"]:
        args["projroot"] = click.prompt('选择默认项目目录',)
    # if not args["cachedir"]:
    #     args["cachedir"] = click.prompt('选择默认缓存目录',
    #                                     default='%(XCFGDIR)s/cache')

    xcfg = XConfig.getXConfig(".", True)
    alreadyInited = (xcfg.config!=None)
    xcfg.createOrReCreateProject(".")
    _updateXCfgWithArgs(xcfg, args)
    xcfg.saveConfigs()
    xcfgdir = xcfg.getEnvVariable("XCFGDIR")
    if alreadyInited:
        logutil.echo("已重置资源库(%s)" % (xcfgdir))
    else:
        logutil.echo("已创建资源库(%s)" % (xcfgdir))

if __name__ == '__main__':
    main()