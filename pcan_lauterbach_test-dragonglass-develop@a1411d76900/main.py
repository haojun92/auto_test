"""
主程序
"""
import time
import copy

from core.can_fd import MyCanFD
from core.lauterbach_c import MyLauterbach
from core.pd_xls import MyXls
from config import dbc_file, excel_case_file, excel_sheet_name
from core.judgement import Judgement


class CANoeLauterbachTest:
    def __init__(self):
        # 初始化excel
        self.my_xls = MyXls(excel_case_file)
        self.my_can_fd = MyCanFD(dbc_file)
        self.dbc_msg_dict = self.my_can_fd.load_dbc()
        self.dbc_variables_info = self.my_can_fd.get_dbc_variables_info()

        self.my_lauterbach = MyLauterbach()

        self.xls_df = self.my_xls.read_excel(excel_sheet_name)

    def can_send(self, msg_name: str, data_dict: dict, send_times=5):
        """
        can发送
        :param send_times: 发送次数
        :param data_dict:
        :param msg_name:
        :return:
        """
        flag = 1
        # 检查是否有该msg_name
        _msg_name_dict = copy.deepcopy(self.dbc_msg_dict.get(msg_name, {}))
        _msg_name_dict.update(data_dict)
        # if(_msg_name_dict[''])
        print(f"发送:{_msg_name_dict}")
        for _ in range(send_times):
            try:
                self.my_can_fd.write(
                    msg_name=msg_name,
                    msg=_msg_name_dict
                )
            except Exception as e:
                print(f"can发送{msg_name}的数据{data_dict}错误，{e}")
                flag = 0
            else:
                print(f"can发送{msg_name}的数据{data_dict}成功.")
                flag = 1
            time.sleep(0.05)
        return flag

    def lauterbach_receive(self, variable_full_name: str, receive_times: int = 5):
        """
        劳德巴赫接收
        :return:
        """
        flag = 1  # 成功
        res = float("-inf")
        for _ in range(receive_times):
            try:
                res = self.my_lauterbach.read(variable_full_name)
            except Exception as e:
                print(f"劳德巴赫接收{variable_full_name}错误,{e}")
                res = -99999
                # res = float("-inf")
                flag = 0  # 失败
            else:
                flag = 1

        return flag, res

    @classmethod
    def count_float_point(cls, value):
        """
        计算小数位数
        :param value:
        :return:
        """
        return len(str(value).split(".")[1]) if len(str(value).split(".")) > 1 else 0

    def test(self):
        """
        开始测试
        :return:
        """
        # 遍历excel的每行数据
        for row in self.xls_df.itertuples():
            # 获取用例编号
            test_case_num = getattr(row, "Index")
            message_name = getattr(row, "Message_Name")
            can_signal = getattr(row, "CAN_Signal")

            rte_port_data_name = getattr(row, "RTE_Port_Data_Name")
            rte_port_element_name = getattr(row, "RTE_Port_Element_Name")
            # 拼接变量名
            variable_full_name = f"{rte_port_data_name}.{rte_port_element_name}"

            # 如果test_values和test_expected_values都存在,就使用这两个值进行测试
            test_values = getattr(row, "Test_Values")
            test_expected_values = getattr(row, "Test_Expected_Values")
            if str(test_values) == "nan" or str(test_expected_values) == "nan":
                # 有一个是空的,就用dbc的数
                # 获取目标值类型
                rte_port_element_type = self.xls_df.loc[test_case_num, "RTE_Port_Element_Type"]
                types_map = {
                    "uint8": int,
                    "uint16": int,
                    "uint32": int,
                    "uint64": int,
                    "float32": float,
                    "float64": float,
                    "boolean": bool
                }

                # 发送can
                # 获取数据范围
                msg_variables_info = self.dbc_variables_info.get(message_name, {})
                variable_info = msg_variables_info.get(can_signal, {})
                variable_max = variable_info.get("max")
                variable_min = variable_info.get("min")
                # 中间值
                # v_tmp = (variable_max+variable_min)/2
                variable_mid = (variable_max+variable_min)/2
                variable_mid = round(variable_mid, 1)
                variable_mid = types_map.get(rte_port_element_type, float)(variable_mid)
                # if variable_max == 1 and variable_min == 0:
                #     variable_mid = 1
                # elif isinstance(variable_max, bool) or isinstance(variable_min, bool):
                #     variable_mid = 1
                # else:
                # # elif isinstance(variable_max, float) or isinstance(variable_min, float):
                #     # 判断有几位小数
                #     point_num = max(self.count_float_point(variable_max), self.count_float_point(variable_min))
                #     # 保留一位小数
                #     variable_mid = round(variable_mid, point_num)
                # # elif isinstance(variable_max, int) and isinstance(variable_min, int):
                # #     # 整数
                # #
                # #
                # # else:
                # #     variable_min = variable_max or variable_min
                # # variable_mid = variable_mid if isinstance(variable_max, type())
                variable_range = f"{variable_min}~{variable_max}"
                test_values_ = [variable_min]

                if variable_mid == 0:
                    # 增加1/4和3/4的值
                    variable_mid_1_4 = types_map.get(rte_port_element_type, float)(round((variable_min+variable_mid)/2
                                                                                         ))

                    test_values_.append(variable_mid_1_4)
                test_values_.append(variable_mid)
                if variable_mid == 0:
                    variable_mid_3_4 = types_map.get(rte_port_element_type, float)(
                        round((variable_mid + variable_max) / 2))
                    test_values_.append(variable_mid_3_4)
                test_values_.append(variable_max)
                # test_values_ = list({variable_min, variable_max})
                test_expected_values_ = test_values_
                # test_values_ = [test_values_] if isinstance(test_values_, int) else test_values_
                self.xls_df.loc[test_case_num, "Range"] = str(variable_range)
                self.xls_df.loc[test_case_num, "Test_Values"] = str(test_values_)
                self.xls_df.loc[test_case_num, "Test_Expected_Values"] = str(test_expected_values_)
            else:
                test_values_ = eval(test_values)
                test_expected_values_ = eval(test_expected_values)

            test_actual_values = []
            for i, test_value in enumerate(test_values_):
                # 循环发送和判断
                # 发送
                self.can_send(msg_name=message_name, data_dict={can_signal: test_value})
                # 接收
                receive_flag, res = self.lauterbach_receive(variable_full_name)
                if receive_flag == 0:
                    # 将报错写入
                    pass
                else:
                    # 写入测试结果
                    test_actual_values.append(res)
            # 比较test_expected_values_与test_actual_values
            # test_result = self.judge(test_expected_values_, test_actual_values)
            test_judgement = Judgement(expected_values=test_expected_values_, actual_values=test_actual_values)
            test_result = test_judgement.judge()
            # 将test_actual_values写入Test_Actual_Values
            self.xls_df.loc[test_case_num, "Test_Actual_Values"] = str(test_actual_values)

            # 将结果写入Test_Result
            self.xls_df.loc[test_case_num, "Test_Result"] = "Pass" if test_result else "Fail"
            time.sleep(0.05)
        # 写入excel
        self.my_xls.to_excel(self.xls_df, excel_sheet_name)

    @classmethod
    def judge(cls, a_list, b_list):
        """
        判断
        精确度也在这里处理
        :param a_list:
        :param b_list:
        :return:
        """
        res = True
        if len(a_list) != len(b_list):
            res = False
            return res
        # if len(a_list) == len(b_list) and all(x in b_list for x in a_list):
        #     res = True
        for i, v in enumerate(a_list):
            # 处理精确度
            if v != b_list[i]:
                res = False
                break
        return res


if __name__ == '__main__':
    start_time = time.time()

    t = CANoeLauterbachTest()
    t.test()
    end_time = time.time()
    print(f"开始时间:{start_time}")
    print(f"结束时间:{end_time}")
    used_time = (end_time - start_time)/60  # 分钟
    print(f"用时: {used_time} min.")
