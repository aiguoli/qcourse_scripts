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
COURSE_DIR = os.path.join(BASE_DIR, 'courses')
if not os.path.exists(COURSE_DIR):
    os.mkdir(COURSE_DIR)


class QCourse:
    def __init__(self):
        # 初始化options
        self.prefs = {"download.default_directory": os.getcwd()}
        self.options = EdgeOptions()
        self.options.use_chromium = True
        self.options.add_argument("log-level=3")
        self.options.add_experimental_option('excludeSwitches', ['enable-logging'])
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

    def get_video(self, video_url=None, path=None):
        if not video_url:
            print('请输入视频url！')
        # 跳转一次没法跳转，可能是设置了preventDefault
        self.driver.get(video_url)
        self.driver.get(video_url)
        # 等待视频开始播放
        WebDriverWait(self.driver, 300).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'loki-time'))
        )
        WebDriverWait(self.driver, 300).until_not(
            lambda driver: driver.find_element_by_class_name('loki-time').get_attribute("innerHTML") == '00:00 / 00:00'
        )

        networks = self.driver.execute_script('return window.performance.getEntries()')
        ts_url = key_url = ''
        for network in networks:
            if '.ts?start' in network.get('name'):
                ts_url = network.get('name')
            elif 'get_dk' in network.get('name'):
                key_url = network.get('name')
        title = self.driver.title
        download_single(ts_url, key_url, title, path)

    def load_cookies(self):
        if not os.path.exists('cookies.json'):
            self.login()
        with open('cookies.json', 'r') as f:
            listCookies = json.loads(f.read())
        self.driver.get(self.login_url)
        for cookie in listCookies:
            self.driver.add_cookie({
                'domain': '.ke.qq.com',
                'httpOnly': cookie['httpOnly'],
                'name': cookie['name'],
                'path': '/',
                'secure': cookie['secure'],
                'value': cookie['value']
            })


def main():
    menu = ['下载单个视频', '下载课程指定章节', '下载课程全部视频']
    utils.print_menu(menu)
    chosen = input('\n输入需要的功能：')
    chosen = int(chosen)
    if chosen == 0:
        url = input('输入视频链接：')
        qq_course = QCourse()
        qq_course.load_cookies()
        qq_course.get_video(video_url=url)
        qq_course.close()
    elif chosen == 1:
        cid = input('请输入课程cid:')
        course_name = utils.get_course_from_api(cid)
        print('获取课程信息成功')
        url_dict = utils.get_all_urls(course_name+'.json')
        chapter_names = list(url_dict.keys())
        utils.print_menu(chapter_names)
        chapter_index = input('请输入要下载的章节：')
        chapter_name = chapter_names[int(chapter_index)]
        courses = url_dict.get(chapter_name)
        chapter_name = chapter_name.replace('/', '／') .replace('\\', '＼')
        print('即将开始下载章节：' + chapter_name)
        print('='*20)
        qq_course = QCourse()
        qq_course.load_cookies()
        chapter_path = os.path.join(COURSE_DIR, course_name, chapter_name)
        if not os.path.exists(chapter_path):
            os.makedirs(chapter_path)
        for course in courses:
            course_url = courses.get(course)
            qq_course.get_video(video_url=course_url, path=chapter_path)
        qq_course.close()
    elif chosen == 2:
        cid = input('请输入课程cid:')
        course_name = utils.get_course_from_api(cid)
        print('获取课程信息成功,准备下载！')
        qq_course = QCourse()
        qq_course.load_cookies()
        url_dict = utils.get_all_urls(course_name+'.json')
        for chapter in url_dict:
            chapter_path = os.path.join(COURSE_DIR, course_name, chapter)
            if not os.path.exists(chapter_path):
                os.makedirs(chapter_path)
            print('正在下载章节：' + chapter)
            courses = url_dict.get(chapter)
            for course in courses:
                course_url = courses.get(course)
                print('正在下载课程：' + course + ', ', end='')
                qq_course.get_video(video_url=course_url, path=chapter_path)
        qq_course.close()


if __name__ == '__main__':
    main()
