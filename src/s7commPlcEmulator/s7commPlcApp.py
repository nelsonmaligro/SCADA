#!/usr/bin/python
#-----------------------------------------------------------------------------
# Name:        s7commPlcApp.py
#
# Purpose:     This module is the main App execution file of the S7Comm PLC 
#              emulator of the honeypot project. It provide the  S7Comm interface 
#              for handling the OT control request and a web interface for PLC 
#              configuration change.
#
# Author:      Yuancheng Liu
#
# Created:     2024/10/21
# version:     v_0.1.3
# Copyright:   Copyright (c) 2024 LiuYuancheng
# License:     MIT License    
#-----------------------------------------------------------------------------

from datetime import timedelta, datetime
from flask import Flask, render_template, flash, redirect, url_for, request
from flask_login import LoginManager, login_required

import s7commPlcGlobal as gv
import s7commPlcAuth
import s7commPlcDataMgr
import monitorClient
from monitorClient import RPT_ALERT, PLC_TYPE

    
#-----------------------------------------------------------------------------
# Init the flask web app program.
def createApp():
    """ Create the flask App."""
    # init the web host
    app = Flask(__name__)
    app.config['SECRET_KEY'] = gv.APP_SEC_KEY
    app.config['REMEMBER_COOKIE_DURATION'] = timedelta(seconds=gv.COOKIE_TIME)
    from s7commPlcAuth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint)
    # Create the user login manager
    loginMgr = LoginManager()
    loginMgr.loginview = 'auth.login'
    loginMgr.init_app(app)
    @loginMgr.user_loader
    def loadUser(userID):
        return s7commPlcAuth.User(userID)
    return app

# Init the user manager
gv.iUserMgr = s7commPlcAuth.userMgr(gv.gUsersRcd)

# Init the PLC function thread.
gv.iPlcDataMgr = s7commPlcDataMgr.DataManager(None)
gv.iPlcDataMgr.start()

gv.iMonitorClient = monitorClient.monitorClient( gv.gMonHubIp, gv.gMonHubPort, 
                                                reportInterval=gv.gReportInv)

gv.iMonitorClient.setParentInfo(gv.gOwnID, gv.gOwnIP, PLC_TYPE, gv.gProType, 
                                ladderID=gv.gLadderID)
gv.iMonitorClient.logintoMonitor()
gv.iMonitorClient.start()

# Init the Web UI thread.
app = createApp()


         

# Please un-comment this function if you want to pick any http request such as normal curl
#@app.before_request
#def before_request():
    #"""Triggered by any request to the web server such as curl"""
    #if gv.iMonitorClient: 
        #gv.iMonitorClient.addReportDict(RPT_ALERT, "A http request is sent to PLC emulator. Someone tries to scan the PLC web service")

#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
# web request handling functions.
@app.route('/')
@app.route('/index')
def index():
    """ route to introduction index page."""
    posts = {'page': 0,
             'ipaddress': gv.gOwnIP,
             'time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
             }  # page index is used to highlight the left page slide bar.
    #if gv.iMonitorClient: gv.iMonitorClient.addReportDict(RPT_ALERT, "A http request is sent to PLC emulator. Possible probe or scan to the PLC web service" )
    return render_template('index.html', posts=posts)
    
#-----------------------------------------------------------------------------
@app.route('/plcstate')
@login_required
def plcstate():
    """ route to the ladder logic page."""
    posts = {'page': 1,
             'time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
             }
    stateData = gv.iPlcDataMgr.getPlcStateDict()
    posts.update(stateData)
    return render_template('plcstate.html', posts=posts)

# -----------------------------------------------------------------------------
# page 3 admin user account's request handling function.
@app.route('/accmgmt')
@login_required
def accmgmt():
    posts = {'page': 3,
             'users': gv.iUserMgr.getUserInfo(),
             'time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
    return render_template('accmgmt.html', posts=posts)

# -----------------------------------------------------------------------------
@app.route('/accmgmt/<string:username>/<string:action>', methods=('POST',))
@login_required
def changeAcc(username, action):
    """ Handle the user account's POST request.
        Args:
            username (str): user name string
            action (str): action tag.
    """
    if action == 'delete':
        if gv.iUserMgr.removeUser(str(username).strip()):
            flash('User [ %s ] has been deleted.' % str(username))
        else:
            flash('User not found.')
    return redirect(url_for('accmgmt'))

# -----------------------------------------------------------------------------
@app.route('/addnewuser', methods=['POST', ])
@login_required
def addnewuser():
    """ Addd a new user in the IoT system."""
    if request.method == 'POST':
        tgttype = request.form.getlist('optradio')
        tgtUser = request.form.get("username")
        tgtPwd = request.form.get("password")
        # print((tgttype, tgtUser, tgtPwd))
        if not gv.iUserMgr.userExist(tgtUser):
            userType = 'admin' if 'option1' in tgttype else 'user'
            if gv.iUserMgr.addUser(tgtUser, tgtPwd, userType):
                flash('User [ %s ] has been added.' % str(tgtUser))
            else:
                flash('User [ %s ] can not be added.' % str(tgtUser))
        else:
            flash('User [ %s ] has been exist.' % str(tgtUser))
    return redirect(url_for('accmgmt'))

# -----------------------------------------------------------------------------
@app.route('/setpassword/<string:username>', methods=['POST', ])
@login_required
def setpassword(username):
    """ Update the user password."""
    if request.method == 'POST':
        newPassword = str(request.form.get("newpassword")).strip()
        if newPassword:
            rst = gv.iUserMgr.updatePwd(username, newPassword)
            if rst:
                flash('Password of user [ %s ] has been changed.' % str(username))
            else:
                flash('Password of user [ %s ] can not be changed.' % str(username))
        else:
            flash('Password can not be empty.')
    return redirect(url_for('accmgmt'))

#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
if __name__ == '__main__':
    #app.run(host="0.0.0.0", port=5000,  debug=False, threaded=True)
    app.run(host=gv.gflaskHost,
        port=gv.gflaskPort,
        debug=gv.gflaskDebug,
        threaded=gv.gflaskMultiTH)
        