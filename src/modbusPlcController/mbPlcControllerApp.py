#-----------------------------------------------------------------------------
# Name:        mbPlcControllerApp.py
#
# Purpose:     This module is the controller program start a Modbus-TCP PLC 
#              client to connect to the PLC simulator to do the PLC control 
#              and result verification, then it will also regularly report 
#              the verification state to the monitor hub for exception detection.
#              
# Author:      Yuancheng Liu
#
# Created:     2024/10/28
# Version:     v_0.1.3
# Copyright:   Copyright (c) 2024 LiuYuancheng
# License:     MIT License      
#-----------------------------------------------------------------------------
"""
Verification Algorithm Design:
    The honeypot PLC controller import the exactly same ladder logic, register and coil 
    matrix as the target PLC, when it is doing the control and verification, it will random 
    generate the PLC control request, then pass the request to the PLC emulator via Modbus-TCP, 
    at the same time, it will also run the request to its internal ladder logic to get the
    "Expected result", then compare the "Expected result" with the "PLC result" to check whether 
    they are same, if they are different, it will identify that either the PLC is under FCI, FDI 
    attack or the PLC ladder logic is modified by attacker.
"""

import time
from random import randint

import mbPlcControllerGlobal as gv
import modbusTcpCom

import monitorClient
from mbLadderLogic import ladderLogic

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
        # Init the PLC Modbus-TCP client
        self.modbusClient = modbusTcpCom.modbusTcpClient(gv.gPlcIP, tgtPort=gv.gPlcPort)
        self.ladderLogic = ladderLogic(None)
        self.terminate = False
        # Test connection
        while not self.modbusClient.checkConn():
            gv.gDebugPrint('Try connect to the PLC: %s' %str(gv.gPlcID), logType=gv.LOG_INFO)
            gv.gDebugPrint("Read coil state: %s" %str(self.modbusClient.getCoilsBits(0, 8)), 
                           logType=gv.LOG_INFO)
            time.sleep(1)
        gv.iMonitorClient.logintoMonitor()
        gv.iMonitorClient.start()
        gv.gDebugPrint("PLC connection established", logType=gv.LOG_INFO)

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
            
            # generate random register input
            regVals = [randint(0, 1) for i in range(8)]
            gv.gDebugPrint("Random generated input: %s" %str(regVals), logType=gv.LOG_INFO)
            # get the expected reault 
            result = self.ladderLogic.runLadderLogic(regVals)
            resultExp = [i == 1 for i in result]
            gv.gDebugPrint("Expected output: %s" %str(resultExp), logType=gv.LOG_INFO)
            for i in range(8):
                self.modbusClient.setHoldingRegs(i, regVals[i])
                time.sleep(0.1)
            time.sleep(1)
            resultGet = self.modbusClient.getCoilsBits(0, 8)
            gv.gDebugPrint("Get PLC result: %s" %str(resultGet), logType=gv.LOG_INFO)
            # set connection state
            connectionRst = False if resultGet is None else True
            if not connectionRst:
                gv.iMonitorClient.addReportDict(monitorClient.RPT_ALERT, 
                                                "alert:Lost connection to target PLC")
                gv.gDebugPrint("Lost connection to target PLC", logType=gv.LOG_INFO)
                continue
            matchRst = resultGet == resultExp
            if not matchRst:
                gv.iMonitorClient.addReportDict(monitorClient.RPT_ALERT, 
                                                "alert:PLC output not match with expected")
                gv.gDebugPrint("Error:PLC output not match with expected", logType=gv.LOG_INFO)
                popup("Error on modBus PLC! Unauthorized Data Injected.")
                continue
            gv.iMonitorClient.addReportDict(monitorClient.RPT_NORMAL, "Pass:PLC Control Loop Normal")
            print("Finish one PLC check round.")
            
        gv.gDebugPrint("PLC client terminated", logType=gv.LOG_INFO)

#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------

def main():
    client = plcControllerApp()
    client.startClient()

if __name__ == "__main__":
    main()
