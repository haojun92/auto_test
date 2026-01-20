import pathlib
import tempfile
import ctypes 		
import os 			
import subprocess 	
import time 				
import xml.etree.ElementTree as ET

class T32_Launch():
    def __init__(self):
        self.t32api = None

        APIPORT = '20000'
        T32_OK = 0
        SYSDIR='C:/T32/'
        APIDIR='demo/api/python/legacy/'
        APIFILE='t32api64.dll'
        LIBFILE=os.path.join(os.sep,SYSDIR,APIDIR,APIFILE)
        T32BIN=SYSDIR+"/bin/windows64/t32mv800.exe"
        CMMFILE = 'lib/rh850.cmm'

        # First, create ./config-py.t32
        CONFIGDIR= pathlib.Path(__file__).parent
        CONFIGFILE=os.path.join(CONFIGDIR,'config-py.t32')
        fp = open(CONFIGFILE,"w+")                # Overwrite if file exists
        fp.write("OS=\n")
        fp.write("ID=T32\n")
        fp.write("SYS="+SYSDIR+"\n")
        fp.write("TMP="+tempfile.gettempdir()+"\n\n")
        fp.write("PBI=\n")
        fp.write("USB\n\n")
        fp.write("RCL=NETASSIST\n")
        fp.write("PACKLEN=1024\n")
        fp.write("PORT="+APIPORT+"\n\n")
        fp.close()

        # Launch TRACE32
        self.t32api=ctypes.cdll.LoadLibrary(LIBFILE)
        print('Loading TRACE32...')
        t32process=subprocess.Popen([T32BIN,'-c',CONFIGFILE,'-s',CMMFILE])
        time.sleep(20)
        self.t32api.T32_Config(b"NODE=",b"localhost")
        self.t32api.T32_Config(b"PORT=", APIPORT.encode())
        self.t32api.T32_Config(b"PACKLEN=",b"1024")

        # Establish a connection to TRACE32
        print('Connecting TRACE32...')
        for i in range (1, 3):
            if self.t32api.T32_Init()==T32_OK:
                if self.t32api.T32_Attach(1)==T32_OK:
                    print('Successfully established a remote connection with TRACE32 PowerView.')
                    break
                else :
                    if i==1:
                        print('Failed once to established a remote connection with TRACE32 PowerView.')
                        self.t32api.T32_Exit()
                    elif i==2 :
                        print('Failed twice to established a remote connection with TRACE32 PowerView.')
                        print(' Terminating ...')
                        #sys.exit()
                        raise Exception('Failed to established a remote connection')
            else :
                if i==1:
                    print('Failed once to initialize a remote connection with TRACE32 PowerView.')
                    self.t32api.T32_Exit()
                elif i==2 :
                    print('Failed twice to initialize a remote connection with TRACE32 PowerView.')
                    print(' Terminating ...')
                    #sys.exit()
                    raise Exception('Failed to initialize a remote connection')

        # Ping TRACE32 to check the connection really is up and running
        rc = self.t32api.T32_Ping()
        if rc != 0:
            self.t32api.T32_Exit()
            print("Error in T32_Ping")
        else:
            print("Ping successfully")

    def T32_GetSymbolFromAddress(self):
        #Get symbol from current address 
        pc_address = ctypes.c_uint32(0)
        symbol_name = (ctypes.c_char*256)()
        #Get address
        error = self.t32api.T32_ReadPP(ctypes.byref(pc_address))
        if error != 0:
            print("Error in GetAddress")
        #Get symbol
        error = self.t32api.T32_GetSymbolFromAddress(symbol_name, pc_address, ctypes.c_int32(256))
        if error != 0:
            print("Error in GetSymbolFromAddress")

        return symbol_name.value.decode()

    def T32_GetSymbol(self,name):
        #Get address for symbol 
        address = ctypes.c_uint32(0)
        size = ctypes.c_uint32(0)
        reserved = ctypes.c_uint32(0)
        
        symname = bytes(name, encoding='UTF-8')
        error = self.t32api.T32_GetSymbol(symname, ctypes.byref(address), ctypes.byref(size), ctypes.byref(reserved))
        if error != 0:
            print("Error in GetSymbol")

        return address.value
    
    def T32_ReadVariableValue(self,variant):
        #Get address from variant 
        value = ctypes.c_uint32(0)
        hvalue = ctypes.c_uint32(0)
        
        symname = bytes(variant, encoding='UTF-8')
        error = self.t32api.T32_ReadVariableValue(symname, ctypes.byref(value), ctypes.byref(hvalue))
        if error != 0:
            print("Error in ReadVariableValue")

        return str(hex(value.value))

    def T32_GetAddress(self):
        #Get symbol from current address 
        pc_address = ctypes.c_uint32(0)
        symbol_name = (ctypes.c_char*256)()
        #Get address
        error = self.t32api.T32_ReadPP(ctypes.byref(pc_address))
        if error != 0:
            print("Error in GetAddress")

        return pc_address.value

    def T32_GetMessage(self):
        #Get message from Trace32 
        message = (ctypes.c_char*256)()
        type = ctypes.c_uint16(0)

        error = self.t32api.T32_GetMessage(message, ctypes.byref(type))
        if error != 0:
            print("Error in Getmessage")

        return message.value.decode()

    def T32_GetState(self):
        state = ctypes.c_int(-1)
        error = self.t32api.T32_GetState(ctypes.byref(state))
        return_value = ''
        
        if error != 0:
            print("Error in T32state")

        match state.value:
            case 0:
                return_value = 'down'
            case 1:
                return_value = 'boot'
            case 2:
                return_value = 'break'
            case 3:
                return_value = 'go'
            case _:
                return_value = 'error'

        return return_value

    def T32_BreakSet(self,name):
        #Get symbol from current address
        break_cmd = "break.set " + name
        error = self.t32api.T32_Cmd(bytes(break_cmd, encoding='UTF-8'))

        return error

    def T32_BreakDelete(self,name):
        #Get symbol from current address
        break_cmd = "break.delete " + name
        error = self.t32api.T32_Cmd(bytes(break_cmd, encoding='UTF-8'))

        return error

    def T32_VarSet(self,variant,value):
        #Set variant value
        set_cmd='Var.set '+variant+' = '+str(value)
        error = self.t32api.T32_Cmd(bytes(set_cmd, encoding='UTF-8'))

        return error

    def T32_ReadValue(self,name):
        #read symbol value
        vvalue = ctypes.c_uint32(0)
        vvalueh = ctypes.c_uint32(0)
        vname = name.encode('utf-8')
        error = self.t32api.T32_ReadVariableValue(vname,ctypes.byref(vvalue),ctypes.byref(vvalueh))
        if error != 0:
            print("Error in ReadValue")

        return vvalue.value

    def T32_ReadRegisterByName(self,name):
        #read symbol value
        vvalue = ctypes.c_uint32(0)
        vvalueh = ctypes.c_uint32(0)
        vname = name.encode('utf-8')
        error = self.t32api.T32_ReadRegisterByName(vname,ctypes.byref(vvalue),ctypes.byref(vvalueh))
        if error != 0:
            print("Error in ReadRegisterByName")

        return str(hex(vvalue.value))

    def T32_RteReadFinish(self):
        
        error = 1

        #Go.direct 0x5200
        pcAddress = self.T32_GetAddress()
        str_pcAddress = str(hex(pcAddress))
        str_pcAddress1000 = str(hex(pcAddress + 0x100))
        #find 0x007F jmp [r31]
        command = bytes("Data.Find "+str_pcAddress+"--"+str_pcAddress1000+" %Word 0x007F", encoding='UTF-8')
        self.t32api.T32_Cmd(command)
        message = self.T32_GetMessage()
        # print(message)
        if message.find('not found in') == -1 and message.find('found in') != -1:
            error = 0
            readAddress = message.split(':')[-1]
            command = bytes("Go.direct P:"+readAddress, encoding='UTF-8')
            self.t32api.T32_Cmd(command)
        else:
            print("Error in RteReadFinish")
        
        return error