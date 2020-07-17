#!/usr/bin/env python
# coding=utf-8
# Filename: indices_helper.py
# :   
# Description: 生成indice文件公用的方法

import os
import json
import plistlib
import sys


from .. import logutil
logger = logutil.getLogger()

def check_params(source, export_file, allow_chinese, plistDict, export_format):
    if export_format!='JSON' and export_format!='PLIST':
        logger.error('\'export-file\' must be a \'.json\' or \'.plist\' file')
        return False, plistDict

    for item in source:
        check_contain_chinese(item[0], allow_chinese)

    check_contain_chinese(export_file, allow_chinese)
    return True, plistDict

def check_contain_chinese(check_str, allow_chinese):
    for ch in check_str:
        if '\u4e00' <= ch <= '\u9fff':
            if allow_chinese:
                logger.warning('the path contains Chinese')
            else:
                logger.error('the path contains Chinese')