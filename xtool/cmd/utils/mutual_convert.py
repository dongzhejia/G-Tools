#!/usr/bin/env python
# coding=utf-8
# Filename: mutual_convert.py
# :   
# Description: 数据格式的相互转换

import os
import json
import plistlib

import sys
import importlib
importlib.reload(sys)

# json dumps/dump loads/load 有所不同
# 前者操作字符串 后者操作文件
def convert_dict_to_json(json_dict):
	separators = (",", ":")
	json_str = json.dumps(json_dict, ensure_ascii=False, separators=separators)
	return json_str

def convert_json_to_dict(json_str):
	json_dict = json.loads(json_str)
	return json_dict

def write_dict_to_json(json_dict, export_file):
	with open(export_file, 'w+') as fp:
		fp.write(convert_dict_to_json(json_dict))

def write_dict_to_plist(plist_dict, export_file):
	try:
		plistlib.writePlist(plist_dict, export_file)
	except Exception as e:
		raise e
	else:
		pass

