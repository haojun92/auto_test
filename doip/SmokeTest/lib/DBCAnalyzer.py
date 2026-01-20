import cantools
import json
import os

class CanChannel:
    def __init__(self, node, channel_name, can_type, arbi_baudr, data_baudr):
        self.node = node
        self.channel_name = channel_name
        self.can_type = can_type
        self.arbi_baudr = arbi_baudr
        self.data_baudr = data_baudr
        self.dbc_file_list = []
        self.tx_msg_list = []
        self.rx_msg_list = []

    def AnalyzerDbcFile(self):
        for dbc in self.dbc_file_list:
            db = cantools.database.load_file(dbc)
            for message in db.messages:
                tx_nodes = message.senders
                if self.node in tx_nodes:
                    self.tx_msg_list.append(message)
                else:    
                    rx_nodes = set() 
                    for signal in message.signals:
                        rx_nodes.update(signal.receivers)
                    if self.node in rx_nodes:
                        self.rx_msg_list.append(message)   
                                         
class DBCAnalyzer:
    def __init__(self, project_path, dbc_cfg_json):
        print("Analyzer Dbc File Start...")
        self.project_path = project_path
        self.dbc_cfg_file = open(dbc_cfg_json, 'r')
        self.dbc_cfg_content = json.load(self.dbc_cfg_file)   
        self.dbc_node = self.dbc_cfg_content.get("NODE")
        self.channel_list = self.dbc_cfg_content.get("ChannelList")
        self.search_path  = self.dbc_cfg_content.get("SearchPath")
        self.search_path = [project_path + Dir for Dir in self.search_path  ]
        self.channel_obj_list = []

        for Channel in self.channel_list:
            a_can_channel_obj =  CanChannel(self.dbc_node, Channel.get("Channel_Name"), Channel.get("CAN_Type"), Channel.get("Arbi_BaudR"), Channel.get("Data_BaudR"))
            a_can_channel_obj.dbc_file_list = self.Get_Src_Files(Channel.get("DBC_List", []), self.search_path)
            a_can_channel_obj.AnalyzerDbcFile()
            self.channel_obj_list.append(a_can_channel_obj)
        print("Analyzer Dbc File Done ...")

    def Get_Src_Files(self,file_names, Inc_Dirlist):
        Temp_Files = []
        for srcdir in Inc_Dirlist:
            if not os.path.exists(srcdir):
                print('ERROR: ' + srcdir + ' does not exist!')
                exit(-1)    
            for path, subdirs, files in os.walk(srcdir):
                for file in files:
                    if file.endswith('.dbc') and ((file in file_names) or ("FCM_DA" in file)):
                        Temp_Files.append(os.path.join(path, file))
        return Temp_Files


