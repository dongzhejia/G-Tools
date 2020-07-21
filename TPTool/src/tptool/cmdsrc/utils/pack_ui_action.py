#!/usr/bin/env python
# coding=utf-8
# Filename: pack_ui_action.py
# :   
# Description: File description

import os
import click
import subprocess
from subprocess import Popen, PIPE

import sys
import importlib
importlib.reload(sys)

from .. import logutil
logger = logutil.getLogger()


def pack_command(pic_list, config):
	pic_arr = []
	for pic in pic_list:
		config.append(pic)
	# for key in config:
		# logger.info("key - "+key)
		
	p = subprocess.Popen(config, stdin = PIPE, stdout = PIPE, stderr = PIPE)
	returntuple = p.communicate()
	stdoutdata = returntuple[0]
	stderrdata = returntuple[1]
	# if p.returncode != 0:
		# XTool.logger.error(stderrdata)
	return p.returncode == 0, stdoutdata

def find_same_file(pic_list, filename):
	for i in range(0, len(pic_list)):
		val = pic_list[i]
		fname = os.path.split(val)[1]
		if filename==fname:
			return i, val
	return None, None

def run(source, config, keep_path):
	pic_list = []
	if keep_path == True or keep_path == 'True':
		pic_list = source
	else:
		for src in source:
			if os.path.isfile(src) and (src.endswith('.png') or src.endswith('.jpg')):
				filename = os.path.split(src)[1]
				index, same_file = find_same_file(pic_list, filename)
				if same_file:
					pic_list.remove(same_file)
				pic_list.append(src)
			elif os.path.isdir(src):
				for dirpath, dirnames, filenames in os.walk(src):
					for filename in filenames:
						if filename.endswith('.png') or filename.endswith('.jpg'):
							index, same_file = find_same_file(pic_list, filename)
							if same_file:
								pic_list.remove(same_file)
							pic_list.append(os.path.join(dirpath, filename))
	return pack_command(pic_list, config)

@click.command()
@click.option('--config', required = True, help = 'TexturePacker 执行的参数')
@click.option('--keep-path/--no-keep-path', default = False, help = 'plist文件中是否保留路径')
@click.argument('source', required = True, nargs = -1) # 源路径
def excute(**options):
	source = options['source']
	config = options['config']
	keep_path = options['keep_path']
	run(source, config, keep_path)

if __name__ == '__main__':
	excute()
