#!/usr/bin/python
#-----------------------------------------------------------------------------
# Name:        monitorClient.py
#
# Purpose:     The client module used to report honeypot PLC emulator and controller
#              state to the monitor hub. 
#  
# Author:      Yuancheng Liu
#
# Created:     2024/11/02
# version:     v0.1.3
# Copyright:   Copyright (c) 2024 LiuYuancheng
# License:     MIT License
#-----------------------------------------------------------------------------

import time
import copy
import requests
import threading
from datetime import datetime
from queue import Queue

MAX_RTP_NUM = 10    # Max number of report can be stored in the queue.

# report type constants
RPT_NORMAL = 'normal'
RPT_WARN = 'warning'
RPT_ALERT = 'alert'
RPT_LOGIN = 'login'
# client ype constants
PLC_TYPE='plc'
CTRL_TYPE='controller'

#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
class monitorClient(threading.Thread):

    def __init__(self, monIP, monPort, reportInterval=5):
        """ Init the monitor client.
            Args:
                monIP (str): monitor hub IP address.
                monPort (int): monitor hub port.
                reportInterval (int, optional): report interval in seconds. Defaults to 5 sec.
        """
        threading.Thread.__init__(self)
        self.monIP = monIP
        self.monPort = monPort
        self.reportInterval = reportInterval
        self.reportLock = threading.Lock()
        self._postUrl = "http://%s:%s/dataPost" % (self.monIP, str(self.monPort))
        self.parentInfoDict = None
        self.monConnected = False
        self.terminate = False 
        self.reportQueue = Queue(maxsize=MAX_RTP_NUM)
        
    #-----------------------------------------------------------------------------
    def addReportDict(self, actionType, reportMsg):
        """ Add the report message to the queue.
            Args:
                actionType(str): one of the report type constants
                msgDict (dict): report message dict.
        """
        if self.reportQueue.full(): self.reportQueue.get()
        data = {
            'type': actionType,
            'time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'message': actionType+' : '+reportMsg
        }
        self.reportQueue.put((actionType, data))

    #-----------------------------------------------------------------------------
    def setParentInfo(self, parID, parIP, parType, parPro, tgtID=None, tgtIP=None, ladderID=None):
        """ Set the parent info.
            Args:
                parID (str): parent ID.
                parIP (str): parent IP address.
                parType (str): parent type.
                parPro (str): parent protocol.
                tgtID (str, optional): target ID. Defaults to None.
                tgtIP (str, optional): target IP address. Defaults to None.
                ladderID (str, optional): ladder logic ID. Defaults to None.
        """
        self.parentInfoDict = {
            "ID": parID, 
            "IP": parIP, 
            "Type": parType, 
            "Protocol": parPro,
            "LadderID": ladderID
        }
        if tgtID is not None: self.parentInfoDict["TargetID"] = tgtID
        if tgtIP is not None: self.parentInfoDict["TargetIP"] = tgtIP

    #-----------------------------------------------------------------------------
    def logintoMonitor(self):
        """ Login to the monitor hub when the program start."""
        self.report2Monitor(RPT_LOGIN, copy.deepcopy(self.parentInfoDict))

    #-----------------------------------------------------------------------------
    def report2Monitor(self, action, data):
        """ Report the data to monitor hub.
            Args:
                action (str): action name.
                data (dict): data to report.
        """
        dataDict = {
            'ID': self.parentInfoDict['ID'],
            'Action': action,
            'Timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'Data': data
        }
        self._postData(self._postUrl, dataDict)

    #-----------------------------------------------------------------------------
    def _postData(self, postUrl, jsonDict, postfile=False):
        """ Send HTTP POST request to send data.
            Args:
                postUrl (str): url string.
                jsonDict (dict): json data send via POST.
                postfile (bool, optional): True: upload file, False: submit data/message.
                    Defaults to False.
            Returns:
                _type_: Server repsonse or None if post failed / lose connection.
        """
        self.reportLock.acquire()
        try:
            res = requests.post(postUrl, files=jsonDict, verify=False) if postfile else requests.post(postUrl, json=jsonDict, verify=False)
            if res.ok:
                print("http server reply: %s" % str(res.json()))
                self.reportLock.release()
                self.monConnected = True
                return res.json()
        except Exception as err:
            print("Error: _postData() > http server not reachable or POST error: %s" % str(err))
            self.monConnected = False
        if self.reportLock.locked(): self.reportLock.release()
        return None

    #-----------------------------------------------------------------------------
    def run(self):
        """ Main state report and task fetch loop called by start(). """
        print("Start the monitor report client main loop.")
        while not self.terminate:
            if self.monConnected:
                if not self.reportQueue.empty():
                    actionType, data = self.reportQueue.get()
                    self.report2Monitor(actionType, data)
            else:
                self.logintoMonitor()
            time.sleep(self.reportInterval)
        print("Monitor report client main loop end.")
