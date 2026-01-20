import requests
import os
import re


# FEISHU_WEBHOOK="https://open.feishu.cn/open-apis/bot/v2/hook/ffd51a8c-79c7-4210-9805-6f082663e0df"
FEISHU_WEBHOOK="https://open.feishu.cn/open-apis/bot/v2/hook/b61761ce-65c0-4d52-b995-bc5601695696"

def send_message(message):
	payload1 = {
		"msg_type": "post",
		"content": {
			"post": {
				"zh_cn": {
					"title": "自动触发软件集成测试",
					"content": [
						[{
							"tag": "text",
							"text": message
						}]
					]
				}
			}
		}
	}

	header = {
        "Content-Type": "application/json"
	}
    
	reponse = requests.post(FEISHU_WEBHOOK, json=payload1, headers=header)
	if reponse.status_code == 200:
		print("飞书消息发送成功")
	else:
		print("飞书消息发送失败")

def get_result(path, pattern):
	message = ""
	log_file = ""
	for root, dirs, files in os.walk(path):
		for name in files:
			if re.search(pattern, name):
				log_file = name

	if 	log_file != '':
		with open(path+log_file, mode='r', encoding='utf-8') as content:
			result_flag = False
			for line in content:
				if "Test Result:" in line:
					result_flag = True
				if result_flag == True:
					line = line.strip()
					if "Total:" in line:
						message = "全量 "+line.split(" ")[1]+" 个"
					if "Pass:" in line:
						message = message+"，通过 "+line.split(" ")[1]+" 个"
					if "Fail:" in line:
						message = message+"，失败 "+line.split(" ")[1]+" 个"
					if "N.A.:" in line:
						message = message+"，NA "+line.split(" ")[1]+" 个"
		if message == "":
			print("Not Find Test Result")
	else:
		print("Not Find LogFile")

	return message

if __name__ == "__main__":
	pattern = r"log_.*.txt"
	interface_path = "D:/CICT/IntegrationTest/output/"
	smoke_path = "D:/CICT/SmokeTest/output/"

	message = "接口测试: "
	message = message + get_result(interface_path,pattern)
	message = message + "\n冒烟测试: "
	message = message + get_result(smoke_path,pattern)
	send_message(message)

