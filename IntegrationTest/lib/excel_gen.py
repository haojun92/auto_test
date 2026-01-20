import xlsxwriter


class content():
    def __init__(self):
        self.name = ''
        self.info = ''
        self.desc = ''
        self.exp = ''
        self.act = ''
        self.stat = ''
        self.comm = ''


def excel_gen(results, name):
    
    workbook = xlsxwriter.Workbook(name)  #创建一个Excel文件
    worksheet = workbook.add_worksheet('Result')    #创建一个sheet
    worksheet.set_column("A:A", 35)
    worksheet.set_column("B:B", 70)
    worksheet.set_column("C:C", 55)
    worksheet.set_column("D:E", 35)
    worksheet.set_column("F:F", 15)
    worksheet.set_column("G:G", 20)

    title_format = workbook.add_format({'bold':True, 'align':'left', 'valign':'top'})   
    content_format = workbook.add_format({'text_wrap':True})  
    worksheet_title = [U'Test Name',U'Interface Info',U'Description',U'Expected Result',U'Actual Result',U'Test Status',U'Comments'] 
    worksheet.write_row(0,0,worksheet_title,title_format)

    row_num = 0
    for result in results:
        row_num += 1
        row_content = []

        exec_content = content()
        #Test Name
        if result.provide == '':
            exec_content.name = result.interface+"_"+result.receive
        elif result.receive == '':
            exec_content.name = result.interface+"_"+result.provide
        else:
            exec_content.name = result.interface+"_"+result.provide+"_"+result.receive

        #Interface Info
        exec_content.info = "Interface:{}\n".format(result.interface)
        exec_content.info = exec_content.info+"Sender:{}\n".format(result.provide)
        exec_content.info = exec_content.info+"Receiver:{}\n".format(result.receive)
        exec_content.info = exec_content.info+"WriteIf:{}\n".format(result.write)
        exec_content.info = exec_content.info+"ReadIf:{}\n".format(result.read)
        exec_content.info = exec_content.info+"Variant:{}\n".format(result.variant)
        exec_content.info = exec_content.info+"Elements:{}".format(result.element)

        if result.map_status == False:
            exec_content.desc = ''
            exec_content.exp = ''
            exec_content.act = ''

        elif result.provide_stop == True and result.receive_stop == True:
            #Description
            exec_content.desc = "Purpose:Check interface {} form {} to {}\n\n".format(result.interface, result.provide, result.receive)
            exec_content.desc = exec_content.desc+"Test Steps:\n"
            exec_content.desc = exec_content.desc+"1)Run and stop the software at WriteIf\n"
            exec_content.desc = exec_content.desc+"2)Set all elements of the parameter to 0\n"
            exec_content.desc = exec_content.desc+"3)Run and stop the software at ReadIf\n"
            exec_content.desc = exec_content.desc+"4)Check the values of all elements of the parameter\n"
            exec_content.desc = exec_content.desc+"5)Run and stop the software at WriteIf\n"
            exec_content.desc = exec_content.desc+"6)Set all elements of the parameter to 1\n"
            exec_content.desc = exec_content.desc+"7)Run and stop the software at ReadIf\n"
            exec_content.desc = exec_content.desc+"8)Check the values of all elements of the parameter"
            #Expected Result
            exec_content.exp = "4)The value of all elements is 0\n"
            exec_content.exp = exec_content.exp+"8)The value of all elements is 1"
            #Actual Result
            exec_content.act = "4)The values of the elements are as follows:\n{}\n".format(result.getvalue[0])
            exec_content.act = exec_content.act+"8)The values of the elements are as follows:\n{}".format(result.getvalue[1])

        elif result.provide_stop == True and result.variant_find == True:
            #Description
            exec_content.desc = "Purpose:Check interface {} of {}\n\n".format(result.interface, result.provide)
            exec_content.desc = exec_content.desc+"Test Steps:\n"
            exec_content.desc = exec_content.desc+"1)Run and stop the software at WriteIf\n"
            exec_content.desc = exec_content.desc+"2)Set all elements of the parameter to 0\n"
            exec_content.desc = exec_content.desc+"3)Run and stop the software at WriteIf\n"
            exec_content.desc = exec_content.desc+"4)Check the values of all elements of the variant\n"
            exec_content.desc = exec_content.desc+"5)Set all elements of the parameter to 1\n"
            exec_content.desc = exec_content.desc+"6)Run and stop the software at WriteIf\n"
            exec_content.desc = exec_content.desc+"7)Check the values of all elements of the variant"
            #Expected Result
            exec_content.exp = "4)The value of all elements is 0\n"
            exec_content.exp = exec_content.exp+"7)The value of all elements is 1"
            #Actual Result
            exec_content.act = "4)The values of the elements are as follows:\n{}\n".format(result.getvalue[0])
            exec_content.act = exec_content.act+"7)The values of the elements are as follows:\n{}".format(result.getvalue[1])

        elif result.receive_stop == True and result.variant_find == True:
            #Description
            exec_content.desc = "Purpose:Check interface {} of {}\n\n".format(result.interface, result.receive)
            exec_content.desc = exec_content.desc+"Test Steps:\n"
            exec_content.desc = exec_content.desc+"1)Run and stop the software at ReadIf\n"
            exec_content.desc = exec_content.desc+"2)Set all elements of the parameter to 0\n"
            exec_content.desc = exec_content.desc+"3)Run and stop the software at ReadIf\n"
            exec_content.desc = exec_content.desc+"4)Check the values of all elements of the variant\n"
            exec_content.desc = exec_content.desc+"5)Set all elements of the parameter to 1\n"
            exec_content.desc = exec_content.desc+"6)Run and stop the software at ReadIf\n"
            exec_content.desc = exec_content.desc+"7)Check the values of all elements of the variant"
            #Expected Result
            exec_content.exp = "4)The value of all elements is 0\n"
            exec_content.exp = exec_content.exp+"7)The value of all elements is 1"
            #Actual Result
            exec_content.act = "4)The values of the elements are as follows:\n{}\n".format(result.getvalue[0])
            exec_content.act = exec_content.act+"7)The values of the elements are as follows:\n{}".format(result.getvalue[1])

        else:
            exec_content.desc = ''
            exec_content.exp = ''
            exec_content.act = ''

        exec_content.stat = result.test_status
        exec_content.comm = result.comments

        worksheet.write(row_num, 0, exec_content.name, content_format)
        worksheet.write(row_num, 1, exec_content.info, content_format)
        worksheet.write(row_num, 2, exec_content.desc, content_format)
        worksheet.write(row_num, 3, exec_content.exp, content_format)
        worksheet.write(row_num, 4, exec_content.act, content_format)
        worksheet.write(row_num, 5, exec_content.stat, content_format)
        worksheet.write(row_num, 6, exec_content.comm, content_format)

        worksheet.set_row(row_num, 98)

    workbook.close()
