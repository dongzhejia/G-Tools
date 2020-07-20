#!/usr/bin/env python
# coding=utf-8
# Filename: SpineTask.py
# :   

import os
import shutil
import types
import yaml
import json
from multiprocessing import Process, Manager, Lock
from xtool.core import XConfig
from Cheetah.Template import Template

fileTemplate = '''\
local data = {
    #set $result = ''
    #for skel, plists in $data.items()
        #set $cell = '{'
        #for $plist in $plists
            #set $cell = $cell + '\"' + $plist + '\",'
        #end for
        #set $cell = $cell[:-1]
        #set $cell = '[\"' + $skel + '\"] = ' +  $cell
        #set $cell = $cell + '},\\n        '
        #set $result = $result + $cell
    #end for
        #set $result = $result[:-10]
        $result
}
return data\
'''

class SpineTask(XTool.BaseTask):
    def __init__(self, name, ctx):
        super(SpineTask, self).__init__(name, ctx)
        self.lock = Lock()

    def execAction(self, taskItem, inputs, outputs):
        with self.lock:
            skelFilePath = self.getPath(inputs, ".skel")
            outputSkelFilePath = self.getPath(outputs, ".skel")
            shutil.copyfile(skelFilePath, outputSkelFilePath)
            return True, [outputSkelFilePath]
        return False, None

    #获得json或者atlas的输出路径
    def getPath(self, outputs, ex):
        for x in outputs:
            if os.path.splitext(x)[1] == ex:
                return x

    def getTexture(self, indexData, image):
        data = indexData["paths"]
        for plist, entry in list(data.items()):
            for img in entry["items"]:
                if img == image:
                    return plist
        return None

    def collectAnimInfo(self, jsonFilepath, indexData):
        plistRefArray = set([])
        jsondata = self.getJsonData(jsonFilepath)
        if "skins" in jsondata:
            skinsData = jsondata["skins"]
            for k,v in list(skinsData.items()):
                for k2,v2 in list(v.items()):
                    for k3,v3 in list(v2.items()):
                        if 'type' in v3 and v3['type']!="mesh":
                            continue
                        imgName = os.path.split(k3)[1] + ".png"
                        texture = self.getTexture(indexData, os.path.split(k3)[1] + ".png")
                        if texture != None:
                            plistRefArray.add(texture)
                        else:
                            self.logger.error(imgName + " not founded in index.json, it reference in the " + jsonFilepath + "!")
                            return None
        return plistRefArray

    def getJsonData(self, filepath):
        fs = open(filepath,'r')
        sz = json.load(fs)
        fs.close()
        jsonString = json.dumps(sz)
        jsondata = json.loads(jsonString)
        return jsondata

    def writeFile(self, data, filepath):
        parentDir = os.path.split(filepath)[0]
        if not os.path.exists(parentDir):
            os.makedirs(parentDir)
        file = open(filepath, "w+")
        content = Template(fileTemplate, searchList = {"data": data})
        file.write(str(content))
        file.close()

    def postAction(self, taskItems):
        logger = XTool.logger
        xcfg = XConfig.getXConfig()
        outputRoot = self.outputdir
        rootPath = xcfg.getProjectRoot()
        depTaskInfo = XTool.getTaskInfo('PackAnimImage') 
        userSettings = xcfg.getProjectSettings("TaskSettings", depTaskInfo["name"])
        if userSettings:
            depTaskInfo = {"settings":userSettings}

        data = {}
        ret = []
        animIndexFilepath = ""
        if "settings" in depTaskInfo:
            settings = depTaskInfo["settings"]
            if "index_name" in settings and "outputdir" in settings:
                animIndexFilepath = os.path.join(outputRoot, settings["outputdir"], settings["index_name"])
        indexData = self.getJsonData(animIndexFilepath)
        for spineTask in taskItems:
            name = spineTask['input'][0]
            fullName = os.path.join(rootPath, name)
            shortName = os.path.split(name)[1]
            plistRefArray = self.collectAnimInfo(fullName, indexData)
            if plistRefArray == None:
                return False, None
            data[spineTask['output'][0]] = plistRefArray
            logger.info("collect [" + shortName +"] information finished")
        outputFilename = os.path.join(outputRoot, "script/assetscript/AnimMainfest.lua")
        self.writeFile(data, outputFilename)
        self.registerExtraOutputFiles(os.path.abspath(outputFilename))
