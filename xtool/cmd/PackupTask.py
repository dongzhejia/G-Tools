#!/usr/bin/env python
# coding=utf-8
# Filename: PackupTask.py
# :   

import os
import sys
import re
import math
import shutil
import plistlib
from multiprocessing import Process, Manager, Lock
from .utils import pack_ui_action as pua
from .utils import texture_indices_action as tia
import subprocess
from subprocess import Popen, PIPE

from . import XTask,logutil, XConfig
logger = logutil.getLogger()

# xcfg = XTool.XConfig.getXConfig(".", True)

texturepacker_params = {
    'scale': 'int',
    'width': 'int',
    'height': 'int',
    'opt': 'string',
    'padding': 'int',
    'extrude': 'int',
    'format': 'string',
    'max-width': 'int',
    'max-height': 'int',
    'max-size' : 'int',
    'trim-margin': 'int',
    'auto-sd': "boolean",
    'trim-mode': 'string',
    'algorithm': 'string',
    'multipack': 'boolean',
    'scale-mode': 'string',
    'shape-padding': 'int',
    'trim-threshold': 'int',
    'border-padding': 'int',
    'etc1-quality': 'string',
    'etc2-quality': 'string',
    'pvr-quality': 'string',
    'texture-format': 'string',
    'force-squared': 'boolean',
    'size-constraints': 'string',
    'enable-rotation': "boolean",
    'disable-rotation': "boolean",
    'trim-sprite-names': 'boolean',
    'force-word-aligned': 'boolean',
    'force-identical-layout': 'boolean',
    'disable-auto-alias': 'boolean',
    'force-publish': 'boolean',
    'dither-type': 'string',
    'premultiply-alpha': 'boolean',
    'alpha-handling': 'string',
    'dither-fs-alpha': 'boolean',
    'jpg-quality': 'int',
    'png-opt-level': 'int',
    'dpi': 'int'
}

class PackupTask(XTask.BaseTask):
    def __init__(self, name, ctx):
        super(PackupTask, self).__init__(name, ctx)
        self.lock = Lock()
        self.manager = Manager()
        self.recommendDataExt = False
        self.recommendTextureExt = False

    def execAction(self, taskItem, inputs, outputs):
        options = taskItem["options"]

        outputsCloneRGB = {}
        outputsCloneRGB = list(outputs)
        optionsCloneRGB = {}
        optionsCloneRGB = dict(optionsCloneRGB, **options)

        outputsCloneA = {}
        outputsCloneA = list(outputs)
        outputsCloneA[0] = outputsCloneA[0] + "@alpha"
        outputsCloneA[1] = outputsCloneA[1] + "@alpha"
        optionsCloneA = {}
        optionsCloneA = dict(optionsCloneA, **options)

        hasOpt = options.get('opt', "none")
        if hasOpt == "ETC1_RGB_ETC1_A":
            # ETC1_RGB
            optionsCloneRGB["opt"] = "ETC1_RGB"
            optionsCloneRGB["disable-auto-alias"] = True
            isOK1, ret1 = self.excuteTpWork(taskItem, inputs, outputsCloneRGB, optionsCloneRGB, True)

            # ETC_A
            optionsCloneA["opt"] = "ETC1_A"
            optionsCloneA["disable-auto-alias"] = True
            isOK2, ret2 = self.excuteTpWork(taskItem, inputs, outputsCloneA, optionsCloneA, False)
            if isOK1 and isOK2:
                ret2 = ret1 + ret2
                if len(ret2) > 0:
                    return True, ret2
            else:
                return False, None
        elif hasOpt == "RGB565_A8":
            # RGB565
            optionsCloneRGB["opt"] = "RGB565"
            optionsCloneRGB["dither-type"] = "FloydSteinberg"
            optionsCloneRGB["disable-auto-alias"] = True
            isOK1, ret1 = self.excuteTpWork(taskItem, inputs, outputsCloneRGB, optionsCloneRGB, True)

            #A8
            optionsCloneA["opt"] = "ALPHA"
            optionsCloneA["disable-auto-alias"] = True
            isOK2, ret2 = self.excuteTpWork(taskItem, inputs, outputsCloneA, optionsCloneA, False)

            if isOK1 and isOK2:
                ret2 = ret1 + ret2
                if len(ret2) > 0:
                    return True, ret2
            else:
                return False, None
        else:
            isOK1, ret1 = self.excuteTpWork(taskItem, inputs, outputs, options, True)
            if isOK1:
                return True, ret1
            else:
                return False, None
        return False, None

    def excuteTpWork(self, taskItem, inputs, outputs, options, writeDataFile):
        source = inputs
        config = []
        outputs = self.processOutput(outputs, options)
        boolTrueValues = ["", "True", "True", "true", True]
        config.append('TexturePacker')
        config.append('--data')
        config.append(outputs[0])
        config.append('--sheet')
        config.append(outputs[1])
        for key in list(options.keys()):
            if key in texturepacker_params:
                if texturepacker_params[key]!="boolean":
                    config.append('--'+key)
                    config.append(str(options[key]))
                else:
                    if options[key] in boolTrueValues:
                        config.append('--'+key)

        config = self.addIgnore(taskItem, config)

        if "keep-path" in list(options.keys()):
            keep_path = options["keep-path"]
            if keep_path in boolTrueValues:
                keep_path = True
            else:
                keep_path = False
        else:
            keep_path = False

        isOK, tpOutputs = pua.run(source, config, keep_path)
        if isOK == False:
            return False, []

        isOK = self.pngquant(outputs, options)
        if not isOK:
            return False, []
        # add scale to plist
        if 'scale' in options:
            scale = options['scale']
            self.writeScaleToPlist(tpOutputs, scale)
        result = self.obtainTpOutputs(tpOutputs, writeDataFile)
        ret = self.reviseTextureDataFile(result)
        return True, ret

    def pngquant(self, outputs, options):
        isApplyPngquant = False
        if "texture-format" in options:
            textureFormat = options["texture-format"]
            if textureFormat == "png":
                isApplyPngquant = True
        else:
            isApplyPngquant = True

        qualityValue = 100
        if "png-quality" in options:
            qualityValue = options["png-quality"]
        else:
            qualityValue = 100
        if isApplyPngquant and qualityValue != 100:
            args = ["pngquant", "-o", outputs[1], "-f", outputs[1], "--speed", "3", "--quality", str(qualityValue)+"-100"]
            p = subprocess.Popen(args, stdin = PIPE, stdout = PIPE, stderr = PIPE)
            returntuple = p.communicate()
            #品质限制，转化成功返回0
            #如果转化后的品质低于最低品质的限制，返回99并且不保存转化后的png
            if p.returncode != 0 and p.returncode != 99:
                return False
        return True

    # dataFile 0
    # textureFile 1
    def obtainTpOutputs(self, tpOutputsString, writeDataFile):
        ret = []
        path = ""

        splitStringArray = str(tpOutputsString, encoding='utf-8')
        splitStringArray = splitStringArray.split('\n')
        for line in splitStringArray:
            if line.find('Writing sprite sheet to ')!=-1:
                ret.insert(0, [line.replace('Writing sprite sheet to ',''), 1])
            elif line.find('Writing data for cocos2d to ')!=-1:
                path = line.replace('Writing data for cocos2d to ','')
                if not writeDataFile:
                    os.remove(path)
                else:
                    ret.insert(0, [path, 0])
            elif line.find('Writing data for cocos2d to ') == -1 \
            and line.find('Writing sprite sheet to ') == -1 and line.find('Writing ') != -1:
                path = line.replace('Writing ','')
                if not writeDataFile:
                    os.remove(path)
                else:
                    ret.insert(0, [path, 0])
        return ret

    def preAction(self, taskItems):
        return True

    def postAction(self, taskItems):
        skip_index = self.context.getOptionValue("skip_index", False)
        if skip_index:
            return True
        indexName = None
        index_fmt = "json"
        if "index_name" in self.settings:
            indexName = self.settings["index_name"]
        if not indexName:
            indexName = "index.json"
        if "index_fmt" in self.settings:
            index_fmt = self.settings["index_fmt"]

        with self.lock:
            resources = []
            for item in taskItems:
                resources.append(item["abs_output"])
            export_file = os.path.join(self.taskoutdir, indexName)
            self.registerExtraOutputFiles(export_file)

            tia.run(resources, export_file, index_fmt, self.outputdir, True)
        return True

    def targetFiles(self, outputs, taskItem):
        options = taskItem["options"]
        standardExts = self.getStandardExt(options)
        outputs = [x.format(n = "{n}", n1 = "{n1}", dataExt= standardExts[0], imgExt = standardExts[1]) for x in outputs]
        if "multipack" in options:
            return [x.format(n = 0, n1 = 1) for x in outputs]
        return outputs

    def addIgnore(self, taskItem, config):
        if "ignore" in taskItem:
            ignore_files = taskItem["ignore"]
        else:
            ignore_files = []
        basepath = os.path.join(self.projroot, taskItem["basepath"])

        # ignorefile
        if ignore_files and len(ignore_files) > 0:
            for value in ignore_files:
                wholepath = os.path.join(basepath, value)
                if os.path.isfile(wholepath):
                    config.append('--ignore-files')
                    config.append(os.path.abspath(wholepath))
                elif os.path.isdir(wholepath):
                    for dirpath, dirnames, filenames in os.walk(wholepath):
                        for filename in filenames:
                            path = os.path.abspath(os.path.join(dirpath, filename))
                            config.append('--ignore-files')
                            config.append(path)
        return config

    def writeScaleToPlist(self, tpOutputs, scale):
        outputs = tpOutputs.split("\n")
        for output in outputs:
            items = output.split(" ")
            temppath = items[len(items)-1]
            if temppath.endswith(".plist") and os.path.exists(temppath):
                plistFile = temppath
                scaleNum = float(scale)
                if scaleNum == math.floor(scaleNum):
                    scaleNum = int(scaleNum)
                if scaleNum == 1:
                    return
                plistDict = plistlib.readPlist(plistFile)
                plistDict.metadata.scale = scaleNum
                plistlib.writePlist(plistDict, plistFile)

    def getStandardExt(self, options):
        imageConfig = {"png":"png", "png8":"png", "pvr2ccz":"pvr.ccz","pvr3ccz":"pvr.ccz",
        "pvr2":"pvr", "pvr2gz":"pvr.gz", "jpg":"jpg",
        "bmp":"bmp", "tga":"tga", "tiff":"tiff",
        "pkm":"pkm", "ppm_ascii":"ppm", "ppm_binary":"ppm" }
        textureFormat = "png"
        if "texture-format" in options:
            textureFormat = options["texture-format"]
            return ["plist", imageConfig[textureFormat]]
        return ["plist", "png"]

    def processOutput(self, outputs, options):
        dataFilepath = outputs[0]
        textureFilepath = outputs[1]
        dataExt = dataFilepath[dataFilepath.index("."):]
        textureExt = textureFilepath[textureFilepath.index("."):]
        standardExts = self.getStandardExt(options)
        if "{dataExt}" in dataFilepath:
            self.recommendDataExt = True
            outputs[0] = dataFilepath.format(n = "{n}", dataExt = standardExts[0])
        else:
            self.recommendDataExt = False
            if ("." + standardExts[0]) == dataExt:
                self.dataAppendExt = ""
            else:
                self.dataAppendExt = "." + standardExts[0]
                outputs[0] = dataFilepath + self.dataAppendExt
        if "{imgExt}" in textureFilepath:
            self.recommendTextureExt = True
            outputs[1] = textureFilepath.format(n = "{n}", imgExt = standardExts[1])
        else:
            self.recommendTextureExt = False
            if ("." + standardExts[1]) == textureExt:
                self.imgAppendExt = ""
            else:
                self.imgAppendExt = "." + standardExts[1]
                outputs[1] = textureFilepath + self.imgAppendExt
        return outputs

    def reviseTextureDataFile(self, input_):
        ret = []
        textureKV = {}
        dataFiles = []
        index = 0
        for value in input_:
            if self.recommendDataExt == False and value[1] == 0:
                dataFilepath = value[0]
                if self.dataAppendExt != "":
                    dataFilepath = value[0][:-len(self.dataAppendExt)]
                    os.rename(value[0], dataFilepath)
                if self.imgAppendExt != "":
                    dataFiles.append(dataFilepath)
                ret.append(dataFilepath)
            if self.recommendTextureExt == False and value[1] == 1:
                textureFilepath = value[0]
                if self.imgAppendExt != "":
                    textureFilepath = value[0][:-len(self.imgAppendExt)]
                    os.rename(value[0], textureFilepath)
                    textureKV[os.path.split(value[0])[1]] = os.path.split(textureFilepath)[1]
                else:
                    textureKV[os.path.split(value[0])[1]] = os.path.split(value[0])[1]
                ret.append(textureFilepath)
            index = index + 1
        for value in dataFiles:
            data = plistlib.readPlist(value)
            key = data['metadata']['realTextureFileName']
            if data['metadata']['realTextureFileName'] != textureKV[key]:
                data['metadata']['realTextureFileName'] = textureKV[key]
                data['metadata']['textureFileName'] = textureKV[key]
                plistlib.writePlist(data, value)
        return ret
