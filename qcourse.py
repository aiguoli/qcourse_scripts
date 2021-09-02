import asyncio
import json
from pathlib import Path
from uuid import uuid1

from playwright.sync_api import sync_playwright

from utils import print_menu, get_course_from_api, get_download_url_from_course_url, choose_term, get_all_urls, \
    get_download_urls, choose_chapter, get_courses_from_chapter
from downloader import download_single


BASE_DIR = Path()
COURSE_DIR = BASE_DIR.joinpath('courses')
if not COURSE_DIR.exists():
    COURSE_DIR.mkdir()


class QCourse:
    def __init__(self):
        self.p = sync_playwright().start()
        self.browser = self.p.chromium.launch(channel='msedge', headless=False)
        self.context = self.browser.new_context()

    def login(self):
        if not self.is_login():
            page = self.context.new_page()
            page.goto('https://ke.qq.com/')
            page.click('#js_login')
            # wait for login
            print('未检测到cookies，请先登录...')
            page.wait_for_selector('.login-mask', state='attached')
            page.wait_for_selector('.login-mask', state='detached')
            self.save_cookies(page.context.cookies())
            page.close()
            print('登录成功')

    def close(self):
        self.browser.close()
        self.p.stop()

    @staticmethod
    def is_login():
        return Path('cookies.json').exists()

    @staticmethod
    def save_cookies(cookies):
        with open('cookies.json', 'w') as f:
            f.write(json.dumps(cookies))

    @staticmethod
    def load_cookie():
        cookies = Path('cookies.json')
        if cookies.exists():
            return json.loads(cookies.read_bytes())

    @staticmethod
    def clear_cookies():
        cookies = Path('cookies.json')
        if cookies.exists():
            cookies.unlink()


async def parse_course_url_and_download(video_url, filename=None, path=None):
    if not path:
        path = Path('courses')
    if not filename:
        filename = str(uuid1())
    urls = get_download_url_from_course_url(video_url, -1)
    if urls:
        await download_single(ts_url=urls[0], key_url=urls[1], filename=filename, path=path)


async def download_selected_chapter(term_id, filename, chapter_name, courses):
    tasks = []
    for course in courses:
        path = Path('courses', filename, chapter_name)
        course_name = course.get('name')
        file_id = course.get('resid_list')
        urls = get_download_urls(term_id, file_id)
        tasks.append(asyncio.create_task(download_single(ts_url=urls[0], key_url=urls[1], filename=course_name, path=path)))
    await asyncio.wait(tasks)


def main():
    menu = ['下载单个视频', '下载课程指定章节', '下载课程全部视频']
    print_menu(menu)
    chosen = int(input('\n输入需要的功能：'))
    # ================大佬看这里================
    # 只有这一个地方用到了playwright，用来模拟登录
    # 实在不想再抓包了，等一个大佬去掉playwright依赖，改成输入账户密码
    qq_course = QCourse()
    qq_course.login()
    qq_course.close()
    # =========================================
    if chosen == 0:
        course_url = input('输入课程链接：')
        parse_course_url_and_download(course_url)
    elif chosen == 1:
        cid = input('请输入课程cid:')
        course_name = get_course_from_api(cid)
        filename = course_name
        print('获取课程信息成功')

        term_index, term_id, term = choose_term(filename+'.json')
        chapter = choose_chapter(term)
        chapter_name = chapter.get('name').replace('/', '／').replace('\\', '＼')
        courses = get_courses_from_chapter(chapter)
        print('即将开始下载章节：' + chapter_name)
        print('='*20)

        chapter_path = COURSE_DIR.joinpath(course_name, chapter_name)
        if not chapter_path.exists():
            chapter_path.mkdir(parents=True)
        asyncio.run(download_selected_chapter(term_id, filename, chapter_name, courses))
    elif chosen == 2:
        cid = input('请输入课程cid:')
        course_name = get_course_from_api(cid)
        term_index = choose_term(course_name+'.json')
        print('获取课程信息成功,准备下载！')
        url_dict = get_all_urls(course_name+'.json', term_index)
        for chapter in url_dict:
            chapter_path = COURSE_DIR.joinpath(course_name, chapter)
            if not chapter_path.exists():
                chapter_path.mkdir(parents=True)
            print('正在下载章节：' + chapter)
            courses = url_dict.get(chapter)
            for course in courses:
                course_url = courses.get(course)
                print('正在下载课程：' + course + ', ', end='')
                parse_course_url_and_download(course_url, filename=course, path=Path('courses', course_name, chapter))
    else:
        print('请按要求输入！')


if __name__ == '__main__':
    main()
