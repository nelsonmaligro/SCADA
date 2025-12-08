#!/usr/bin/python
#-----------------------------------------------------------------------------
# Name:        s7LadderLogic.py
#
# Purpose:     This module is the PLC ladder logic simulation module example for 
#              the s7CommPLC emulator. Both the PLC emulator and controller will run the 
#              same ladder logic at the same time. This module inherits from the 
#              <lib/modbusTcpCom.py>'s ladderLogic class. If you want to build your 
#              own ladder logic, you can copy this module and modify it.
#  
# Author:      Yuancheng Liu
#
# Created:     2024/11/08
# version:     v0.1.3
# Copyright:   Copyright (c) 2024 LiuYuancheng
# License:     MIT License    
#-----------------------------------------------------------------------------

# Change below line to use the controller's global if you copy in the controller side
import s7commPlcGlobal as gv 
import snap7Comm

#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
class ladderLogic(snap7Comm.rtuLadderLogic):

    """ A test ladder logic program with take 8 bool input data in 2 memory and run a 
        1 level ladder logic then set 8 output data in another 2 memory address. To use 
        this ladder logic in plc emulator, call the self.server.startService(eventHandlerFun=handlerS7request)
        in the plc or the runVerifyLadderLogic() in the controller.
    """
    def __init__(self, parent, nameStr):
        super().__init__(parent, ladderName=nameStr)

    #-----------------------------------------------------------------------------
    def initLadderInfo(self):
        # Init the input data saving memory address and data index
        self.srcAddrValInfo = {'addressIdx': (1, 2), 'dataIdx': (0, 2, 4, 6)}
        # init the output data saving memory address and data index
        self.destAddrValInfo = {'addressIdx': (3, 4), 'dataIdx': (0, 2, 4, 6)}

    #-----------------------------------------------------------------------------
    def runLadderLogic(self, inputData=None):
        """ Execute the ladder logic with the input memory address data list and set 
            the output address data list. In this example, there will be 8 rungs to 
            be executed.
        """
        print(" - runLadderLogic")
        addr, dataIdx, datalen = inputData
        print("Received data write request: ")
        print("Address: %s " %str(addr))
        print("dataIdx: %s " %str(dataIdx))
        print("datalen: %s" %str(datalen))
        srcMIdx = self.srcAddrValInfo['addressIdx'] # source memory index
        srcDIdx = self.srcAddrValInfo['dataIdx'] # source data index

        if addr in srcMIdx and dataIdx in srcDIdx:
            # Get all current memory source value 
            ms0 = self.parent.getMemoryVal(srcMIdx[0], srcDIdx[0])
            ms1 = self.parent.getMemoryVal(srcMIdx[0], srcDIdx[1])
            ms2 = self.parent.getMemoryVal(srcMIdx[0], srcDIdx[2])
            ms3 = self.parent.getMemoryVal(srcMIdx[0], srcDIdx[3])
            ms4 = self.parent.getMemoryVal(srcMIdx[1], srcDIdx[0])
            ms5 = self.parent.getMemoryVal(srcMIdx[1], srcDIdx[1])
            ms6 = self.parent.getMemoryVal(srcMIdx[1], srcDIdx[2])
            ms7 = self.parent.getMemoryVal(srcMIdx[1], srcDIdx[3])
            
            # Run the rung and set all the memory destination value
            # rung 0: ms0 and ms1 -> ds0
            c0 = ms0 and ms7
            self.parent.setMemoryVal(self.destAddrValInfo['addressIdx'][0], 
                                    self.destAddrValInfo['dataIdx'][0], c0)
            # rung 1: not ms1 -> ds1
            c1 = not ms1
            self.parent.setMemoryVal(self.destAddrValInfo['addressIdx'][0],
                                    self.destAddrValInfo['dataIdx'][1], c1)
            # rung 2: ms2 and ms3 and ms4 -> ds2
            c2 = ms2 and ms3 and ms4
            self.parent.setMemoryVal(self.destAddrValInfo['addressIdx'][0],
                                    self.destAddrValInfo['dataIdx'][2], c2)
            # rung 3: ms0 or ms6-> ds3
            c3 = (not ms0) or ms6
            self.parent.setMemoryVal(self.destAddrValInfo['addressIdx'][0],
                                    self.destAddrValInfo['dataIdx'][3], c3)
            # rung 4: not(ms4 or ms5) -> ds4
            c4 = not(ms4 or ms5)
            self.parent.setMemoryVal(self.destAddrValInfo['addressIdx'][1],
                                    self.destAddrValInfo['dataIdx'][0], c4)
            # rung 5: not ms0 and ms6 -> ds5
            c5 = (not ms0) and ms6
            self.parent.setMemoryVal(self.destAddrValInfo['addressIdx'][1],
                                     self.destAddrValInfo['dataIdx'][1], c5)
            # rung 6: ms3 or not ms7 -> ds6
            c6 = ms3 or not ms7
            self.parent.setMemoryVal(self.destAddrValInfo['addressIdx'][1],
                                     self.destAddrValInfo['dataIdx'][2], c6)
            # rung 7: ms5 -> ds7
            c7 =  ms5
            self.parent.setMemoryVal(self.destAddrValInfo['addressIdx'][1],
                                     self.destAddrValInfo['dataIdx'][3], c7)

    #-----------------------------------------------------------------------------
    def runVerifyLadderLogic(self, regsList):
        """ Execute the ladder logic with the input holding register list and set 
            the output coils. In this example, there will be 8 rungs to be executed.
        """
        # coils will be set ast the reverse state of the input registers' state. 
        if len(regsList) != 8: return None
        # rung 0: HR0 and HR7 -> Q0
        c0 = regsList[0] and regsList[7]
        # rung 1: not HR1 -> Q1
        c1 = not regsList[1]
        # rung 2: HR2 and HR3 and HR4 -> Q2
        c2 = regsList[2] and regsList[3] and regsList[4]
        # rung 3: not HR0 or HR6 -> Q3
        c3 = (not regsList[0]) or regsList[6]
        # rung 4: not (HR4 or HR5) -> Q4
        c4 = not (regsList[4] or regsList[5])
        # rung 5: (not HR0) and HR6 -> Q5
        c5 = (not regsList[0]) and regsList[6]
        # rung 6: HR3 or (not HR7) -> Q6
        c6 = regsList[3] or (not regsList[7])
        # rung 7: HR5 -> Q7
        c7 = regsList[5]
        return [c0, c1, c2, c3, c4, c5, c6, c7]
