import requests
import json


def get_course_from_api(cid=None):
    # 获取课程信息
    if cid is None:
        print('请输入cid！')
    url = 'https://ke.qq.com/cgi-bin/course/basic_info?cid=' + str(cid)
    response = requests.get(url).json()
    name = response.get('result').get('course_detail').get('name') + '.json'
    with open(name, 'w') as f:
        f.write(json.dumps(response))
    return name


def get_chapters(filename):
    # 从json文件内获取章节信息
    with open(filename, 'r') as f:
        course_info = json.loads(f.read())
    chapters = course_info.get('result').get('course_detail').get('terms')[0].get('chapter_info')[0].get('sub_info')
    return chapters


def get_courses_from_chapter(chapter):
    return chapter.get('task_info')


def get_course_url(course):
    # 传入课程字典，拼接成课程链接
    cid = course.get('cid')
    term_id = course.get('term_id')
    course_id = course.get('taid')
    url = 'https://ke.qq.com/webcourse/{}/{}#taid={}'.format(cid, term_id, course_id)
    return url


def get_all_urls(filename):
    chapters = get_chapters(filename)
    result = {}
    for chapter in chapters:
        chapter_name = chapter.get('name')
        courses = get_courses_from_chapter(chapter)
        chapter_info = {}
        for course in courses:
            chapter_info.update({course.get('name'): get_course_url(course)})
        result.update({chapter_name: chapter_info})
    return result


def print_menu(menu):
    for item in menu:
        print(str(menu.index(item))+'. '+item)
