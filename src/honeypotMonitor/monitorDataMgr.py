#!/usr/bin/python
#-----------------------------------------------------------------------------
# Name:        monitorDataMgr.py [python3]
#
# Purpose:     This module is the data management module of the monitor hub to 
#              accept, process and store the data from the honeypot components.
#              It will also provide the processed data to the state visualization 
#              dashboard. 
#  
# Author:      Yuancheng Liu
#
# Created:     2024/11/03
# version:     v_0.1.3
# Copyright:   Copyright (c) 2024 LiuYuancheng
# License:     MIT License    
#-----------------------------------------------------------------------------

import time
import monitorGlobal as gv

RCD_NUM = 10 # Record number keep by the agent. 

RPT_NORMAL = 'normal'
RPT_WARN = 'warning'
RPT_ALERT = 'alert'
RPT_LOGIN = 'login'

PLC_TYPE = 'plc'
CTRL_TYPE = 'controller'

#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
class agentDev(object):
    """ Agent class used for storing and processing device's data. """
    def __init__(self, id, ipaddress, protocol, rcdLimit=RCD_NUM):
        self.id = id
        self.ipaddress = ipaddress
        self.protocol = protocol
        self.reportList = [] # list to store the report dict() data. 
        self.exceptList = [] # list to store the exception dict() data.
        self.rcdLimit = rcdLimit
        self.loginTime = time.time()
        self.lastUpdateTime = self.loginTime
        self.online = True
        self.totalExpCount = 0
        self.totalRptCount = 0

    #-----------------------------------------------------------------------------
    def addOneReport(self, reportDict):
        """ Add one report data dict into the report list."""
        self.lastUpdateTime = time.time()
        self.totalRptCount += 1
        if len(self.reportList) > self.rcdLimit: self.reportList.pop(0)
        self.reportList.append(reportDict)
        if reportDict['type'] == RPT_ALERT or reportDict['type'] == RPT_WARN:
            self.addExcept(reportDict)

    def addExcept(self, exceptDict):
        """ Add one exception data dict into the exception list."""
        if len(self.exceptList) > self.rcdLimit: self.exceptList.pop(0)
        self.totalExpCount += 1
        self.exceptList.append(exceptDict)

    #-----------------------------------------------------------------------------
    def getID(self):
        return self.id
    
    def getAgentState(self):
        self.updateOnlineState()
        dataDict = {'id': self.id,
                    'ip': self.ipaddress,
                    'protocol': self.protocol,
                    'lastUpdateT': time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(self.lastUpdateTime)),
                    'reportT': (self.lastUpdateTime - self.loginTime)//60,
                    'online': self.online,
                    'exceptCount': self.totalExpCount,
                    'totalRptCount': self.totalRptCount
                    }
        return dataDict

    def getRecordList(self):
        return self.reportList
    
    def getExecptList(self):
        return self.exceptList

    #-----------------------------------------------------------------------------
    def setIP(self, newIp):
        self.ipaddress = newIp
    
    def setProtocol(self, newProtocol):
        self.protocol = newProtocol

    def updateOnlineState(self):
        self.online = time.time() - self.lastUpdateTime < gv.gTimeOut

#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
class agentPLC(agentDev):
    """ Agent class used for storing and processing PLC emulator data. """

    def __init__(self, id, ipaddress, protocol, ladderInfo=None):
        super().__init__(id, ipaddress, protocol)
        self.ladderInfo = ladderInfo

    def getPLCState(self):
        dataDict = self.getAgentState()
        dataDict['ladderInfo'] = self.ladderInfo
        return dataDict

    def setLadderInfo(self, ladderInfo):
        self.ladderInfo = ladderInfo

#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
class agentController(agentDev):
    """ Agent class used for storing and processing PLC controller data. """

    def __init__(self, id, ipaddress, protocol, plcID, plcIP):
        super().__init__(id, ipaddress, protocol)
        self.tgtPlcID = plcID
        self.tgtPlcIP = plcIP

    def getControllerState(self):
        dataDict = self.getAgentState()
        dataDict['TargetID'] = self.tgtPlcID
        dataDict['TargetIP'] = self.tgtPlcIP
        return dataDict

    def setTargetPLCInfo(self, plcID, plcIP):
        self.tgtPlcID = plcID
        self.tgtPlcIP = plcIP

#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
class DataManger(object):
    """ Data manager class for the monitor hub. """
    def __init__(self, parent=None):
        self.parent = parent
        # Init dictionary to store PLC emulator data, key will be the plcID,
        # value will be the agentPLC object
        self.plcDict = {}
        # Init dictionary to store PLC controller data, key will be the controllerID,
        # value will be the agentController object
        self.controllerDict = {}
        gv.gDebugPrint("Monitor Hub Data Manager Initialized.", logType=gv.LOG_INFO)
    
    #-----------------------------------------------------------------------------
    def addPlc(self, plcID, plcIP, protocol, ladderInfo=None):
        """ Create a agentPLC and add in the plcDict.
            Args:
                plcID (str): unique PLC emulator ID.
                plcIP (str): PLC emulator IP address.
                protocol (str): OT protocol used by PLC emulator.
                ladderInfo (_type_, str): ladder logic module ID. Defaults to None.
        """
        if plcID not in self.plcDict.keys():
            self.plcDict[plcID] = agentPLC(plcID, plcIP, protocol, ladderInfo=ladderInfo)
            gv.gDebugPrint("Added a new PLC emulator: %s" % plcID, logType=gv.LOG_INFO)
        else:
            self.plcDict[plcID].setIP(plcIP)
            self.plcDict[plcID].setProtocol(protocol)
            self.plcDict[plcID].setLadderInfo(ladderInfo)
            gv.gDebugPrint("Updated existed PLC emulator info: %s" % plcID, 
                           logType=gv.LOG_INFO)

    #-----------------------------------------------------------------------------
    def addController(self, controllerID, controllerIP, protocol, plcID, plcIP):
        """ Create a agentController and add in the controllerDict.

        Args:
            controllerID (str): unique PLC controller ID.
            controllerIP (str): PLC controller IP address.
            protocol (str): OT protocol used by PLC controller to link to PLC
            plcID (str): connected PLC ID.
            plcIP (str): connected PLC ID.
        """
        if controllerID not in self.controllerDict.keys():
            self.controllerDict[controllerID] = agentController(controllerID, controllerIP, protocol, plcID, plcIP)
            gv.gDebugPrint("Added a new PLC controller: %s" % controllerID, logType=gv.LOG_INFO)
        else:
            self.controllerDict[controllerID].setIP(controllerIP)
            self.controllerDict[controllerID].setProtocol(protocol)
            self.controllerDict[controllerID].setTargetPLCInfo(plcID, plcIP)
            gv.gDebugPrint("Updated existed PLC controller info: %s" % controllerID, 
                           logType=gv.LOG_INFO)

    #-----------------------------------------------------------------------------
    def handleRequest(self, requestDict):
        """ Handle all the report request from the PLC emulator and controller."""
        reqDict = dict(requestDict)
        action = str(reqDict['Action']).lower()
        data = reqDict['Data']

        if action == RPT_LOGIN:
            if str(data['Type']).lower() == PLC_TYPE:
                self.addPlc(data['ID'], data['IP'], data['Protocol'], ladderInfo=data['LadderID'])
                gv.gDebugPrint("PLC Emulator: %s login." % data['ID'], logType=gv.LOG_INFO)
            elif str(data['Type']).lower() == 'controller':
                self.addController(data['ID'], data['IP'], data['Protocol'], data['TargetID'], data['TargetIP'])
                gv.gDebugPrint("PLC Controller: %s login." % data['ID'], logType=gv.LOG_INFO)
        elif action == RPT_NORMAL or action == RPT_WARN or action == RPT_ALERT:
            if reqDict['ID'] in self.plcDict.keys(): 
                self.plcDict[reqDict['ID']].addOneReport(data)
            elif reqDict['ID'] in self.controllerDict.keys(): 
                self.controllerDict[reqDict['ID']].addOneReport(data)
            else:
                gv.gDebugPrint("ID: %s not login before.", logType=gv.LOG_WARN)
        return {"ok": True}

    #-----------------------------------------------------------------------------
    # Function to provide PLC emulator data
    def getAllPlcState(self):
        return [self.plcDict[plcID].getPLCState() for plcID in self.plcDict.keys()]
    
    def getPlcState(self, plcID):
        return self.plcDict[plcID].getPLCState() if plcID in self.plcDict.keys() else None 
            
    def getPlcReport(self, plcID):
        if plcID in self.plcDict.keys():
            return {
                'report': self.plcDict[plcID].getRecordList(),
                'alert': self.plcDict[plcID].getExecptList()
            }
        return None

    #-----------------------------------------------------------------------------
    # Function to provide PLC controller data
    def getAllControllerState(self):
        return [self.controllerDict[controllerID].getControllerState() for controllerID in self.controllerDict.keys()] 

    def getControllerState(self, controllerID):
        return self.controllerDict[controllerID].getControllerState() if controllerID in self.controllerDict.keys() else None 
    
    def getControllerReport(self, controllerID):
        if controllerID in self.controllerDict.keys():
            return {
                'report': self.controllerDict[controllerID].getRecordList(), 
                'alert': self.controllerDict[controllerID].getExecptList()
            }
        return None
