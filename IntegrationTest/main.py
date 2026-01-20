# For Interface Test
import os 	
import sys		
import time 		
import json 		
import argparse
import lib.excel_parser as excel_parser
import lib.log as log
import lib.t32_launch as t32_launch
import lib.tc_gen as tc_gen
import lib.tc_run as tc_run
import lib.excel_gen as excel_gen
from lib.dh1766 import *

class Logger(object):
  def __init__(self, filename="default.txt", stream=sys.stdout):
    self.terminal = stream
    self.log = open(filename, "w")
	
  def write(self, message):
    self.terminal.write(message)
    self.log.write(message)
	
  def flush(self):
    pass

if __name__ == "__main__":

    localtime = time.localtime(time.time())
    timestamp = time.strftime('%Y%m%d-%H-%M-%S',localtime)
    log_file = "output/log_"+timestamp+".txt"
    result_file = "output/result_"+timestamp+".xlsx"
    fail_file = "output/fail_"+timestamp+".json"

    if os.path.exists("output") == False:
        os.mkdir("output")

    output_handler = open(log_file,"w")
    sys.stdout = Logger(log_file, sys.stdout)
    sys.stderr = Logger(log_file, sys.stderr)

    print("\nStart testing...")
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S',localtime)
    print('Started:',timestamp)

    parser = argparse.ArgumentParser(description='')
    parser.add_argument('-ep',
                        '--excel_path',
                        nargs=1,
                        type=str,
                        default=None,
                        help="input excel file path")
    parser.add_argument('-p',
                        '--project',
                        nargs=1,
                        type=str,
                        default=None,
                        help="input project name:T1GC/E03")  
    parser.add_argument('-tc',
                        '--json_path',
                        nargs=1,
                        type=str,
                        default=None,
                        help="input json file path")                  
    args = parser.parse_args()

    #failed testcase
    t_json_path = None
    if None != args.json_path:
        t_json_path = args.json_path[0]

    #full test
    if t_json_path == None:

        t_excel_path = None
        if None != args.excel_path:
            t_excel_path = args.excel_path[0]
        else:
            parser.print_help()
            exit(-1)

        t_project_name = None
        if None != args.project:
            t_project_name = args.project[0]
        else:
            parser.print_help()
            exit(-1)

        if t_project_name not in ["T1GC","E03","E01"]:
            print("Error!!! Invalid project name!")
            exit(-1)

        logging = log.setup_logger('log','output/log.txt')

        ep = excel_parser.excel_parser()
        ep.parse_excel(t_excel_path, t_project_name, logging)

        tc = tc_gen.tc_gen(ep)
        tc_list = tc.testcases
    #test failed testcase
    else:
        tc_list = tc_gen.tc_input(t_json_path)

    dh1766setvolt(12,12,0)
    dh1766onall()
    t32 = t32_launch.T32_Launch()

    it = tc_run.tc_run(tc_list, t32)

    #output failed testcase
    tc_gen.tc_output(it.results, fail_file)

    excel_gen.excel_gen(it.results, result_file)

    #exit t32
    t32.t32api.T32_Cmd(b"quit")

    output_handler.close() 
    print("\nFinished")
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))
    print('Ended:',timestamp)