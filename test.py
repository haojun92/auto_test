import subprocess
import sys
from flask import Flask, request, jsonify
import os
import time
from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.chrome.service import Service
from csdn.selenium.csdn.QQemail.EmailGo import QQMailer
from csdn.selenium.csdn.handle.article import CsdnArticle
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import logging

#

logger = logging.getLogger()
logger.setLevel(logging.INFO)
# 创建文件处理器
file_handler = logging.FileHandler('app.log')
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

# 创建流处理器
stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.INFO)
stream_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

# 将处理器添加到日志记录器
logger.addHandler(file_handler)
logger.addHandler(stream_handler)

app = Flask(__name__)

# 执行前 执行该命令 set PYTHONPATH=%PYTHONPATH%;C:\Users\Nekosann\Desktop\giteecode\myscript\


def is_download_completed(download_dir):
    # 循环检查下载文件夹中是否还有临时文件
    filelist = os.listdir(download_dir)
    # logger.info(f"当前文件夹中的文件列表为：{filelist}")
    while any([filename.endswith(".crdownload") for filename in os.listdir(download_dir)]):
        logger.info(f"存在crdownload文件: 下载中...")
        time.sleep(1)  # 等待1秒再次检查
    return True

@app.route('/csdn/article/download', methods=['POST'])
def article_download():
    logger.info("当前请求参数是："+str(request.get_json()))
    try:
        if request.content_type == 'application/json':
            # 处理JSON格式的数据
            data = request.get_json()
            article_url = data.get('article_url')
            download_url = data.get('download_url')
            receiver_email = data.get('receiver_email')
            format = data.get('format')
            # 创建一个Chrome选项对象
            chrome_options = Options()
            # 例如 Windows 上可能是 'C:\Users\Nekosann\AppData\Local\Google\Chrome\User Data'
            # 或者 macOS 上可能是 '/Users/YourUserName/Library/Application Support/Google/Chrome'
            # mac_profile_path = '/Users/hj/Library/Application Support/Google/Chrome'
            windows_profile_path = None
            service = None
            if os.name == 'nt':
                service = Service("C:\\Users\\Nekosann\\Desktop\\chromedriver-win64\\chromedriver-win64\\chromedriver.exe")
                windows_profile_path = 'C:\\Users\\Nekosann\\AppData\\Local\\Google\\Chrome\\User Data'
            chrome_options.add_argument(f'user-data-dir={windows_profile_path}')
            chrome_options.add_argument('log-level=3')
            driver = webdriver.Chrome(options=chrome_options,service=service)
            directory_path = r'C:\Users\Nekosann\Downloads'
            try:
                if article_url:
                    csdnArticle = CsdnArticle(driver)
                    csdnArticle.get_article(article_url)
                    ActionChains(driver).send_keys('aa').perform()
                    time.sleep(3)
                    ActionChains(driver).send_keys('sr').perform()
                    time.sleep(2)
                    if format == 'screenshot':
                        # 获取目录中的所有文件和文件夹
                        files_and_folders = os.listdir(directory_path)
                        # 当前文件中的个数
                        file_num = len(files_and_folders)
                        ActionChains(driver).send_keys('pg').perform()
                        while True:
                            # 获取目录中的所有文件和文件夹
                            files_and_folders = os.listdir(directory_path)
                            # 当前文件中的个数
                            current_file_num = len(files_and_folders)
                            if current_file_num > file_num:
                                break
                            else:
                                logger.info(f"当前图片正在下载中...")
                                time.sleep(1)
                    else:
                        ActionChains(driver).send_keys('oh').perform()
                        time.sleep(4)
                else:
                    # 打开csdn的下载链接
                    driver.get(download_url)
                    # 获取页面源码 检查是否具备下载权限
                    page_source = driver.page_source
                    if "VIP专享下载" in page_source or "立即下载" in page_source:
                        # 判断下载内容是否超过50MB
                        file_size_span = driver.find_element(By.XPATH,
                                                             '/html/body/div[3]/div/div[1]/div/div[2]/div[1]/div[1]/div[2]/div[1]/div[1]/div/div[2]/div[2]/div/span[7]')
                        # 获取其中文本
                        file_size = file_size_span.text
                        # 判断其中是否含有 KB 或者MB 等单位
                        if 'MB' in file_size:
                            # 获取其中的数字
                            file_size = float(file_size.replace('MB', '').strip())
                            if file_size > 50:
                                return "暂不支持下载文件超过50MB", 505
                        elif 'KB' in file_size:
                            pass
                        else:
                            # 判断下载内容是否超过50MB
                            file_size_span = driver.find_element(By.XPATH,
                                                                 '/html/body/div[3]/div/div[1]/div/div[2]/div[1]/div[1]/div[2]/div[1]/div[1]/div/div[2]/div[2]/div/span[6]')
                            # 获取其中文本
                            file_size = file_size_span.text
                            if 'MB' in file_size:
                                # 获取其中的数字
                                file_size = float(file_size.replace('MB', '').strip())
                                if file_size > 50:
                                    return "暂不支持下载文件超过50MB", 505
                        # 点击立即下载按钮
                        try:
                            download_button = driver.find_element(By.XPATH,
                                                                  '/html/body/div[3]/div/div[1]/div/div[3]/div[1]/div[1]/div[2]/div[1]/div[3]/div[1]/button/span/span')
                            download_button.click()
                        except Exception as e:
                            logger.info("点击下载按钮出错，正在重试")
                            download_button = driver.find_element(By.XPATH,
                                                                  "/html/body/div[3]/div/div[1]/div/div[2]/div[1]/div[1]/div[2]/div[1]/div[3]/div[1]/button/span/span")
                            download_button.click()
                        logger.info("点击下载按钮")
                        time.sleep(3)
                        # 在弹窗页面中找到VIP专享下载按钮
                        try:
                            vip_download_button = driver.find_element(By.XPATH,
                                                                      '/html/body/div[3]/div/div[1]/div/div[4]/div/div[3]/div/div/button')
                            vip_download_button.click()
                        except Exception as e:
                            logger.info("点击VIP专享下载按钮出错，正在重试")
                            vip_download_button = driver.find_element(By.XPATH,
                                                                      "/html/body/div[3]/div/div[1]/div/div[3]/div/div[3]/div/div/button")
                            vip_download_button.click()
                        logger.info("点击VIP专享下载按钮,开始下载文件...")
                        time.sleep(3)
                if os.name == 'nt':
                    logger.info("当前操作系统是Windows")
                    # 设置目录路径
                    if is_download_completed(directory_path):
                        # 获取目录中的所有文件和文件夹
                        files_and_folders = os.listdir(directory_path)
                        # 过滤出文件列表
                        files = [f for f in files_and_folders if os.path.isfile(os.path.join(directory_path, f))]
                        # 初始化最新文件的时间戳和路径
                        latest_timestamp = 0
                        latest_file_path = None
                        # 遍历文件列表，找到最新生成的文件
                        for file in files:
                            file_path = os.path.join(directory_path, file)
                            file_timestamp = os.path.getmtime(file_path)  # 获取文件最后修改时间的时间戳
                            if file_timestamp > latest_timestamp:
                                latest_timestamp = file_timestamp
                                latest_file_path = file_path
                        # 打印最新生成的文件路径
                        logger.info(f"最新生成的文件路径: {latest_file_path}")
                        #发送邮件
                        sender = ""  # 你的QQ邮箱地址
                        auth_code = ""  # 你的QQ邮箱授权码
                        mailer = QQMailer(sender, auth_code)
                        mailer.send_mail(
                            receiver_email=receiver_email,
                            subject="csdn资源",
                            body="csdn文章资源自助服务内容，请在附件中查看您的文章内容",
                            attachment_path=latest_file_path
                        )
                driver.quit()
            except RuntimeError as runtimeError:
                logger.error(f"下载文章失败,错误内容为：{runtimeError}")
                driver.quit()
                return "专栏文章需要单独付费不在服务范围", 501
            except Exception as e:
                logger.error(f"下载文章失败,错误内容为：{e}")
                driver.quit()
                return "下载异常，请联系店家解决", 502
            return '下载完毕，已发送至邮箱，请查收！', 200
        else:
            return '提交数据格式不正确',403
    except Exception as e:
        logger.error(f"下载文章失败,错误内容为：{e}")
        return "下载异常，请联系店家解决", 503

if __name__ == '__main__':

    # 定义需要安装的模块列表
    required_packages = ['flask', 'requests','selenium']
    # 检查每个模块是否已安装，未安装的将使用pip安装
    for package in required_packages:
        try:
            # 尝试导入模块
            __import__(package)
        except ImportError:
            # 如果模块未安装，使用pip安装
            print(f"安装模块：{package}")
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
    app.run(host='0.0.0.0',debug=True,port=5000)