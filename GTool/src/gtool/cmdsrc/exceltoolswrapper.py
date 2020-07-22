#!/usr/bin/env python
# coding=utf-8
# Filename:sqlitetoolswrapper.py
# Author:   
# Description: File description


import os, sys, os.path, shutil
import sys
import time
import click
import yaml
import subprocess
from . import common
from . import logutil, ToolConfig
logger = logutil.getLogger()

from dataTools import dataTools

def svn_update(revision, inputdir, logger):
    if revision == None:
        return 0
    cmdParams = ['svn', 'update']
    cmdParams.extend(['-r', revision])
    cmdParams.append(str(inputdir))
    returncode = subprocess.call(cmdParams)
    if returncode == 0:
        logger.info('数据表更新成功,版本号:%s' %revision)
    else:
        logger.error('数据表更新到指定版本失败，将使用当前版本')
    return returncode

@click.command()
@click.option('--source', '-s', default='Develop', required=False, help='数据表分支')
@click.option('--revision', '-r', required=False, help='更新数据表到指定版本')
@click.option('--cache/--no-cache', default=True, help='是否使用缓存')
# @click.option('--encrypted/--no-encrypted', default=False, help='是否加密,默认不加密')
# @click.option('--encrypted-key', default=None, help='秘钥,默认使用默认秘钥')
@click.pass_context
def main(ctx, **args):
    '''导出json命令'''
    start_time = time.process_time()

    log_path = args.get('log_path')
    use_cache = args.get('cache')
    encrypted = args.get('encrypted')
    encrypted_key = args.get("encrypted-key")

    xcfg = ToolConfig.getToolConfig(".", True)

    source = args.get('source')

    revision = None
    if 'revision' in args:
        revision = args['revision']
    if svn_update(revision, source, logger) != 0:
        return

    outputdir = xcfg.getValue("gtool", "jsonoutputdir")
    datasetdir = xcfg.getValue("gtool", "jsonprojroot")
    inputdir = os.path.join(datasetdir, source)

    # print("==========================")
    # print(("inputdir = "+str(inputdir)))
    # print(("outputdir = "+str(outputdir)))
    # print(use_cache)
    # print("==========================")

    if not os.path.isdir(inputdir):
        logger.error('无效的数据源目录：%s' % (inputdir,))
        sys.exit(-1)

    if not os.path.isdir(outputdir):
        logger.error('无效的数据目标目录：%s' % (outputdir,))
        sys.exit(-1)
    
    sqlite_tools = dataTools.DataTools(log_path)
    sqlite_tools.execute_export_json(inputdir, outputdir, 4, (not use_cache))

    end_time = time.process_time()
    logger.info('完成！用时：%ss' % (str(end_time-start_time)))

