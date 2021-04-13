import json
import os
import time

import utils
from downloader import download_single

from msedge.selenium_tools import Edge, EdgeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

BASE_DIR = os.getcwd()


class QCourse:
    def __init__(self):
        # 初始化options
        self.prefs = {"download.default_directory": os.getcwd()}
        self.options = EdgeOptions()
        self.options.use_chromium = True
        self.options.add_experimental_option('prefs', self.prefs)
        self.options.add_argument("--mute-audio")

        self.login_url = 'https://ke.qq.com/'

        self.driver = Edge(executable_path='msedgedriver.exe', options=self.options)

    def login(self):
        self.driver.get('https://ke.qq.com/')
        self.driver.find_element_by_id('js_login').click()
        time.sleep(1)

        WebDriverWait(self.driver, 300).until_not(
            EC.presence_of_element_located((By.CLASS_NAME, 'ptlogin-mask'))
        )

        dictCookies = self.driver.get_cookies()
        jsonCookies = json.dumps(dictCookies)
        with open('cookies.json', 'w') as f:
            f.write(jsonCookies)
        print('登陆成功！')

    def close(self):
        self.driver.close()

    def get_video(self, video_url=None):
        if not video_url:
            print('请输入视频url！')
        os.chdir(BASE_DIR)
        if not os.path.exists('cookies.json'):
            self.login()
        with open('cookies.json', 'r') as f:
            listCookies = json.loads(f.read())
        self.driver.get(video_url)
        for cookie in listCookies:
            self.driver.add_cookie({
                'domain': '.ke.qq.com',
                'httpOnly': cookie['httpOnly'],
                'name': cookie['name'],
                'path': '/',
                'secure': cookie['secure'],
                'value': cookie['value']
            })
        self.driver.get(video_url)
        # 等待视频开始加载，如果你的浏览器很牛逼，这里可以缩短一些
        time.sleep(10)
        networks = self.driver.execute_script('return window.performance.getEntries()')
        ts_url = key_url = ''
        for network in networks:
            if '.ts?start' in network.get('name'):
                ts_url = network.get('name')
            elif 'get_dk' in network.get('name'):
                key_url = network.get('name')
        title = self.driver.title
        catalog = self.driver.execute_script('return document.getElementsByClassName("task-item task-info active")'
                                             '[0].parentNode.firstElementChild.innerText')
        if not os.path.exists(catalog):
            os.mkdir(catalog)
        os.chdir(os.path.join(os.getcwd(), catalog))
        download_single(ts_url, key_url, title)
        self.close()


def main():
    menu = ['下载单个视频', '下载课程指定章节', '下载课程全部视频']
    utils.print_menu(menu)
    chosen = input('\n输入需要的功能：')
    chosen = int(chosen)
    if chosen == 0:
        url = input('输入视频链接：')
        qq_course = QCourse()
        qq_course.get_video(video_url=url)
    elif chosen == 1:
        qq_course = QCourse()
        cid = input('请输入课程cid:')
        course_name = utils.get_course_from_api(cid)
        print('获取课程信息成功')
        url_dict = utils.get_all_urls(course_name)
        chapter_names = list(url_dict.keys())
        utils.print_menu(chapter_names)
        chapter_index = input('请输入要下载的章节：')
        chapter_name = chapter_names[int(chapter_index)]
        courses = url_dict.get(chapter_name)
        print('即将开始下载章节：' + chapter_name)
        for course in courses:
            course_url = courses.get(course)
            print('正在下载课程：' + course)
            print(course_url)
            qq_course.get_video(video_url=course_url)
    elif chosen == 2:
        qq_course = QCourse()
        cid = input('请输入课程cid:')
        course_name = utils.get_course_from_api(cid)
        print('获取课程信息成功')
        url_dict = utils.get_all_urls(course_name)
        for chapter in url_dict:
            print('正在下载章节：' + chapter)
            courses = url_dict.get(chapter)
            for course in courses:
                course_url = courses.get(course)
                print('正在下载课程：' + course)
                qq_course.get_video(video_url=course_url)


if __name__ == '__main__':
    main()
