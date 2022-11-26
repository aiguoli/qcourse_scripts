import asyncio
import json
import re
from pathlib import Path
from uuid import uuid1

import browser_cookie3
from requests.utils import dict_from_cookiejar, cookiejar_from_dict

import utils
from logger import logger
from utils import (
    print_menu,
    get_course_from_api,
    get_download_url_from_course_url,
    choose_term,
    get_download_urls,
    choose_chapter,
    get_courses_from_chapter,
    get_chapters_from_file,
)
from downloader import download_single
from downloader_m3u8 import download_m3u8_raw as m3u8_down

BASE_DIR = Path()
COURSE_DIR = BASE_DIR.joinpath('courses')
if not COURSE_DIR.exists():
    COURSE_DIR.mkdir()


class QCourse:

    def login(self):
        if not self.is_login():
            # Todo: 默认用edge，下版本考虑添加浏览器选择
            cj = self.get_cookies()
            self.save_cookies(dict_from_cookiejar(cj))
            print('登陆成功！')
            logger.info(dict_from_cookiejar(cj))

    def get_cookies(self):
        if not self.is_login():
            browsers = {
                'Chrome': browser_cookie3.chrome,
                'FireFox': browser_cookie3.firefox,
                'Opera': browser_cookie3.opera,
                'Edge': browser_cookie3.edge,
                'Chromium': browser_cookie3.Chromium,
                'Brave': browser_cookie3.brave,
                'Vivaldi': browser_cookie3.vivaldi,
                'Safari': browser_cookie3.safari,
            }
            print('登录腾讯课堂(https://ke.qq.com)，然后选择你安装的浏览器')
            browser_menu = list(browsers.keys())
            print_menu(browser_menu)
            chosen = int(input('请选择你的浏览器序号：'))
            return browsers[browser_menu[chosen]](domain_name='ke.qq.com')

    @staticmethod
    def is_login():
        return Path('cookies.json').exists()

    @staticmethod
    def save_cookies(cookies):
        with open('cookies.json', 'w') as f:
            json.dump(cookies, f, indent=4)

    @staticmethod
    def load_cookie():
        cookies = Path('cookies.json')
        if cookies.exists():
            return cookiejar_from_dict(json.loads(cookies.read_bytes()))

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
    if urls[1]:
        await download_single(urls[0], urls[1], filename, path)
    else:
        m3u8_down(urls[0], path, filename, True)


async def download_selected_chapter(term_id, filename, chapter_name, courses, cid):
    tasks = []
    for course in courses:
        path = Path('courses', filename, chapter_name)
        course_name = course.get('name')
        file_id = course.get('resid_list')
        file_id = re.search(r'(\d+)', file_id).group(1)
        urls = get_download_urls(term_id, file_id, cid=cid)
        tasks.append(
            asyncio.create_task(
                download_single(
                    ts_url=urls[0], key_url=urls[1], filename=course_name, path=path
                )
            )
        )
    sem = asyncio.Semaphore(3)
    async with sem:
        await asyncio.wait(tasks)


def main():
    menu = ['下载单个视频', '下载课程指定章节', '下载课程全部视频', '退出登录']
    print_menu(menu)
    chosen = int(input('\n输入需要的功能：'))
    qq_course = QCourse()
    qq_course.login()
    # =========================================
    if chosen == 0:
        course_url = input('输入课程链接：')
        logger.info('URL: '+course_url)
        asyncio.run(parse_course_url_and_download(course_url))
    elif chosen == 1:
        cid = utils.choose_course()
        course_name = get_course_from_api(cid)
        print('获取课程信息成功')
        info_file = Path(course_name + '.json')
        term_index, term_id, term = choose_term(info_file)
        chapter = choose_chapter(term)
        chapter_name = chapter.get('name').replace('/', '／').replace('\\', '＼')
        courses = get_courses_from_chapter(chapter)
        logger.info('cid: {}，name: {}, term: {}, chapter: {}'.format(cid, course_name, term_id, chapter_name))
        print('即将开始下载章节：' + chapter_name)
        print('=' * 20)

        chapter_path = COURSE_DIR.joinpath(course_name, chapter_name)
        if not chapter_path.exists():
            chapter_path.mkdir(parents=True)
        asyncio.run(
            download_selected_chapter(term_id, course_name, chapter_name, courses, cid)
        )
    elif chosen == 2:
        cid = utils.choose_course()
        course_name = get_course_from_api(cid)
        term_index, term_id, term = choose_term(course_name + '.json')
        print('获取课程信息成功,准备下载！')
        logger.info('cid: '+cid)
        chapters = get_chapters_from_file(course_name + '.json', term_index)
        for chapter in chapters:
            chapter_name = chapter.get('name').replace('/', '／').replace('\\', '＼')
            courses = get_courses_from_chapter(chapter)
            print('即将开始下载章节：' + chapter_name)
            print('=' * 20)

            chapter_path = COURSE_DIR.joinpath(course_name, chapter_name)
            if not chapter_path.exists():
                chapter_path.mkdir(parents=True)
            asyncio.run(
                download_selected_chapter(
                    term_id, course_name, chapter_name, courses, cid
                )
            )
    elif chosen == 3:
        QCourse.clear_cookies()
    else:
        print('请按要求输入！')


if __name__ == '__main__':
    main()
