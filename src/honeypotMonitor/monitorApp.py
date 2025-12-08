#!/usr/bin/python
#-----------------------------------------------------------------------------
# Name:        monitorApp.py [python3]
#
# Purpose:     This module is the main App execution file of PLC honeypot system
#              monitor web server which provide the visualization dashboard to 
#              show the working state of each subsystem and components.
#
# Author:      Yuancheng Liu
#
# Created:     2024/10/21
# version:     v_0.1.3
# Copyright:   Copyright (c) 2024 LiuYuancheng
# License:     MIT License    
#-----------------------------------------------------------------------------

from datetime import timedelta 
from flask import Flask, render_template, jsonify, request

import monitorGlobal as gv
import monitorDataMgr as dataMgr

#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
# Init the flask web app program.
def createApp():
    """ Create the flask App and init the app config parameters."""
    app = Flask(__name__)
    app.config['SECRET_KEY'] = gv.APP_SEC_KEY
    app.config['REMEMBER_COOKIE_DURATION'] = timedelta(seconds=gv.COOKIE_TIME)
    return app

gv.iDataMgr = dataMgr.DataManger()
app = createApp()

#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
# web request handling functions.
@app.route('/')
@app.route('/index')
def index():
    """ route to introduction index page."""
    posts = {'page': 0}  # page index is used to highlight the left page slide bar.
    return render_template('index.html', posts=posts)

#-----------------------------------------------------------------------------
@app.route('/controllerview')
def controllerview():
    """ route to PLC controllers subsystem view page."""
    infoList = gv.iDataMgr.getAllControllerState()
    posts = {'page': 1,
             'controllerinfo': infoList
             }
    return render_template('controllerview.html', posts=posts)

#-----------------------------------------------------------------------------
@app.route('/plcemuview')
def plcemuview():
    """ route to PLC emulators subsystem view page."""
    infoList = gv.iDataMgr.getAllPlcState()
    posts = {'page': 2,
             'plcinfo': infoList
             }
    return render_template('plcemuview.html', posts=posts)

#-----------------------------------------------------------------------------
@app.route('/plc/<string:postID>')
def plcpeerstate(postID):
    """ route to the individual PLC emulator state page."""
    plcInfo = gv.iDataMgr.getPlcState(postID)
    posts = { 'plcinfo': plcInfo}
    reportDict = gv.iDataMgr.getPlcReport(postID)
    if reportDict is not None: posts.update(reportDict)
    return render_template('plcpeerstate.html', posts=posts)

#-----------------------------------------------------------------------------
@app.route('/controller/<string:postID>')
def ctrlpeerstate(postID):
    """ route to the individual PLC controller state page."""
    controllerInfo = gv.iDataMgr.getControllerState(postID)
    posts = {'controllerinfo': controllerInfo}
    reportDict = gv.iDataMgr.getControllerReport(postID)
    if reportDict is not None: posts.update(reportDict)
    return render_template('ctrlpeerstate.html', posts=posts)

#-----------------------------------------------------------------------------
@app.route('/dataPost', methods=('POST',))
def dataPost():
    """ Handle PLC emulator and controller data report request.
        API call example:
            requests.post(http://%s:%s/dataPost/<devID>, json={})
    """
    content = request.json
    gv.gDebugPrint("Raw Data: %s" % str(content), prt=True, logType=gv.LOG_INFO)
    result = gv.iDataMgr.handleRequest(content) if gv.iDataMgr else {"ok": True}
    return jsonify(result)

#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
if __name__ == '__main__':
    #app.run(host="0.0.0.0", port=5000,  debug=False, threaded=True)
    app.run(host=gv.gflaskHost,
        port=gv.gflaskPort,
        debug=gv.gflaskDebug,
        threaded=gv.gflaskMultiTH)
