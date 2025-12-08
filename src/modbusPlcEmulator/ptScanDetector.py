#!/usr/bin/python
#-----------------------------------------------------------------------------
# Name:        ptScanDetector.py
#
# Purpose:     The port scan detector module splitted from the PLC emulator and run 
#              separate as to detect the red team attacker's port scan. This module 
#              currently only worked on Linux OS
#  
# Author:      Yuancheng Liu
#
# Created:     2024/12/02
# version:     v0.1.3
# Copyright:   Copyright (c) 2024 LiuYuancheng
# License:     MIT License
#-----------------------------------------------------------------------------

import modbusPlcGlobal as gv
import monitorClient
from monitorClient import RPT_ALERT, PLC_TYPE

from scapy.all import *
from collections import defaultdict
import time

# Set the contents
SCAN_DETECTION_THRESHOLD = 100  # Number of  ports accessed in a short period

# Dictionary to track IPs and their accessed ports
scan_tracker = defaultdict(list)
# Dictionary to track the scan alert report count
alert_tracker = {}

gv.iMonitorClient = monitorClient.monitorClient( gv.gMonHubIp, gv.gMonHubPort, 
                                                reportInterval=gv.gReportInv)

gv.iMonitorClient.setParentInfo(gv.gOwnID, gv.gOwnIP, PLC_TYPE, gv.gProType, 
                                ladderID=gv.gLadderID)

#-----------------------------------------------------------------------------
def detectScan(packet):
    """Detect Nmap TCP SYN scans request and ."""
    if packet.haslayer(TCP) and packet[TCP].flags == "S":  # TCP SYN packets
        srcIP = packet[IP].src
        destPort = packet[TCP].dport
        # Track the port and timestamp
        scan_tracker[srcIP].append((destPort, time.time()))
        if srcIP not in alert_tracker: alert_tracker[srcIP] =1
        # Check for scan threshold
        if len(scan_tracker[srcIP]) >= SCAN_DETECTION_THRESHOLD and alert_tracker[srcIP]==1:
            msg = "Alert: Nmap scan detected from %s and try scan more than %s ports" %(srcIP, str(SCAN_DETECTION_THRESHOLD))
            if gv.iMonitorClient:
                alert_tracker[srcIP] = 0
                print(msg)
                gv.iMonitorClient.addReportDict(RPT_ALERT, msg)

#-----------------------------------------------------------------------------
# Sniff network packets
def monitorSynRequest(interface="eth0"):
    print("Monitoring traffic on for Nmap scans...")
    sniff(iface=interface, prn=detectScan, store=False)

#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
if __name__ == "__main__":
    interface = "eth0"  # Replace with your network interface name
    # Init the monitor client thread.
    gv.iMonitorClient.start()
    # start sniffing the 
    monitorSynRequest(interface)