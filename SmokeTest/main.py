from lib.DBCAnalyzer import DBCAnalyzer
from lib.zlgcan import *
from lib.TC import TC
import argparse
import logging
from loguru import logger
import time
import os
import sys


class Logger(object):
  def __init__(self, filename="default.txt", stream=sys.stdout):
    self.terminal = stream
    self.log = open(filename, "w")
	
  def write(self, message):
    self.terminal.write(message)
    self.log.write(message)
	
  def flush(self):
    pass


class InterceptHandler(logging.Handler):
    def emit(self, record):
        opt = logger.opt(depth=6, exception=record.exc_info)
        opt.remove()
        opt.add(sink=sys.stdout, format="{message}")
        opt.log(logger.level(record.levelname).name, record.getMessage())


def InputParamLoad(): 
    Parse = argparse.ArgumentParser()
    Parse.add_argument('-p', 
                        '--path',
                        nargs=1, 
                        type=str,
                        default=None, 
                        help="input project path")
    Parse.add_argument('-c', 
                        '--cfg', 
                        nargs=1,
                        type=str, 
                        default=None, 
                        help="input cfg path") 
    InputArgs = Parse.parse_args()
    if InputArgs.path == None:
        print('Please input project work path!')
        Parse.print_help() 
        exit(-1)
    if InputArgs.cfg == None:
        print('Please input project config file!')
        Parse.print_help()
        exit(-1)

    return InputArgs 

if __name__ == "__main__":
    # a_args = InputParamLoad()
    # project_path =  a_args.path[0] 
    # cfg_file_path = a_args.cfg[0]
    project_path =  "input\\"
    cfg_file_path = "lib\\DBCConfig.json"

    parser = argparse.ArgumentParser(description='')
    parser.add_argument('-p',
                        '--project',
                        nargs=1,
                        type=str,
                        default=None,
                        help="input project name:T1GC/E03")                  
    args = parser.parse_args()

    t_project_name = None
    if None != args.project:
        t_project_name = args.project[0]
    else:
        parser.print_help()
        exit(-1)

    if t_project_name not in ["T1GC","E03","E01"]:
        print("Error!!! Invalid project name!")
        exit(-1)

    localtime = time.localtime(time.time())
    timestamp = time.strftime('%Y%m%d-%H-%M-%S',localtime)
    log_file = "output/log_smoke_"+timestamp+".txt"

    if os.path.exists("output") == False:
        os.mkdir("output")

    output_handler = open(log_file,"w")
    sys.stdout = Logger(log_file, sys.stdout)
    sys.stderr = Logger(log_file, sys.stderr)

    for name in ["doipclient", "UdsClient", "Connection"]:
        if name not in logging.root.manager.loggerDict:
            continue
        # logging.getLogger(name).setLevel("ERROR")
        logging.getLogger(name).setLevel("DEBUG")
        logging.getLogger(name).handlers = []
        logging.getLogger(name).addHandler(InterceptHandler())

    print("Start testing...")
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S',localtime)
    print('Started:',timestamp)

    print("Step 1 DBC Analysis...")
    a_dbc_analyzer_obj = DBCAnalyzer(project_path, cfg_file_path)

    print("\nStep 2 Open Device...")
    zcanlib = ZCAN()
    handle = zcanlib.open_device()

    print("\nStep 3 Open Channel...")
    chn0_handle = zcanlib.canfd_start(handle, 0)
    print("channel0 handle:%d" %(chn0_handle))
    # chn1_handle = zcanlib.canfd_start(handle, 1)
    # print("channel1 handle:%d" %(chn1_handle))

    print("\nStep 4 Run Testcase...")
    tc = TC(t_project_name)
    chn0_handle = tc.start_test(a_dbc_analyzer_obj, zcanlib, handle, chn0_handle)
    time.sleep(1)

    print("\nStep 5 Close Channel...")
    ret=zcanlib.ResetCAN(chn0_handle)
    if ret==1:
        print("Close Channel0 success! ")
    # ret=zcanlib.ResetCAN(chn1_handle)
    # if ret==1:
    #     print("Close Channel1 success! ")

    print("\nStep 6 Close Device...")
    ret=zcanlib.CloseDevice(handle)
    if ret==1:
        print("Close Device success! ")

    output_handler.close() 
    print("\nFinished")
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))
    print('Ended:',timestamp)