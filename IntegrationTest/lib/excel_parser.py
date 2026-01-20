import pandas as pd
import re
from collections import defaultdict

class swc():
    def __init__(self, name):
        self.name = name
        self.runnables = []
        self.events = []
        self.ports = []

    def add_runnable(self, runnable):
        self.runnables.append(runnable)

    def add_event(self, event):
        self.events.append(event)

    def add_port(self, port):
        self.ports.append(port)
        
class interface():
    def __init__(self, name, datatype, element, queued):
        self.name = name
        self.datatype = datatype
        self.element = element
        self.queued = queued
         
class ib_event():
    def __init__(self, name, runnable, timing_period=None, target=None, port=None):
        self.name = name
        self.runnable = runnable
        self.timing_period = timing_period
        self.target = target
        self.port = port

class cp_port():
    def __init__(self, name, direction, datatype, element, queued, queue_len, update='N',access_point=None):
        self.name = name
        self.direction = direction
        self.datatype = datatype
        self.access_point = access_point
        self.valid = True
        self.element = element
        self.queued = queued
        self.queue_len = queue_len
        self.update = update

class datatype():
    def __init__(self,name):
        self.name = name
        self.type = None
        self.members = {}
        self.array_size = -1
        self.datatype = None

class port_mapping():
    def __init__(self,name):
        self.name = name
        self.sender_swc = ''
        self.receiver_swcs = []

class excel_parser():
    def __init__(self):
        self.sheets = {}
        self.swcs = []
        self.interfaces = []
        self.datatypes = []
        self.excel_version_info = ''
        self.mappings = []

    def read_sheet_from_excel(self, file_path, project_name, logging):
        interface_platform_sheet = pd.read_excel(file_path, sheet_name='Interface_Platform', engine='openpyxl', skiprows=1, header=None)
        interface_vehicle_sheet = pd.read_excel(file_path, sheet_name='Interface_{}'.format(project_name), engine='openpyxl', skiprows=1, header=None)
        self.sheets['interface_sheet'] = pd.concat([interface_platform_sheet,interface_vehicle_sheet],ignore_index=True)
        datatype_platform_sheet = pd.read_excel(file_path, sheet_name='DataType_Platform', engine='openpyxl', skiprows=1, header=None)
        datatype_vehicle_sheet = pd.read_excel(file_path, sheet_name='DataType_{}'.format(project_name), engine='openpyxl', skiprows=1, header=None)
        self.sheets['datatype_sheet'] = pd.concat([datatype_platform_sheet,datatype_vehicle_sheet],ignore_index=True)
        self.sheets['internalbehavior_sheet'] = pd.read_excel(file_path, sheet_name='InternalBehavior', header=None, usecols="A:F", skiprows=1)
        self.sheets['ChangeHistory'] = pd.read_excel(file_path, sheet_name='ChangeHistory', engine='openpyxl', skiprows=1, header=None)

    def parse_version_info_from_excel(self,logging):
        row_number = self.sheets['ChangeHistory'].shape[0] - 1
        self.excel_version_info = 'Version: {}, Author: {}, ChangeInfo: {}'.format(self.sheets['ChangeHistory']._values[row_number][0], self.sheets['ChangeHistory']._values[row_number][2], self.sheets['ChangeHistory']._values[row_number][6])

    def parse_interfaces_from_excel(self,logging):
        seen_names = set()

        for _, row in self.sheets['interface_sheet'].iterrows():
            t_type = row[2]
            t_name = row[3]
            if t_type == 'S/R':
                t_datatype = row[4] 
                t_dataelement = row[3]
                t_queued = row[8]
            elif t_type == 'C/S':
                logging.info("Need create CS Interface related for {}.".format(t_name))
            else:
                logging.error("Invalid PortType of {}!!!".format(t_name))

            
            if t_name not in seen_names:
                seen_names.add(t_name)
                if t_type == 'S/R':
                    self.interfaces.append(interface(t_name, t_datatype, t_dataelement,t_queued))

    def parse_datatypes_from_excel(self,logging):
        seen_names = set()
        current_datatype = None

        for _, row in self.sheets['datatype_sheet'].iterrows():
            t_name = row[0]
            t_datatype_type = row[3]
            t_array_size = row[4]
            t_member_name = row[2]
            if t_name in seen_names:
                logging.error("Duplicated Datatype {} in excel file".format(t_name))
            if pd.notna(t_name):  # if the name is not NaN, then we are starting a new datatype
                t_name = re.sub(r'\s+', '', t_name)
                if current_datatype is not None:  # if there is a current datatype, add it to the list
                    seen_names.add(t_name)
                    self.datatypes.append(current_datatype)
                current_datatype = datatype(t_name)
                if t_datatype_type == 'Struct':
                    current_datatype.type = 'STRUCTURE'
                elif t_array_size == 1:
                    current_datatype.type = 'TYPE_REFERENCE'
                    current_datatype.datatype = t_datatype_type
                elif t_array_size > 1:
                    current_datatype.type = 'ARRAY'
                    current_datatype.datatype = t_datatype_type
                    current_datatype.array_size = int(t_array_size)
                elif t_datatype_type == 'Enum':
                    current_datatype.type = 'Enum'
            elif current_datatype is not None and current_datatype.type == 'STRUCTURE':
                t_member_name = re.sub(r'\s+', '', t_member_name)
                # if the name is NaN, but we are in the middle of a struct datatype
                t_array_datatype_name = "rt_Array_" + t_datatype_type + "_" + str(t_array_size).split(".")[0]
                if t_array_size > 1 and t_array_datatype_name not in seen_names:
                    current_datatype.members[t_member_name] = t_array_datatype_name
                    array_datatype = datatype(t_array_datatype_name)
                    array_datatype.array_size = int(t_array_size)
                    array_datatype.datatype = t_datatype_type
                    array_datatype.type = 'ARRAY'
                    seen_names.add(t_array_datatype_name)
                    self.datatypes.append(array_datatype)
                elif t_array_size > 1: 
                    current_datatype.members[t_member_name] = t_array_datatype_name
                elif t_array_size == 1:
                    current_datatype.members[t_member_name] = t_datatype_type
            elif current_datatype is not None and current_datatype.type == 'Enum':
                t_member_name = re.sub(r'\s+', '', t_member_name)
                current_datatype.members[t_member_name] = t_datatype_type
                
        if current_datatype is not None:  # add the last datatype to the list
            seen_names.add(t_name)
            self.datatypes.append(current_datatype)

    def parse_internal_behavior_sheet(self,logging):

        # Create a dictionary to hold the SWC objects
        swc_dict = {}
        current_swc_name = None

        for _, row in self.sheets['internalbehavior_sheet'].iterrows():
            t_swc_name = row[0]
            t_runnable = row[1]
            t_event = row[2]
            t_timing_period = row[3]
            t_target = row[4]
            t_port = row[5]

            # Check if we are starting a new SWC
            if pd.notna(t_swc_name) and t_swc_name != current_swc_name:
                current_swc_name = t_swc_name
                swc_dict[current_swc_name] = swc(current_swc_name)

            # Add the runnable to the SWC
            if pd.notna(t_runnable):
                swc_dict[current_swc_name].add_runnable(t_runnable)

            # Create and add the event to the SWC
            if pd.notna(t_event):
                if t_event == "TimingEvent" and pd.notna(t_timing_period):
                    event_obj = ib_event(t_event, t_runnable, t_timing_period)
                elif t_event == "InitEvent":
                    event_obj = ib_event(t_event, t_runnable)
                elif t_event == "OperationInvokedEvent" and pd.notna(t_target) and pd.notna(t_port):
                    event_obj = ib_event(t_event, t_runnable, t_timing_period, t_target, t_port)
                elif t_event == "BackgroundEvent":
                    event_obj = ib_event(t_event, t_runnable)
                else:
                    logging.error("Invalid Event {} in excel file".format(t_runnable))

                swc_dict[current_swc_name].add_event(event_obj)

        # Convert the dictionary to a list of SWC objects
        self.swcs = list(swc_dict.values())
    
    def parse_port_from_excel(self,logging):

        # Create a dictionary to hold the SWC objects
        swc_dict = {swc.name: swc for swc in self.swcs}

        for _, row in self.sheets['interface_sheet'].iterrows():
            t_swc_name = row[0]
            t_direction = row[1]
            t_type = row[2]
            t_port_name = row[3]
            t_datatype = row[4]
            t_access_point = row[7]
            t_dataelement = row[3]
            t_queued = row[8]
            t_queue_length = row[9]
            t_update = row[12]
            if t_type == 'S/R':
                # Create the Port object
                if pd.notna(t_access_point) and pd.notna(t_direction) and pd.notna(t_port_name) and pd.notna(t_datatype):
                    t_port = cp_port(t_port_name, t_direction, t_datatype, t_dataelement, t_queued, t_queue_length,t_update, t_access_point)
                else:
                    logging.error("Invalid Port {} in {}".format(t_port_name, t_swc_name))

                # Add the port to the SWC
                if t_swc_name in swc_dict:
                        swc_dict[t_swc_name].add_port(t_port)
                else:
                    # Create a new SWC and add it to the dictionary if the swc's name is not in swc_list
                    new_swc = swc(t_swc_name)
                    new_swc.add_port(t_port)
                    swc_dict[t_swc_name] = new_swc

        # Convert the dictionary back to a list of SWC objects
        self.swcs = list(swc_dict.values())
    
    def find_ports_with_mismatched_direction(self, logging):
        # 使用字典存储每个名称的方向集合
        name_to_directions = defaultdict(set)
        # 使用字典存储每个名称的swc
        name_to_swc = defaultdict(list)

        # 遍历端口列表，收集每个名称的方向集合和swc
        for swc in self.swcs:
            for port in swc.ports:
                name_to_directions[port.name].add(port.direction)
                name_to_swc[port.name].append(swc.name)

        # 找到方向不匹配的端口名称
        mismatched_names = [name for name, directions in name_to_directions.items() if len(directions) <= 1]

        for name in mismatched_names:
            swcs = name_to_swc[name]
            for swc_name in swcs:
                logging.warning("Can't find name matched port of {} in {}".format(name, swc_name))

    def find_ports_mapping(self, logging):
        # 使用字典存储每个port的接收方和发送方
        port_sender_swc = defaultdict(list)
        port_receive_swc = defaultdict(list)
        ports = set()

        # 遍历端口列表，收集每个port的swc
        for swc in self.swcs:
            for port in swc.ports:
                ports.add(port.name)
                if port.direction == "Inport":
                    port_receive_swc[port.name].append(swc.name)
                elif port.direction == "Outport":
                    port_sender_swc[port.name].append(swc.name)
                else:
                    raise Exception("Port direction is wrong:"+port)
        ports_list = list(ports)
        ports_list_sorted = sorted(ports_list)
        for port in ports_list_sorted:
            mapping = port_mapping(port)
            # if len(port_sender_swc[port]) < 1 or len(port_receive_swc[port]) < 1:
            #     print(port)
            if len(port_sender_swc[port]) > 1:
                raise Exception("Duplicate output port:"+port)     
            elif len(port_sender_swc[port]) == 1:           
                mapping.sender_swc = port_sender_swc[port][0]
            mapping.receiver_swcs = port_receive_swc[port]
            self.mappings.append(mapping)

    def parse_excel(self,t_excel_path,project_name,logging):
        self.read_sheet_from_excel(t_excel_path,project_name,logging)
        # self.parse_version_info_from_excel(logging)
        self.parse_interfaces_from_excel(logging)
        self.parse_datatypes_from_excel(logging)
        # self.parse_internal_behavior_sheet(logging)
        self.parse_port_from_excel(logging)
        # self.find_ports_with_mismatched_direction(logging)
        self.find_ports_mapping(logging)






