#-----------------------------------------------------------------------------
# Name:        logArchiveServerGlobal.py
#
# Purpose:     This module is used as a project global config file to set the 
#              constants, parameters and instances which will be used in the 
#              other modules in the project.
#              
# Author:      Yuancheng Liu
#
# Created:     2024/08/21
# Version:     v_0.1.1
# Copyright:   Copyright (c) 2023 LiuYuancheng
# License:     MIT License
#-----------------------------------------------------------------------------
"""
For good coding practice, follow the below naming convention:
    1) Global variables should be defined with initial character 'g'.
    2) Global instances should be defined with initial character 'i'.
    3) Global CONSTANTS should be defined with UPPER_CASE letters.
"""

import os
import sys

print("Current working directory is : %s" % os.getcwd())
DIR_PATH = dirpath = os.path.dirname(os.path.abspath(__file__))
print("Current source code location : %s" % dirpath)
APP_NAME = ('LogArchive', 'Server')

TOPDIR = 'src'
LIBDIR = 'lib'

#-----------------------------------------------------------------------------
# find the lib folder for importing the library modules
idx = dirpath.find(TOPDIR)
gTopDir = dirpath[:idx + len(TOPDIR)] if idx != -1 else dirpath   # found it - truncate right after TOPDIR
# Config the lib folder 
gLibDir = os.path.join(gTopDir, LIBDIR)
if os.path.exists(gLibDir): sys.path.insert(0, gLibDir)

#-----------------------------------------------------------------------------
# Init the configure file loader.
#Load the agent config file
import ConfigLoader
CONFIG_FILE_NAME = 'ServerConfig.txt'
gGonfigPath = os.path.join(dirpath, CONFIG_FILE_NAME)
iConfigLoader = ConfigLoader.ConfigLoader(gGonfigPath, mode='r')
if iConfigLoader is None:
    print("Error: The config file %s is not exist.Program exit!" %str(gGonfigPath))
    exit()
CONFIG_DICT = iConfigLoader.getJson()

ROOT_DIR = os.path.join(dirpath, CONFIG_DICT['LOG_DIR'])

#-------<GLOBAL VARIABLES (start with "g")>------------------------------------
# VARIABLES are the built in data type.
gTestMD = CONFIG_DICT['TEST_MODE']
gClientInfo = []

#-------<GLOBAL PARAMTERS>-----------------------------------------------------
iFTPservice = None
iDataMgr = None