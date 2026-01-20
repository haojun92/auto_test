# For Interface Test		
import time 				

basetype = {"uint8","uint16","uint32","int8","int16","int32","single","boolean"}

class test_result():
    def __init__(self):
        self.interface = ''
        self.provide = ''
        self.receive = ''
        self.write = ''
        self.read = ''
        self.variant = ''
        self.element = []
        self.array_name = ''
        self.if_datatype = ''
        self.map_status = True
        self.setvalue = [[],[]]
        self.getvalue = [[],[]]
        self.provide_find = False
        self.receive_find = False
        self.variant_find = False
        self.provide_stop = False
        self.receive_stop = False
        self.test_status = ''   #PASS/Fail/NA
        self.comments = ''

class tc_run():
    def __init__(self, testcases, t32):
        self.t32 = t32
        self.results = []

        self.t32.t32api.T32_Cmd(b"go")
        time.sleep(1)
        self.t32.t32api.T32_Cmd(b"break")
        self.t32.t32api.T32_Cmd('SYStem.Mode Attach')

        self.total = len(testcases)
        self.pass_cnt = 0
        self.fail_cnt = 0
        self.na_cnt = 0
        counter = 0

        for testcase in testcases:
            counter += 1
            # if counter > 10:
            #     break

            self.clear()
            self.interface = testcase.interface
            self.provide = testcase.provide
            self.receive = testcase.receive
            self.write = testcase.write
            self.read = testcase.read
            self.variant = testcase.variant
            self.element = testcase.element
            self.array_name = testcase.array_name
            self.if_datatype = testcase.if_datatype
            self.map_status = testcase.map_status

            print('\n*** Interface Number %d/%d ***'%(counter,self.total))
            print("Interface:",self.interface)
            print("Sender:",self.provide)
            print("Receiver:",self.receive)
            print("WriteIF:",self.write)
            print("ReadIF:",self.read)
            print("Variant:",self.variant)
            print("Element:",self.element)

            self.execute()
            self.add_result()

            if self.test_status == 'PASS':
                self.pass_cnt += 1
            elif self.test_status == 'Fail':
                self.fail_cnt += 1
            elif self.test_status == 'NA':
                self.na_cnt += 1
        
        print("\nTest Result:")
        print("Total: %d\nPass: %d\nFail: %d\nN.A.: %d"%(self.total,self.pass_cnt,self.fail_cnt,self.na_cnt))
        self.t32.t32api.T32_Cmd(b'SYStem.RESetTarget')
        time.sleep(1)
        self.t32.t32api.T32_Cmd(b'SYStem.Mode Attach')
        self.t32.t32api.T32_Cmd(b"go")
        
    def add_result(self):
        t_result = test_result()
        t_result.interface = self.interface
        t_result.provide = self.provide
        t_result.receive = self.receive
        t_result.write = self.write
        t_result.read = self.read
        t_result.variant = self.variant
        t_result.element = self.element
        t_result.array_name = self.array_name
        t_result.if_datatype = self.if_datatype
        t_result.map_status = self.map_status
        t_result.setvalue = self.setvalue
        t_result.getvalue = self.getvalue
        t_result.provide_find = self.provide_find
        t_result.receive_find = self.receive_find
        t_result.variant_find = self.variant_find
        t_result.provide_stop = self.provide_stop
        t_result.receive_stop = self.receive_stop
        t_result.test_status = self.test_status
        t_result.comments = self.comments
        self.results.append(t_result)


    def clear(self):
        self.interface = ''
        self.provide = ''
        self.receive = ''
        self.write = ''
        self.read = ''
        self.variant = ''
        self.element = []
        self.array_name = ''
        self.map_status = True
        self.setvalue = [[],[]]
        self.getvalue = [[],[]]
        self.provide_find = False
        self.receive_find = False
        self.variant_find = False
        self.provide_stop = False
        self.receive_stop = False
        self.test_status = ''   #PASS/Fail/NA
        self.comments = ''


    def interface_check(self):
        #check rte write
        if self.t32.T32_BreakSet(self.write) == 0:
            self.provide_find = True
            self.t32.t32api.T32_Cmd(b"go")
            time.sleep(0.5)
            if self.t32.T32_GetState() == 'break':
                self.provide_stop = True
            else:
                self.t32.t32api.T32_Cmd(b"break")

            self.t32.T32_BreakDelete(self.write)

        #check rte read
        if self.t32.T32_BreakSet(self.read) == 0:
            self.receive_find = True
            self.t32.t32api.T32_Cmd(b"go")
            time.sleep(0.5)
            if self.t32.T32_GetState() == 'break':
                self.receive_stop = True
            else:
                self.t32.t32api.T32_Cmd(b"break")

            self.t32.T32_BreakDelete(self.read)

        # self.t32.t32api.T32_Nop()
        # self.t32.t32api.T32_Cmd(b"AREA.CLEAR")

        self.t32.t32api.T32_Cmd(b"ERROR.RESet")
        self.t32.t32api.T32_Cmd('SYStem.Mode Attach')

        #check variant
        if self.t32.T32_GetSymbol(self.variant) != 0xffffffff:
            self.variant_find = True

        #init setvalue
        if (self.provide_stop == True and self.receive_stop == True) or ((self.provide_stop == True or self.receive_stop == True) and self.variant_find == True):
            for i in range(len(self.element)):
                self.setvalue[0].append(0)
                self.setvalue[1].append(1)

    def p_test(self):
        #check write interface
        self.t32.T32_BreakSet(self.write)
        self.t32.t32api.T32_Cmd(b"go")
        time.sleep(0.5)

        for value_index in range(len(self.setvalue)):
            if self.t32.T32_GetSymbolFromAddress() == self.write:
                #set value
                for element_index in range(len(self.element)):
                    if self.array_name != '':
                        self.t32.T32_VarSet('(*((('+self.array_name+'*)data)))'+self.element[element_index],self.setvalue[value_index][element_index])
                    else:
                        self.t32.T32_VarSet('(*(data))'+self.element[element_index],self.setvalue[value_index][element_index])
                    
                print("SetValue:",self.setvalue[value_index])

                self.t32.T32_RteReadFinish()
                time.sleep(0.2)

                #read value
                for element_index in range(len(self.element)):
                    self.getvalue[value_index].append(self.t32.T32_ReadValue(self.variant+self.element[element_index]))

                print("GetValue:",self.getvalue[value_index])

            if self.setvalue[value_index] != self.getvalue[value_index]:
                self.test_status = 'Fail'
                self.comments = self.comments + 'The variant value is inconsistent with the provided.'
                break
            elif value_index == len(self.setvalue)-1:
                self.test_status = 'PASS'
                self.comments = self.comments + 'Write interface test pass.'

            self.t32.t32api.T32_Cmd(b"go")
            time.sleep(0.5)

        #delete breakpoints
        self.t32.t32api.T32_Cmd(b"break.delete")
        #t32 stop
        self.t32.t32api.T32_Cmd(b"break")

    def r_test(self):
        #check read interface
        self.t32.T32_BreakSet(self.read)
        self.t32.t32api.T32_Cmd(b"go")
        time.sleep(0.5)

        for value_index in range(len(self.setvalue)):
            if self.t32.T32_GetSymbolFromAddress() == self.read:
                #set value
                for element_index in range(len(self.element)):
                    self.t32.T32_VarSet(self.variant+self.element[element_index],self.setvalue[value_index][element_index])

                print("SetValue:",self.setvalue[value_index])

                data_address = self.t32.T32_ReadRegisterByName("R6")
                self.t32.T32_RteReadFinish()
                time.sleep(0.2)

                #read value
                for element_index in range(len(self.element)):
                    self.getvalue[value_index].append(self.t32.T32_ReadValue('(*((('+self.if_datatype+'*)'+data_address+')))'+self.element[element_index]))
                
                print("GetValue:",self.getvalue[value_index])

            if self.setvalue[value_index] != self.getvalue[value_index]:
                self.test_status = 'Fail'
                self.comments = self.comments + 'The received value is inconsistent with variant.'
                break
            elif value_index == len(self.setvalue)-1:
                self.test_status = 'PASS'
                self.comments = self.comments + 'Read interface test pass.'

            self.t32.t32api.T32_Cmd(b"go")
            time.sleep(0.5)

        #delete breakpoints
        self.t32.t32api.T32_Cmd(b"break.delete")
        #t32 stop
        self.t32.t32api.T32_Cmd(b"break")

    def pr_test(self):
        #check write and read interface
        self.t32.T32_BreakSet(self.write)
        self.t32.t32api.T32_Cmd(b"go")
        time.sleep(0.5)
        self.t32.T32_BreakSet(self.read)

        for value_index in range(len(self.setvalue)):
            write_flag = False
            counter = 100
            while counter > 0:
                counter -= 1
                
                if self.t32.T32_GetSymbolFromAddress() == self.write:
                    #set value
                    write_flag = True
                    for element_index in range(len(self.element)):
                        if self.array_name != '':
                            self.t32.T32_VarSet('(*((('+self.array_name+'*)data)))'+self.element[element_index],self.setvalue[value_index][element_index])
                        else:
                            self.t32.T32_VarSet('(*(data))'+self.element[element_index],self.setvalue[value_index][element_index])

                    print("SetValue:",self.setvalue[value_index])

                elif self.t32.T32_GetSymbolFromAddress() == self.read and write_flag == True:
                    data_address = self.t32.T32_ReadRegisterByName("R6")
                    self.t32.T32_RteReadFinish()
                    time.sleep(0.2)

                    #read value
                    for element_index in range(len(self.element)):
                        self.getvalue[value_index].append(self.t32.T32_ReadValue('(*((('+self.if_datatype+'*)'+data_address+')))'+self.element[element_index]))
                    
                    print("GetValue:",self.getvalue[value_index])
                    break

                self.t32.t32api.T32_Cmd(b"go")
                time.sleep(0.5)

            if self.setvalue[value_index] != self.getvalue[value_index]:
                self.test_status = 'Fail'
                self.comments = 'The received value is inconsistent with the provided.'
                break
            elif value_index == len(self.setvalue)-1:
                self.test_status = 'PASS'
                self.comments = 'Write and read interface test pass.'

        #delete breakpoints
        self.t32.t32api.T32_Cmd(b"break.delete")
        #t32 stop
        self.t32.t32api.T32_Cmd(b"break")

    def execute(self):
        if self.map_status == False:
            self.test_status = 'NA'
            self.comments = 'No port to map.'
        else:
            self.interface_check()
            if self.provide_find == False and self.receive_find == False and self.if_datatype in basetype:
                self.test_status = 'NA'
                self.comments = 'Atomic data type.'

            elif self.provide_find == False and self.receive_find == False:
                self.test_status = 'Fail'
                self.comments = 'Not find write and read interface.'

            elif self.provide_find == False:
                self.test_status = 'Fail'
                self.comments = 'Not find write interface.'

            elif self.receive_find == False:
                self.test_status = 'Fail'
                self.comments = 'Not find read interface.'

            elif self.provide_stop == True and self.receive_stop == True:
                self.pr_test()

            elif self.provide_stop == True:
                self.comments = 'Read interface not be called.'
                if self.variant_find == False:
                    self.test_status = 'Fail'
                    self.comments = self.comments+'Not find variant.'
                else:
                    self.p_test()

            elif self.receive_stop == True:
                self.comments = 'Write interface not be called.'
                if self.variant_find == False:
                    self.test_status = 'Fail'
                    self.comments = self.comments+'Not find variant.'
                else:
                    self.r_test()

            else:
                self.test_status = 'NA'
                self.comments = 'Interfaces not be called.'

        print("TestStatus:",self.test_status)
        print("Comments:",self.comments)