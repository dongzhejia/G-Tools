#!/usr/bin/env python
# coding=utf-8
# Filename: dict2indices.py
# :   
# Description: 生成indice字典

import os
import sys
import importlib
importlib.reload(sys)
# sys.setdefaultencoding('utf8')

def convert_anim_to_index(root, save_key, anim_filename):
    componentArr = []
    index_dict = {}
    traverse_anim(root, anim_filename, componentArr)
    index_dict[save_key] = {}
    index_dict[save_key]['globalItems'] = []
    index_dict[save_key]['libItems'] = componentArr
    return index_dict

def traverse_anim(root, anim_filename, componentArr):
    for child in root:
        for key in child.findall('key'):
            if key.text.endswith('_' + anim_filename):
                componentArr.append(key.text)
        if child.getchildren() > 0:
            traverse_anim(child, anim_filename, componentArr)

def convert_texture_to_index(plist, plistPath):
    componentArr = []
    index_dict = {}
    traverse_texture(plist, componentArr)
    index_dict['items'] = componentArr
    index_dict['texture'] = os.path.join(
        os.path.dirname(plistPath),
        plist["metadata"]["textureFileName"])
    return index_dict

def traverse_texture(plist, componentArr):
    for key in plist["frames"]:
        componentArr.append(key)
