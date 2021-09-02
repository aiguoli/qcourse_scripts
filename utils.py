import base64
import re
from pathlib import Path

import requests
import json
import subprocess
from urllib.parse import urlencode, urlparse, parse_qs


def get_course_from_api(cid=None):
    # 获取课程信息
    if cid is None:
        print('请输入cid！')
    url = 'https://ke.qq.com/cgi-bin/course/basic_info?cid=' + str(cid)
    response = requests.get(url).json()
    name = response.get('result').get('course_detail').get('name').replace('/', '／').replace('\\', '＼')
    with open(name+'.json', 'w') as f:
        f.write(json.dumps(response))
    return name


def get_terms_from_api(cid, term_id_list):
    # term_id_list是一个数组，里面是整数格式的term_id
    url = 'https://ke.qq.com/cgi-bin/course/get_terms_detail'
    referer = 'https://ke.qq.com/webcourse/{cid}/{term_id}'.format(cid=cid, term_id=term_id_list[0])
    params = {
        'cid': cid,
        'term_id_list': term_id_list
    }
    headers = {
        'referer': referer
    }
    response = requests.get(url, params=urlencode(params), headers=headers).json()
    return response


def get_terms(filename):
    # 从json文件内获取学期信息
    with open(filename, 'r') as f:
        course_info = json.loads(f.read()).get('result')
    if course_info.get('course_detail'):
        terms = course_info.get('course_detail').get('terms')
    else:
        terms = course_info.get('terms')
    return terms


def get_chapters_from_file(filename, term_index):
    # 从json文件内获取章节信息
    with open(filename, 'r') as f:
        course_info = json.loads(f.read())
    chapters = course_info.get('result').get('course_detail').get('terms')[term_index].get('chapter_info')[0]\
        .get('sub_info')
    return chapters


def get_chapters(term):
    return term.get('chapter_info')[0].get('sub_info')


def get_courses_from_chapter(chapter):
    return chapter.get('task_info')


def get_course_url(course):
    # 传入课程字典，拼接成课程链接
    cid = course.get('cid')
    term_id = course.get('term_id')
    course_id = course.get('taid')
    url = 'https://ke.qq.com/webcourse/{}/{}#taid={}&vid={}'.format(cid, term_id, course_id, course.get('resid_list'))
    return url


def get_all_urls(filename, term_index):
    chapters = get_chapters_from_file(filename, term_index)
    result = {}
    for chapter in chapters:
        chapter_name = chapter.get('name')
        courses = get_courses_from_chapter(chapter)
        chapter_info = {}
        for course in courses:
            # 这里跳过了文件类附件下载
            # TODO：添加附件下载支持
            chapter_info.update({course.get('name'): get_course_url(course)})
        result.update({chapter_name: chapter_info})
    return result


def print_menu(menu):
    for item in menu:
        print(str(menu.index(item))+'. '+item)


def ts2mp4(file):
    file = Path(file)
    ffmpeg = Path('ffmpeg.exe')
    basename = file.name.split('.')[0]
    file_dir = file.parent
    output = file_dir.joinpath(basename)
    cmd = str(ffmpeg) + " -i \"" + str(file) + "\" -c copy \"" + str(output) + "\".mp4"
    subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    file.unlink()


def choose_term(filename):
    terms = get_terms(filename)
    term_index = 0
    if len(terms) > 1:
        print_menu([i.get('name') for i in terms])
        term_index = int(input('请选择学期：'))
    term = terms[term_index]
    term_id = term.get('term_id')
    return term_index, term_id, term


def choose_chapter(term):
    chapters = get_chapters(term)
    chapter_names = [chapter.get('name') for chapter in chapters]
    print_menu(chapter_names)
    chapter_index = int(input('请选择章节：'))
    chapter = chapters[chapter_index]
    return chapter


def load_json_cookies():
    cookies = Path('cookies.json')
    if cookies.exists():
        res = {}
        for i in json.loads(cookies.read_bytes()):
            res.update({i['name']: i['value']})
        return res


def parse_video_url(video_url):
    # 从播放url中提取出获取token要用的file_id和term_id
    file_id = parse_qs(video_url).get('vid')[0]
    term_id = urlparse(video_url).path.split('/')[-1]
    return term_id, file_id


def get_video_token(term_id, file_id):
    # 获得sign, t, us这三个参数
    # 这三个参数用来获取视频m3u8
    url = 'https://ke.qq.com/cgi-bin/qcloud/get_token'
    params = {
        'term_id': term_id,
        'fileId': file_id
    }
    response = requests.get(url, params=params, cookies=load_json_cookies()).json()
    return response.get('result')


def get_video_info(file_id, t, sign, us):
    # 1258712167这个跟请求的cdn有关
    # 但我发现这东西写死在js里，且不同账户下不同课程都是用这一个cdn
    # 而且这东西没有通过api数据返回，初步判断它是固定的
    # 因此将其作为固定参数
    url = 'https://playvideo.qcloud.com/getplayinfo/v2/1258712167/' + str(file_id)
    params = {
        't': t,
        'sign': sign,
        'us': us,
        'exper': 0
    }
    response = requests.get(url, params=params, cookies=load_json_cookies()).json()
    return response


def get_token_for_key_url():
    # 这个key_url后面要接一个操蛋的token，研究发现，token是如下结构base64加密后得到的
    # uin=2300043476;skey=;pskey=;plskey=;ext=;uid_type=0;uid_origin_uid_type=0;cid=3026354;term_id=103142420;vod_type=0
    # 其中的plskey是要填的，这个东西来自登陆时的token去掉结尾的两个"="，也可以在cookies.json里获取
    cookies = Path('cookies.json')
    if cookies.exists():
        cookies = json.loads(cookies.read_bytes())
        qq_id = None
        p_lskey = None
        for cookie in cookies:
            if cookie.get('name') == 'p_lskey':
                p_lskey = cookie.get('value')
            if cookie.get('name') == 'ptui_loginuin':
                qq_id = cookie.get('value')
        str_token = 'uin={qq_id};' \
                    'skey=;pskey=;' \
                    'plskey={p_lskey};' \
                    'ext=;uid_type=0;uid_origin_uid_type=0;cid=3026354;term_id=103142420;vod_type=0'\
            .format(qq_id=qq_id, p_lskey=p_lskey)
        return base64.b64encode(str_token.encode()).decode()


def get_video_url(video_info, video_index=-1):
    # 接收来自get_video_info函数返回的视频信息
    # 根据video_index返回不同清晰度的视频ts下载链接
    video = video_info.get('videoInfo').get('transcodeList')[video_index]
    if video:
        video_url = video.get('url').replace('.m3u8', '.ts')
        key_url = get_key_url_from_m3u8(video.get('url')) + '&token=' + get_token_for_key_url()
        return video_url, key_url


def get_key_url_from_m3u8(m3u8_url):
    # 传入带sign, t, us参数的m3u8下载链接
    m3u8_text = requests.get(m3u8_url).text
    pattern = re.compile(r'(https://ke.qq.com/cgi-bin/qcloud/get_dk.+)"')
    return pattern.findall(m3u8_text)[0]


def get_download_url_from_course_url(video_url, video_index=-1):
    term_id, file_id = parse_video_url(video_url)
    tokens = get_video_token(term_id, file_id)
    video_info = get_video_info(file_id, tokens.get('t'), tokens.get('sign'), tokens.get('us'))
    return get_video_url(video_info, video_index)


def get_download_urls(term_id, file_id, video_index=-1):
    tokens = get_video_token(term_id, file_id)
    video_info = get_video_info(file_id, tokens.get('t'), tokens.get('sign'), tokens.get('us'))
    return get_video_url(video_info, video_index)
