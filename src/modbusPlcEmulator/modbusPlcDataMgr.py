#!/usr/bin/python
#-----------------------------------------------------------------------------
# Name:        modbusPlcDataMgr.py 
#
# Purpose:     This module is the data management module to init the Modbus-TCP 
#              server, Plc internal registers, coils and the PLC ladder logic diagram.
#              It will handle the Modbus request from the honeypot PLC controller, 
#              read registers state (input), then calculate the ladder logic and 
#              set the plc coils(output) in its every clock cycle.
#  
# Author:      Yuancheng Liu
#
# Created:     2024/11/02
# version:     v_0.1.3
# Copyright:   Copyright (c) 2024 LiuYuancheng
# License:     MIT License    
#-----------------------------------------------------------------------------

import random
import threading

import modbusPlcGlobal as gv
import modbusTcpCom
from mbLadderLogic import ladderLogic

#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
class DataManager(threading.Thread):
    """ Management module running parallel with the main thread to handle all the 
        PLC request and control functions.
    """
    def __init__(self, parent) -> None:
        threading.Thread.__init__(self)
        # Init the ladder logic 
        self.ladder = ladderLogic(None, id=gv.gLadderID)
        # Init the plc data handler and permission config
        self.plcDataMgr = modbusTcpCom.plcDataHandler(allowRipList=list(gv.ALLOW_R_L).copy(), 
                                              allowWipList=list(gv.ALLOW_W_L).copy())
        # Init the modbus server
        self.server = modbusTcpCom.modbusTcpServer(hostIp=gv.gPlcHostIp, 
                                                 hostPort=gv.gHostPort, 
                                                 dataHandler=self.plcDataMgr)
        serverInfo = self.server.getServerInfo()
        self.plcDataMgr.initServerInfo(serverInfo)
        self.plcDataMgr.addLadderLogic(gv.gLadderID, self.ladder)
        self.plcDataMgr.setAutoUpdate(True)
        self.terminate = False
        gv.gDebugPrint("PLC data manager init finished.", logType=gv.LOG_INFO)

    #-----------------------------------------------------------------------------
    def addAllowReadIp(self, ipaddress):
        return self.plcDataMgr.addAllowReadIp(str(ipaddress))

    def addAllowWriteIp(self, ipaddress):
        return self.plcDataMgr.addAllowWriteIp(str(ipaddress))

    #-----------------------------------------------------------------------------
    def getAllowRipList(self):
        return self.plcDataMgr.getAllowReadIpaddresses()

    def getAllowWipList(self):
        return self.plcDataMgr.getAllowWriteIpaddresses()

    def getAllRegistersVal(self):
        return self.plcDataMgr.getHoldingRegState(0, 8)

    def getAllCoilsVal(self):
        return self.plcDataMgr.getCoilState(0, 8)

    #-----------------------------------------------------------------------------
    def run(self):
        """ Thread run() function call by start(). """
        gv.gDebugPrint('PLC Modbus-TCP server started.', logType=gv.LOG_INFO)
        self.server.startServer()
        gv.gDebugPrint('PLC Modbus-TCP server terminated.', logType=gv.LOG_INFO)

    #-----------------------------------------------------------------------------
    def resetAllowRipList(self):
        return self.plcDataMgr.setAllowReadIpaddresses(list(gv.ALLOW_R_L).copy())

    def resetAllowWipList(self):
        return self.plcDataMgr.setAllowWriteIpaddresses(list(gv.ALLOW_W_L).copy())

    #-----------------------------------------------------------------------------
    def getPlcStateDict(self):
        """ Return the PLC current input voltage, register value, coil value and 
            output voltage as a dictionary.
        """
        stateDict = {
            'inputVol':[],
            'registerVal':[],
            'coilVal':[],
            'outputVol':[]
        }
        for val in self.getAllRegistersVal():
            stateDict['registerVal'].append(val)
            voltage = round(5 + random.uniform(-0.05, 0.05),2) if val else 0 
            stateDict['inputVol'].append(voltage)
        for val in self.getAllCoilsVal():
            stateDict['coilVal'].append(val)
            voltage = round(5 + random.uniform(-0.05, 0.05),2) if val else 0
            stateDict['outputVol'].append(voltage)
        return stateDict