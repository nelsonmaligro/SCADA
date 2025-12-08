#-----------------------------------------------------------------------------
# Name:        s7commPlcControllerApp.py
#
# Purpose:     This module is the controller program start a Siemens-S7Comm PLC 
#              client to connect to the PLC simulator to do the PLC control 
#              and result verification, then it will also regularly report 
#              the verification state to the monitor hub for exception detection.
#              
# Author:      Yuancheng Liu
#
# Created:     2024/11/08
# Version:     v_0.1.3
# Copyright:   Copyright (c) 2024 LiuYuancheng
# License:     MIT License      
#-----------------------------------------------------------------------------
"""
Verification Algorithm Design:
    The honeypot PLC controller import the exactly same ladder logic, memory and data index
    matrix as the target PLC, when it is doing the control and verification, it will random 
    generate the PLC control request, then pass the request to the PLC emulator via S7comm, 
    at the same time, it will also run the request to its internal ladder logic to get the
    "Expected result", then compare the "Expected result" with the "PLC result" to check whether 
    they are same, if they are different, it will identify that either the PLC is under FCI, FDI 
    attack or the PLC ladder logic is modified by attacker.
"""
import time
from random import randint

import s7commPlcControllerGlobal as gv
import snap7Comm
from snap7Comm import BOOL_TYPE

import monitorClient
from s7LadderLogic import ladderLogic

import tkinter as tk
from tkinter import messagebox

def popup(msg):
    # Create a root window (it will be hidden)
    root = tk.Tk()
    root.withdraw()  # Hide the main window
    root.attributes('-topmost', True)  # Make it stay on top of all windows
    # Show a popup message
    messagebox.showerror("Critical",msg)

    # Close the root window
    root.destroy()

#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
class plcControllerApp(object):
    """ PLC controller main program. It will generate the PLC control request 
        randomly then check the plc execution result.
    """
    def __init__(self) -> None:
        # init the monitor reporter thread
        gv.iMonitorClient = monitorClient.monitorClient(gv.gMonHubIp, gv.gMonHubPort, 
                                                reportInterval=gv.gReportInv)
        gv.iMonitorClient.setParentInfo(gv.gOwnID, gv.gOwnIP, monitorClient.CTRL_TYPE, gv.gProType, 
                                        tgtID=gv.gPlcID, tgtIP=gv.gPlcIP, ladderID=gv.gLadderID)

        # Init the PLC S7Comm client
        self.s7commClient = snap7Comm.s7CommClient(gv.gPlcIP, rtuPort=gv.gPlcPort, snapLibPath=gv.gS7snapDllPath)
        self.ladderLogic = ladderLogic(None, gv.gLadderID)
        self.terminate = False
        gv.iMonitorClient.logintoMonitor()
        gv.iMonitorClient.start()
        gv.gDebugPrint("PLC controller %s Inited" % gv.gOwnID, logType=gv.LOG_INFO)

    #-----------------------------------------------------------------------------
    def startClient(self):
        """ Start the PLC client loop to send the holding register and get the coil 
            states, then compare with the local calculated result. If match, means 
            PLC works normally, else means PLC has some problem or under attack.
            
            User can modify this function to add more control logic.
        """
        gv.gDebugPrint("PLC controller verification loop started", logType=gv.LOG_INFO)

        while not self.terminate:
            gv.gDebugPrint("Start one around verification.", logType=gv.LOG_INFO)
            time.sleep(gv.gPlcConnInt)
            # generate random memory change input
            randomVals = [randint(0, 1) for i in range(8)]
            regVals = [i == 1 for i in randomVals]
            gv.gDebugPrint("Random generate input: %s" %str(regVals), logType=gv.LOG_INFO)
            resultExp = self.ladderLogic.runVerifyLadderLogic(regVals)
            gv.gDebugPrint("Expected output: %s" %str(resultExp), logType=gv.LOG_INFO)
            self.s7commClient.setAddressVal(1, 0, regVals[0], dataType=snap7Comm.BOOL_TYPE)
            time.sleep(0.1)
            self.s7commClient.setAddressVal(1, 2, regVals[1], dataType=snap7Comm.BOOL_TYPE)
            time.sleep(0.1)
            self.s7commClient.setAddressVal(1, 4, regVals[2], dataType=snap7Comm.BOOL_TYPE)
            time.sleep(0.1)
            self.s7commClient.setAddressVal(1, 6, regVals[3], dataType=snap7Comm.BOOL_TYPE)
            time.sleep(0.1)
            self.s7commClient.setAddressVal(2, 0, regVals[4], dataType=snap7Comm.BOOL_TYPE)
            time.sleep(0.1)
            self.s7commClient.setAddressVal(2, 2, regVals[5], dataType=snap7Comm.BOOL_TYPE)
            time.sleep(0.1)
            self.s7commClient.setAddressVal(2, 4, regVals[6], dataType=snap7Comm.BOOL_TYPE)
            time.sleep(0.1)
            self.s7commClient.setAddressVal(2, 6, regVals[7], dataType=snap7Comm.BOOL_TYPE)
            time.sleep(0.1)
            time.sleep(1)
            # get PLC result
            val1 = self.s7commClient.readAddressVal(3, dataIdxList=(0, 2, 4, 6),
                                                    dataTypeList=(BOOL_TYPE, BOOL_TYPE, BOOL_TYPE, BOOL_TYPE))
            val2 = self.s7commClient.readAddressVal(4, dataIdxList=(0, 2, 4, 6),
                                                    dataTypeList=(BOOL_TYPE, BOOL_TYPE, BOOL_TYPE, BOOL_TYPE))
            # set connection state
            connectionRst = False if val1 is None or val2 is None else True
            if not connectionRst:
                gv.iMonitorClient.addReportDict(monitorClient.RPT_ALERT, 
                                                "alert:Lost connection to target PLC:%s" % gv.gPlcID)
                gv.gDebugPrint("Lost connection to target PLC:%s" % gv.gPlcID, logType=gv.LOG_INFO)
                continue
            resultGet = val1 + val2
            gv.gDebugPrint("Get PLC result: %s" %str(resultGet), logType=gv.LOG_INFO)
            matchRst = resultGet == resultExp
            if not matchRst:
                gv.iMonitorClient.addReportDict(monitorClient.RPT_ALERT, 
                                                "alert:PLC output not match with expected")
                gv.gDebugPrint("Err:PLC output not match with expected")
                popup("Error on Siemens PLC! Unauthorized Data Injected.")
                continue
            #self.dataManager.setCoilState(matchRst, resultGet)
            gv.iMonitorClient.addReportDict(monitorClient.RPT_NORMAL, "PLC Control Loop Normal")
            print("Finish one PLC check round.")
            
        gv.gDebugPrint("PLC client terminated", logType=gv.LOG_INFO)

#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
def main():
    client = plcControllerApp()
    client.startClient()

if __name__ == "__main__":
    main()
