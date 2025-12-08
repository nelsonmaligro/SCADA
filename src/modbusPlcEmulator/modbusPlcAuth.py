#-----------------------------------------------------------------------------
# Name:        modbusPlcAuth.py
#
# Purpose:     PLC emulator's user authorization module used for check user login, 
#              signup, update and logout.
#              
# Author:      Yuancheng Liu
#
# Created:     2024/11/03
# version:     v_0.1.3
# Copyright:   Copyright (c) 2024 LiuYuancheng
# License:     MIT License    
#-----------------------------------------------------------------------------

from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, login_required, logout_user, UserMixin

import modbusPlcGlobal as gv
from ConfigLoader import JsonLoader
from monitorClient import RPT_NORMAL, RPT_WARN, RPT_ALERT

auth = Blueprint('auth', __name__)

#-----------------------------------------------------------------------------
class User(UserMixin):
    """ User object used to get the user info from backend during init.
        Args:
            UserMixin (_type_): _description_
    """
    def __init__(self, id):
        self.id = id
        self.name = id
        self.type = 'user'
        self.password = None

    def __repr__(self):
        return "%d/%s/%s" % (self.name, self.type, self.password)

# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
class userMgr(JsonLoader):
    """ User information manager module to handle add user, delete user, update 
        user, query user information. It is a child module inherited from  
        ConfigLoader.JsonLoader
    """
    
    def __init__(self, userRcd):
        """ userMgr class constructor. Init example mgr = userMgr("user.json")
            Args:
                userRcd (str): user record json file path.
        """
        super().__init__()
        self.loadFile(userRcd)

    # -----------------------------------------------------------------------------
    # user check function.
    def userExist(self, userID):
        if not self._haveData(): return False
        if userID in self.jsonData.keys(): return True
        return False

    def verifyUser(self, userName, userPwd):
        if self.userExist(userName):
            return self.jsonData[str(userName)]['password'] == userPwd
        return False
    
    # -----------------------------------------------------------------------------
    # Get() function
    def getUserInfo(self):
        if self._haveData():
            return self.getJsonData().values()
        return []

    # -----------------------------------------------------------------------------
    # user create, update and delete function.
    def addUser(self, userName, userPwd, userType, updateRcd=True):
        userName = str(userName).strip()
        if not self._haveData(): return False 
        if self.userExist(userName): return False
        data = {
            "username": str(userName),
            "password": str(userPwd),
            "usertype": str(userType)
        }
        self.jsonData[userName] = data
        if gv.iMonitorClient: gv.iMonitorClient.addReportDict(RPT_WARN, "Added new user: %s" % userName)
        if updateRcd: self.updateRcdFile()
        return True
    
    # -----------------------------------------------------------------------------
    def updatePwd(self, userName, newPwd, updateRcd=True) :
        if self.userExist(userName):
            self.jsonData[userName]['password'] = str(newPwd)
            if gv.iMonitorClient: gv.iMonitorClient.addReportDict(RPT_WARN, "User %s password is changed" % userName)
            if updateRcd: self.updateRcdFile()
            return True 
        return False

    # -----------------------------------------------------------------------------
    def removeUser(self, userName, updateRcd=True):
        print(userName)
        if self.userExist(userName):
            self.jsonData.pop(userName)
            if gv.iMonitorClient: gv.iMonitorClient.addReportDict(RPT_ALERT, "PLC user detect action, username: %s " % userName)
            if updateRcd: self.updateRcdFile()
            return True            
        return False

#-----------------------------------------------------------------------------
@auth.route('/login')
def login():
    return render_template('index.html')

@auth.route('/login', methods=['POST'])
def login_post():
    account = request.form.get('account')
    password = request.form.get('password')
    remember = True if request.form.get('remember') else False
    print((account, password))
    if gv.iUserMgr.userExist(account):
        if gv.iUserMgr.verifyUser(str(account), str(password)):
            login_user(User(account), remember=remember)
            if gv.iMonitorClient: gv.iMonitorClient.addReportDict(RPT_NORMAL, "User %s login to PLC" % account)
            return redirect(url_for('index'))
        else:
            flash('User password incorrect!')
    else:
        flash('Login user does not exit!')
    return redirect(url_for('index'))

#-----------------------------------------------------------------------------
@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))