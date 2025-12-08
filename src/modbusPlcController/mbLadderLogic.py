#!/usr/bin/python
#-----------------------------------------------------------------------------
# Name:        mbLadderLogic.py
#
# Purpose:     This module is the PLC ladder logic simulation module example for 
#              the PLC emulator. Both the PLC emulator and controller will run the 
#              same ladder logic at the same time. This module inherits from the 
#              <lib/modbusTcpCom.py>'s ladderLogic class. If you want to build your 
#              own ladder logic, you can copy this module and modify it.
#  
# Author:      Yuancheng Liu
#
# Created:     2024/11/01
# version:     v_0.1.3
# Copyright:   Copyright (c) 2024 LiuYuancheng
# License:     MIT License    
#-----------------------------------------------------------------------------

# Change below line to use the controller's global if you copy in the controller side
import mbPlcControllerGlobal as gv 
import modbusTcpCom

#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
class ladderLogic(modbusTcpCom.ladderLogic):
    """ A test ladder logic program with 8 holding register and 1 level ladder
        logic to set the 8 output coils. To use this ladder logic in plc emulator,
        call the addLadderLogic() function of modbusTcpCom.plcDataHandler. 
    """
    def __init__(self, parent, id="testLDlogic") -> None:
        super().__init__(parent)
        self.id = id

    def getID(self):
        return self.id

    #-----------------------------------------------------------------------------
    def initLadderInfo(self):
        """ Initialize the ladder logic information."""
        # Init the start holding register address index I0.x
        self.holdingRegsInfo['address'] = 0
        # Init the number of holding register used. 
        self.holdingRegsInfo['offset'] = 8
        # Init teh start output coils address index Q0.x
        self.destCoilsInfo['address'] = 0
        # Init the number of output coils used.
        self.destCoilsInfo['offset'] = 8
    
    #-----------------------------------------------------------------------------
    def runLadderLogic(self, regsList, coilList=None):
        """ Execute the ladder logic with the input holding register list and set 
            the output coils. In this example, there will be 8 rungs to be executed.
        """
        # coils will be set ast the reverse state of the input registers' state. 
        if len(regsList) != 8: return None
        # rung 0: HR0 and HR2 -> Q0
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