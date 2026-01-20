import openpyxl
from openpyxl.styles import Alignment, Font, PatternFill,  Border, Side
from openpyxl.styles.colors import Color
from openpyxl.utils import get_column_letter

black = Color(rgb='000000')
white = Color(rgb='FFFFFF')
red = Color(rgb='FF0000')
green = Color(rgb='00FF00')
blue = Color(rgb='0000FF')
cyan = Color(rgb='00FFFF')
magenta = Color(rgb='FF00FF')
yellow  = Color(rgb='FFFF00')
orange = Color(rgb='FFA500')
purple = Color(rgb='800080')

gray_fill = PatternFill(start_color="D3D3D3", end_color="D3D3D3", fill_type="solid")
yellow_fill = PatternFill(start_color="FFFF00", end_color="FFFF00", fill_type="solid")
green_fill = PatternFill(start_color="00FF00", end_color="00FF00", fill_type="solid")
red_fill = PatternFill(start_color="FF0000", end_color="FF0000", fill_type="solid")

cell_test_fill_Color = {'green':green_fill, 'red':red_fill, 'gray':gray_fill}
cell_test_fill_text = {'green':"PASS", 'red':"FAILED", 'gray':"NOTEST"}

Header_font = Font(name='Arial', size=10, bold=True, italic=False, color=black)
Header_fill = PatternFill(fill_type='solid', start_color='FFFF00', end_color='FFFF00')
Header_border = Border(left=Side(style='thin', color='000000'), right=Side(style='thin', color= black), \
              top=Side(style='thin', color='000000'), bottom=Side(style='thin', color='000000'))
Header_alignment = Alignment(horizontal='center', vertical='center', wrap_text=False)

front = Font(name='Arial', size=10, bold=False, italic=False, color=black)
fill = PatternFill(fill_type='solid', start_color='FFFF00', end_color='FFFF00')
border = Border(left=Side(style='thin', color='000000'), right=Side(style='thin', color= black), \
              top=Side(style='thin', color='000000'), bottom=Side(style='thin', color='000000'))

alignment_Hcenter_Vcenter = Alignment(horizontal='center', vertical='center', wrap_text=False)
alignment_Hleft_Vcenter = Alignment(horizontal='left', vertical='center', wrap_text=False)

def GenerateFile(file_name):
    print("生成测试报告 ...")
    # 生成一个新的 Excel 文件
    workbook = openpyxl.Workbook()


    # 获取当前的工作表
    test_channel_sheet = workbook.create_sheet("Public CAN")
    # 写入表头
    sheet_Head = ['序号','报文类型', '消息名称','物理值','信号值','期望周期ms','接收测试','周期测试', '最大值测试/中间值测试/最小值测试', '中间值测试', '最小值测试']
    test_channel_sheet.append(sheet_Head)

    # 设置第一行的单元格格式
    for cell in test_channel_sheet[1]:
        cell.alignment = Header_alignment
        cell.font = Header_font
        cell.border = Header_border
    
    a_row  = 2 #从第二行开始写入memory数据
    msg_type_start_row = a_row

    a_col = 1

    write_physics_data ="最大值期望值："
    data_str = msg.dbc_msg.encode(msg.signal_data_max).hex()
    data_str = ' '.join(data_str[i:i+2] for i in range(0, len(data_str), 2))
    write_physics_data += data_str + '\n'
    write_physics_data +="最大值实际值："
    if msg.store_max_check_data != "":
        data_str = msg.store_max_check_data.hex()
        data_str = ' '.join(data_str[i:i+2] for i in range(0, len(data_str), 2))
    else:
        data_str = ""
    write_physics_data += data_str + '\n'

    write_physics_data +="中间值期望值："
    data_str = msg.dbc_msg.encode(msg.signal_data_mid).hex()
    data_str = ' '.join(data_str[i:i+2] for i in range(0, len(data_str), 2))
    write_physics_data += data_str + '\n'
    write_physics_data +="中间值实际值："
    if msg.store_mid_check_data != "":
        data_str = msg.store_mid_check_data.hex()
        data_str = ' '.join(data_str[i:i+2] for i in range(0, len(data_str), 2))
    else:
        data_str = ""
    write_physics_data += data_str + '\n'

    write_physics_data +="最小值期望值："
    data_str = msg.dbc_msg.encode(msg.signal_data_min).hex()
    data_str = ' '.join(data_str[i:i+2] for i in range(0, len(data_str), 2))
    write_physics_data += data_str + '\n'
    write_physics_data +="最小值实际值："
    if msg.store_min_check_data != "":
        data_str = msg.store_min_check_data.hex()
        data_str = ' '.join(data_str[i:i+2] for i in range(0, len(data_str), 2))
    else:
        data_str = ""
    write_physics_data += data_str

    write_signal_data = ""
    write_signal_data ="最大值期望值："
    data_str = str(msg.signal_data_max)
    write_signal_data += data_str + '\n'
    write_signal_data +="最大值实际值："
    if msg.store_max_check_data != "":
        data_str = msg.dbc_msg.decode(msg.store_max_check_data)
        data_str = str(data_str)
    else:
        data_str = ""
    write_signal_data += data_str + '\n'

    write_signal_data +="中间值期望值："
    data_str = str(msg.signal_data_mid)
    write_signal_data += data_str + '\n'
    write_signal_data +="中间值实际值："
    if msg.store_mid_check_data != "":
        data_str = msg.dbc_msg.decode(msg.store_mid_check_data)
        data_str = str(data_str)
    else:
        data_str = ""
    write_signal_data += data_str + '\n'

    write_signal_data +="最小值期望值："
    data_str = str(msg.signal_data_min)
    write_signal_data += data_str + '\n'
    write_signal_data +="最小值实际值："
    if msg.store_min_check_data != "":
        data_str = msg.dbc_msg.decode(msg.store_min_check_data)
        data_str = str(data_str)
    else:
        data_str = ""
    write_signal_data += data_str
    
    Val =  [str(a_row-1),                                               # 第1列
            "TX",                                                       # 第2列
            msg.dbc_msg.name + '-0x' + str(hex(msg.dbc_msg.frame_id)),  # 第3列
            write_physics_data,                                         # 第4列
            write_signal_data,                                          # 第5列
            str(msg.dbc_msg.cycle_time),                                # 第6列       
            cell_test_fill_text[msg.tr_test_result],                    # 第7列
            cell_test_fill_text[msg.period_test_result],                # 第8列
            cell_test_fill_text[msg.max_value_test_result],             # 第9列
            cell_test_fill_text[msg.mid_value_test_result],             # 第10列
            cell_test_fill_text[msg.min_value_test_result]              # 第11列
            ]
    #按列写入数据
    test_channel_sheet.append(Val)
    #设置对齐方式
    for i in Val:
        cell = test_channel_sheet.cell(row = a_row, column= a_col)
        cell.alignment = alignment_Hcenter_Vcenter
        cell.font = front
        cell.border = border
        a_col+=1
    test_channel_sheet.cell(row = a_row, column= 4).alignment = alignment_Hleft_Vcenter
    test_channel_sheet.cell(row = a_row, column= 5).alignment = alignment_Hleft_Vcenter
    test_channel_sheet.cell(row = a_row, column= 7).fill = cell_test_fill_Color[msg.tr_test_result]
    test_channel_sheet.cell(row = a_row, column= 8).fill = cell_test_fill_Color[msg.period_test_result]
    test_channel_sheet.cell(row = a_row, column= 9).fill = cell_test_fill_Color[msg.max_value_test_result]
    test_channel_sheet.cell(row = a_row, column= 10).fill = cell_test_fill_Color[msg.mid_value_test_result]
    test_channel_sheet.cell(row = a_row, column= 11).fill = cell_test_fill_Color[msg.min_value_test_result]
    a_row+=1
    Val.clear()
    msg_type_end_row = a_row-1
    test_channel_sheet.merge_cells(f'B{msg_type_start_row}:B{msg_type_end_row}')  
    msg_type_start_row = a_row

    # 自动调整列宽
    for column in test_channel_sheet.columns:
        max_length = 0
        column = [cell for cell in column]
        

        for cell in column:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(cell.value)
            except:
                pass
    
        col_idx = column[0].column  # 获取列索引
        col_letter = get_column_letter(col_idx)  # 将列索引转换为字母

        # 跳过第4和第5列
        if col_letter in ['D', 'E']:  # 'D' 是第4列，'E' 是第5列
            adjusted_width = (max_length/6 + 4)
        else:
            adjusted_width = (max_length + 4)
        test_channel_sheet.column_dimensions[get_column_letter(column[0].column)].width = adjusted_width


    workbook.save(file_name+'.xlsx')
    print("测试报告生成完成，文件名："+file_name)

GenerateFile()