echo "Running PLC honey port monitor [monitorApp.py]"
start /min pythonw honeypotMonitor\monitorApp.py"

TIMEOUT /T 10 /NOBREAK
echo "Running ModbusPLC Emulator [modbusPlcApp.py]"
start /min pythonw modbusPlcEmulator\modbusPlcApp.py

echo "Running S7comm PLC emulator [s7commPlcApp.py]"
start /min pythonw s7commPlcEmulator\s7commPlcApp.py



TIMEOUT /T 10 /NOBREAK

echo "Running S7comm PLC controller [s7commPlcControllerApp.py]"
start /min pythonw s7commPlcController\s7commPlcControllerApp.py
TIMEOUT /T 2 /NOBREAK
echo "Running ModbusPLC Controller [mbPlcControllerApp.py]"
start /min pythonw modbusPlcController\mbPlcControllerApp.py
