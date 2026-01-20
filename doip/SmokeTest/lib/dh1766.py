import socket
import time

DH1766_HOST = "192.168.2.12"
DH1766_PORT = 5025
DH1766_BUFSIZE = 0x1000

dh1766socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
dh1766socket.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, DH1766_BUFSIZE)
dh1766socket.settimeout(0.2)

def dh1766send(data):
    ADDR = (DH1766_HOST, DH1766_PORT)

    if type(data) != str:
        data = str(data)

    data = bytes(data, 'gbk')

    dh1766socket.sendto(data, ADDR)

def dh1766recv():
    try:
        data, ADDR = dh1766socket.recvfrom(DH1766_BUFSIZE)
    except socket.timeout:
        print('DH1766 time out.')
        data = ''

    if len(data) > 0:
        return data.decode('utf-8')
    else: 
        return ''
        
def dh1766call():
    dh1766send('MEAS:CURR:ALL?\n')
    cstr = dh1766recv().split(',')
    return [float(s) for s in cstr if len(s) > 0]

def dh1766vall():
    dh1766send('MEAS:VOLT:ALL?\n')
    cstr = dh1766recv().split(',')
    return [float(s) for s in cstr]

def dh1766onall():
    dh1766send('APPL:OUTP ON,ON,ON\n')

def dh1766offall(): 
    dh1766send('APPL:OUTP OFF,OFF,OFF\n')

def dh1766setvolt(v1,v2,v3):
    dh1766send('APPL:VOLT %f,%f,%f\n'%(v1,v2,v3))

def dh1766volt(v1):
    dh1766send('VOLT %f\n'%v1)

def dh1766curr():
    dh1766send('MEAS:CURR?\n')
    cstr = dh1766recv()
    if len(cstr) > 0: 
        return float(cstr)
    else: return 0

def dh1766beep():
    dh1766send('SYSTEM:BEEPER?\n')

def dh1766out(onoff):
    if onoff > 0:
        dh1766send('OUTP ON\n')
    else:
        dh1766send('OUTP OFF\n')


# dh1766offall()
# time.sleep(2)
# dh1766onall()
# time.sleep(2)
# dh1766setvolt(12,12,0)
# time.sleep(2)
# print(dh1766vall())
# time.sleep(2)
# print(dh1766call())
# time.sleep(2)
# dh1766volt(10)
# time.sleep(2)
# print(dh1766curr())
# time.sleep(2)
# dh1766out(0)