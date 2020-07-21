#!/usr/bin/env python
# coding=utf-8
# Filename: texture_indices_action.py
# :   
# Description: File description

import os, os.path
import json
import click
import plistlib
from . import dict2indices as D2I
from . import mutual_convert as MC
from . import indices_helper as IH

import sys
import importlib
importlib.reload(sys)


from .. import logutil
logger = logutil.getLogger()

# 接收的参数是一个字符串
def find_plist(itemList, outputDir, plistDict):
    for item in itemList:
        add_mapping(item[0], outputDir, plistDict)

def add_mapping(wholePath, outputDir, plistDict):
    plist = plistlib.readPlist(wholePath)
    picArr = []
    try:
        save_key = ''
        save_key = os.path.relpath(wholePath, outputDir)
        plistPath = save_key
        index_dict = D2I.convert_texture_to_index(plist, plistPath)
        plistDict[save_key] = index_dict
    except Exception as e:
        raise e
    return plistDict

def run(source, export_file, index_fmt, outputDir, allow_chinese):
    indicesFile = {}
    export_format = index_fmt.upper()
    check_ok, indicesFile = IH.check_params(source, \
                                          export_file, \
                                          allow_chinese, \
                                          indicesFile, \
                                          export_format)
    check_ok = True
    plistDict = {}
    if 'meta' not in indicesFile:
        indicesFile['meta'] = {'version':'1.0', 'indexType':'ImageAtlas'}
    if check_ok:
        find_plist(source, outputDir, plistDict) # todo
        indicesFile['paths'] = plistDict
        if export_format == 'JSON':
            MC.write_dict_to_json(indicesFile, export_file)
            plistDict = None
            indicesFile = None
        elif export_format == 'PLIST':
            MC.write_dict_to_plist(indicesFile, export_file)
            plistDict = None
            indicesFile = None

@click.command()
@click.option('--export-file', '-ef', required = True, help = '导出的目标文件(.json or .plist)')
@click.option('--allow-chinese', '-ac', is_flag = True, help = '是否允许中文路径')
@click.option('--outputdir', '-o', help = '输出目录')
@click.argument('source', required = True, nargs = -1) # 导出的源路经
def excute(**args):
    source = args['source']
    export_file = args['export_file']
    outputDir = args['outputdir']
    allow_chinese = args['allow_chinese']
    run(source, export_file, outputDir, allow_chinese)

if __name__ == '__main__':
    excute()
