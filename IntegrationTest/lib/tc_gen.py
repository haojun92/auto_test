import json


class testcase():
    def __init__(self, name):
        self.interface = name
        self.provide = ""
        self.receive = ""
        self.write = ""
        self.read = ""
        self.variant = ""
        self.element = []
        self.array_name = ""
        self.if_datatype = ""
        self.map_status = True

class tc_gen():
    def __init__(self, ep):
        self.ep = ep
        self.basetype = {"uint8","uint16","uint32","uint64","int8","int16","int32","int64","single","double","boolean"}
        self.elements = []
        self.testcases = []

        for mapping in self.ep.mappings:
            self.elements = []
            #check mapping status
            if mapping.sender_swc == '':
                for receiver_swc in mapping.receiver_swcs:
                    t_testcase = testcase(mapping.name)
                    t_testcase.map_status = False
                    t_testcase.receive = receiver_swc
                    t_testcase.read = "Rte_Read_"+receiver_swc+"_"+mapping.name+"_"+mapping.name
                    self.testcases.append(t_testcase)

            elif len(mapping.receiver_swcs) < 1:
                t_testcase = testcase(mapping.name)
                t_testcase.map_status = False
                t_testcase.provide = mapping.sender_swc
                t_testcase.write = "Rte_Write_"+mapping.sender_swc+"_"+mapping.name+"_"+mapping.name
                t_testcase.variant = "Rte_"+mapping.sender_swc+"_"+mapping.name+"_"+mapping.name
                self.testcases.append(t_testcase)
                
            else:
                #find datatype
                t_datatype = ''
                for swc in self.ep.swcs:
                    if swc.name == mapping.sender_swc:
                        for port in swc.ports:
                            if port.name == mapping.name:
                                t_datatype = port.datatype
                                break
                        break

                #find elements
                self.datatype_ref(t_datatype,"")
                t_array_name = ""
                for datatype in self.ep.datatypes:
                    if datatype.name == t_datatype:
                        if datatype.type == "ARRAY":
                            t_array_name = datatype.name
                        break
                
                for receiver_swc in mapping.receiver_swcs:
                    t_testcase = testcase(mapping.name)
                    t_testcase.provide = mapping.sender_swc
                    t_testcase.receive = receiver_swc
                    t_testcase.write = "Rte_Write_"+mapping.sender_swc+"_"+mapping.name+"_"+mapping.name
                    t_testcase.read = "Rte_Read_"+receiver_swc+"_"+mapping.name+"_"+mapping.name
                    t_testcase.variant = "Rte_"+mapping.sender_swc+"_"+mapping.name+"_"+mapping.name
                    t_testcase.element = self.elements.copy()
                    t_testcase.array_name = t_array_name
                    t_testcase.if_datatype = t_datatype
                    self.testcases.append(t_testcase)


    def datatype_ref(self, t_datatype, element_name):
        for datatype in self.ep.datatypes:
            if datatype.name == t_datatype:
                if datatype.type == "STRUCTURE":
                    for member,datatype in datatype.members.items():
                        if datatype in self.basetype:
                            self.elements.append(element_name+"."+member)
                        else:
                            self.datatype_ref(datatype,element_name+"."+member)

                elif datatype.type == "ARRAY":
                    for index in range(datatype.array_size):
                        if datatype.datatype in self.basetype and datatype.name == ("rt_Array_"+datatype.datatype+"_"+str(datatype.array_size)) :
                            self.elements.append(element_name+"["+str(index)+"]")
                        elif datatype.datatype in self.basetype:
                            self.elements.append(element_name+"["+str(index)+"]."+datatype.name)
                        else:
                            self.datatype_ref(datatype.datatype,element_name+"["+str(index)+"]")
                        
                elif datatype.type == "TYPE_REFERENCE":
                    if datatype.datatype in self.basetype:
                        self.elements.append(element_name+"."+datatype.name)
                    else:
                        self.datatype_ref(datatype.datatype,element_name+"."+datatype.name)

                elif datatype.type == "Enum":
                    self.elements.append(element_name)

                else:
                    raise Exception("Unknown type of datatype") 
                break
        

def tc_output(results, fail_file):
    fail_tc_list = []
    for result in results:
        if result.test_status == 'Fail':
            t_testcase = {}
            t_testcase["interface"] = result.interface
            t_testcase["provide"] = result.provide
            t_testcase["receive"] = result.receive
            t_testcase["write"] = result.write
            t_testcase["read"] = result.read
            t_testcase["variant"] = result.variant
            t_testcase["element"] = result.element
            t_testcase["array_name"] = result.array_name
            t_testcase["if_datatype"] = result.if_datatype
            t_testcase["map_status"] = result.map_status
            fail_tc_list.append(t_testcase)

    with open(fail_file, 'w') as f:
        json.dump(fail_tc_list, f, indent=2)


def tc_input(json_file):
    with open(json_file, 'r') as f:
        json_file_list = json.load(f)

    tc_list = []

    for tc in json_file_list:
        t_testcase = testcase(tc["interface"])
        t_testcase.provide = tc["provide"]
        t_testcase.receive = tc["receive"]
        t_testcase.write = tc["write"]
        t_testcase.read = tc["read"]
        t_testcase.variant = tc["variant"]
        t_testcase.element = tc["element"]
        t_testcase.array_name = tc["array_name"]
        t_testcase.if_datatype = tc["if_datatype"]
        t_testcase.map_status = tc["map_status"]
        tc_list.append(t_testcase)

    return tc_list