"""
pandas读写
"""
import pandas as pd
import numpy as np
import os
from config import result_excel_file, result_excel_file_sheet_name


class MyXls:
    def __init__(self, dbc_xls_path: str):
        self.dbc_xls_path = dbc_xls_path
        # 读
        # self.raw_data = pd.read_excel(dbc_xls_path)
        # with pd.ExcelFile(dbc_xls_path) as reader:
        #     self.reader = reader
        # self.reader = pd.ExcelFile(dbc_xls_path)
        # 创建ExcelWrite对象
        # with pd.ExcelWriter(dbc_xls_path) as writer:
        #     self.writer = writer
        # self.writer = pd.ExcelWriter(dbc_xls_path)


    def read_excel(self, sheet_name: str = "Sheet1"):
        # https: // zhuanlan.zhihu.com / p / 564004991
        # 读excel
        index_col_name = "用例编号"
        try:
            df = pd.read_excel(self.dbc_xls_path, sheet_name=sheet_name, header=0, index_col=1)
        except Exception as e:
            raise e
        else:

            return df

    def to_excel(self, df: pd.DataFrame, sheet_name: str = 'Sheet2', xls_path: str = ""):
        # http://c.biancheng.net/pandas/excel.html
        # https: // mp.weixin.qq.com / s / -qBbcLWu3jHptlSPjyB3Ng
        """写入excel"""
        xls_path = result_excel_file
        if not os.path.exists(xls_path):
            open(xls_path, mode='w')
        # 关闭打开的
        writer = pd.ExcelWriter(xls_path, mode="w", engine="openpyxl")
        try:
            df.to_excel(excel_writer=writer, sheet_name=result_excel_file_sheet_name)
        except Exception as e:
            print(e)
        else:
            print("写入成功")
        finally:
            writer._save()
            writer.close()


if __name__ == '__main__':
    excel_file = r"C:\001_work\QH01\lauterbach_test\FLCR.xlsx"
    p_xls = MyXls(excel_file)
    xls_df = p_xls.read_excel()
    print(1111)
    for row in xls_df.itertuples():
        test_values = getattr(row, "Test_Values")
        print(getattr(row, "Index"), row)
