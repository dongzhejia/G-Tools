#!/usr/bin/env python
# coding=utf-8
# Filename: anim_indices_action.py
# :   
# Description: File description

import os
import click
import xml.etree.cElementTree as ET
from . import dict2indices as D2I
from . import mutual_convert as MC
from . import indices_helper as IH

import sys
import importlib
importlib.reload(sys)
# sys.setdefaultencoding('utf8')

# plistDict = {}
# export_format = 'JSON'  # 'JSON' or 'PLIST'

# 接收的参数是一个字符串列表
def find_animxml(srcs, outputDir, plistDict, export_format):
	for src in srcs:
		find_animxml_2(src, outputDir, plistDict, export_format)

# 接收的参数是一个字符串
def find_animxml_2(src, outputDir, plistDict, export_format):
	if os.path.isfile(src) and src.endswith('.animxml'): #and not src.endswith('image.animxml'):
		componentArr = []
		try:
			tree = ET.parse(src)
			root = tree.getroot()
			fileName = os.path.basename(src)[0:-8] # 截取路径中的文件名并去掉末尾的'.animxml'扩展名
			add_mapping(fileName, componentArr, root, src, outputDir, plistDict, export_format)
		except Exception as e:
			raise e
		else:
			pass
	elif os.path.isfile(src) and not src.endswith('.animxml'):
		pass
	elif os.path.isdir(src):
		for _file in os.listdir(src):
			wholePath = os.path.join(src, _file)
			find_animxml_2(wholePath, outputDir, plistDict, export_format)
	# elif os.path.isfile(src) and src.endswith('image.animxml'):
	# 	pass
	else:
		click.secho('Warning: ' + src + ' is not a right path', fg = 'green')

def add_mapping(fileName, componentArr, root, wholePath, outputDir, plistDict, export_format):
	try:
		save_key = ''
		save_key = os.path.relpath(wholePath, outputDir)
		index_dict = D2I.convert_anim_to_index(root, save_key, fileName)
		plistDict[save_key] = index_dict[save_key]
	except Exception as e:
		raise e
	click.echo(fileName+' add finish!')

def run(source, export_file, outputDir, allow_chinese):
	indicesContent = {}
	export_format = 'JSON'
	check_ok, indicesContent, export_format = IH.check_params(source, \
														export_file, \
														allow_chinese, \
														indicesContent, \
														export_format)
	plistDict = {}
	if 'indices' in indicesContent:
		plistDict = indicesContent['indices']
	if 'fileinfo' not in indicesContent:
		indicesContent['fileinfo'] = {'version':'1.0', 'indexType':'MoveClip', 'xmlDataFormat':'bobj'}
	if check_ok:
		find_animxml(source, outputDir, plistDict, export_format)
		indicesContent['indices'] = plistDict
		if export_format == 'JSON':
			MC.write_dict_to_json(indicesContent, export_file)
			plistDict = None
			indicesContent = None
		elif export_format == 'PLIST':
			MC.write_dict_to_plist(indicesContent, export_file)
			plistDict = None
			indicesContent = None

@click.command()
@click.option('--export-file', '-ef', required = True, help = '导出的目标文件(.json or .plist)')
@click.option('--allow-chinese', '-ac', is_flag = True, help = '是否允许中文路径')
@click.option('--outputdir', '-o', help = '输出目录') # Resources
@click.argument('source', required = True, nargs = -1) # 导出的源路经
def excute(**args):
	source = args['source']
	export_file = args['export_file']
	outputDir = args['outputdir']
	allow_chinese = args['allow_chinese']
	run(source, export_file, outputDir, allow_chinese)

if __name__ == '__main__':
	excute()
