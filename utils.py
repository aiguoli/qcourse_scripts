import base64
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

import requests
from requests.utils import dict_from_cookiejar, cookiejar_from_dict
import json
import subprocess
from urllib.parse import urlparse, parse_qs
from urllib.request import getproxies


class API:
    ItemsUri = 'https://ke.qq.com/cgi-bin/course/get_terms_detail'
    TokenUri = 'https://ke.qq.com/cgi-bin/qcloud/get_token'
    MediaUri = 'https://playvideo.qcloud.com/getplayinfo/v2/1258712167/'
    InfoUri = 'https://ke.qq.com/cgi-bin/identity/info?'
    BasicInfoUri = 'https://ke.qq.com/cgi-bin/course/basic_info?cid={cid}'
    MiniAppQrcode = 'https://ke.qq.com/cgi-proxy/get_miniapp_qrcode?'
    LoginState = 'https://ke.qq.com/cgi-proxy/get_login_state?'
    A2Login = 'https://ke.qq.com/cgi-proxy/account_login/a2_login?'
    XLogin = 'https://xui.ptlogin2.qq.com/cgi-bin/xlogin?'
    PtQrShow = 'https://ssl.ptlogin2.qq.com/ptqrshow?'
    PtQrLogin = 'https://ssl.ptlogin2.qq.com/ptqrlogin?'
    Check = 'https://ssl.ptlogin2.qq.com/check?'
    CourseList = 'https://ke.qq.com/cgi-proxy/user/user_center/get_plan_list'
    VideoRec = 'https://ke.qq.com/cgi-proxy/rec_video/describe_rec_video'
    DefaultAccount = 'https://ke.qq.com/cgi-proxy/accbind/get_default_account'


DEFAULT_HEADERS = {'referer': 'https://ke.qq.com/webcourse/'}
CURRENT_USER = {}
PROXIES = getproxies()  # 当你使用魔法，避免出现check_hostname requires server_hostname


def get_course_from_api(cid):
    # 获取课程信息
    # url = 'https://ke.qq.com/cgi-bin/course/basic_info?cid=' + str(cid)
    url = API.BasicInfoUri.format(cid=cid)
    response = requests.get(url, headers=DEFAULT_HEADERS, proxies=PROXIES).json()
    name = (
        response.get('result')
            .get('course_detail')
            .get('name')
            .replace('/', '／')
            .replace('\\', '＼')
    )
    with open(name + '.json', 'w') as f:
        json.dump(response, f, ensure_ascii=False, indent=4)
    return name


def get_terms_from_api(cid, term_id_list):
    # term_id_list是一个数组，里面是整数格式的term_id
    params = {'cid': cid, 'term_id_list': term_id_list}
    response = requests.get(API.ItemsUri, params=params, headers=DEFAULT_HEADERS, proxies=PROXIES).json()
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
    chapters = (
        course_info.get('result')
            .get('course_detail')
            .get('terms')[term_index]
            .get('chapter_info')[0]
            .get('sub_info')
    )
    return chapters


def get_chapters(term):
    return term.get('chapter_info')[0].get('sub_info')


def get_courses_from_chapter(chapter):
    return chapter.get('task_info')


def get_all_courses():
    # 下个版本加入该函数，用于获取用户计划内的课程，在脚本运行时不用输入cid了
    # count参数最多为10，返回response中end代表有没有下一页
    # 考虑到课程一般不会有几百个，所以不做分页处理
    def _load_res(r):
        if r:
            for i in r.get('map_list'):
                for j in i.get('map_courses'):
                    res.append({
                        'name': j.get('cname'),
                        'cid': j.get('cid')
                    })
    res = []
    page = 1
    response = requests.get(API.CourseList,
                            params={'page': page, 'count': '10'},
                            headers=DEFAULT_HEADERS,
                            cookies=load_json_cookies(),
                            proxies=PROXIES).json().get('result')
    _load_res(response)
    while response.get('end') == 0:
        page += 1
        response = requests.get(API.CourseList,
                                params={'page': page, 'count': '10'},
                                headers=DEFAULT_HEADERS,
                                cookies=load_json_cookies(),
                                proxies=PROXIES).json().get('result')
        _load_res(response)
    return res


def choose_course():
    courses = get_all_courses()
    print('你的账号里有如下课程：')
    for course in courses:
        print(str(courses.index(course)) + '. ' + course.get('name'))
    cid = courses[int(input('请输入要下载的课程序号(回车结束)：'))].get('cid')
    return cid


def get_course_url(course):
    # 传入课程字典，拼接成课程链接
    cid = course.get('cid')
    term_id = course.get('term_id')
    course_id = course.get('taid')
    url = 'https://ke.qq.com/webcourse/{}/{}#taid={}&vid={}'.format(
        cid, term_id, course_id, course.get('resid_list')
    )
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
        print(str(menu.index(item)) + '. ' + item)


def run_shell(shell, retry=True, retry_times=3):
    cmd = subprocess.Popen(
        shell,
        close_fds=True,
        shell=True,
        bufsize=1,
        stderr=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
    )

    if retry and cmd.returncode != 0:
        time.sleep(1)
        if retry_times > 0:
            return run_shell(shell, retry=True, retry_times=retry_times - 1)
        print('\nShell出现异常，请自行查看课程文件是否转码成功')
    return cmd.returncode


def ts2mp4(file):
    file = Path(file)
    ffmpeg = Path('ffmpeg.exe')
    basename = file.name.split('.ts')[0]
    file_dir = file.parent
    output = file_dir.joinpath(basename)
    cmd = str(ffmpeg) + ' -i "' + str(file) + '" -c copy "' + str(output) + '".mp4'
    # 这个命令会报错，但是我不熟悉ffmpeg，而且似乎输出视频没有毛病，所以屏蔽了错误输出
    run_shell(cmd, retry_times=False)
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
        return cookiejar_from_dict(json.loads(cookies.read_bytes()))


def parse_video_url(video_url):
    # 从播放url中提取出获取token要用的file_id和term_id
    file_id = parse_qs(video_url).get('vid')[0]
    term_id = urlparse(video_url).path.split('/')[-1]
    return term_id, file_id


def parse_cid_url(video_url):
    pattern = re.compile('https://ke.qq.com/webcourse/(.*)/')
    return pattern.findall(video_url)[0]


def get_video_token(term_id, file_id):
    # 获得sign, t, us这三个参数 这三个参数用来获取视频m3u8
    params = {'term_id': term_id, 'fileId': file_id}
    response = requests.get(
        API.TokenUri, params=params, cookies=load_json_cookies(), proxies=PROXIES
    ).json()
    return response.get('result')


def get_video_info(file_id, t, sign, us):
    """
    1258712167这个跟请求的cdn有关
    但我发现这东西写死在js里，且不同账户下不同课程都是用这一个cdn
    而且这东西没有通过api数据返回，初步判断它是固定的
    因此将其作为固定参数
    """
    url = API.MediaUri + str(file_id)
    params = {'t': t, 'sign': sign, 'us': us, 'exper': 0}
    response = requests.get(url, params=params, cookies=load_json_cookies(), proxies=PROXIES).json()
    return response


def get_token_for_key_url(term_id, cid):
    """
    这个key_url后面要接一个token，研究发现，token是如下结构base64加密后得到的
    其中的plskey是要填的，这个东西来自登陆时的token去掉结尾的两个'='，也可以在cookies.json里获取
    """
    if not CURRENT_USER:
        cookies = Path('cookies.json')
        if cookies.exists():
            cookies = json.loads(cookies.read_bytes())
            uin = get_uin()
            CURRENT_USER['uin'] = uin
            if len(CURRENT_USER.get('uin')) > 10:
                # 微信
                CURRENT_USER['ext'] = cookies.get('uid_a2')
                CURRENT_USER['appid'] = cookies.get('uid_appid')
                CURRENT_USER['uid_type'] = cookies.get('uid_type')
                str_token = 'uin={uin};skey=;pskey=;plskey=;ext={uid_a2};uid_appid={appid};' \
                            'uid_type={uid_type};uid_origin_uid_type=2;uid_origin_auth_type=2;' \
                            'cid={cid};term_id={term_id};vod_type=0;platform=3'\
                    .format(uin=uin,
                            uid_a2=CURRENT_USER.get('ext'),
                            appid=CURRENT_USER.get('appid'),
                            uid_type=CURRENT_USER.get('uid_type'),
                            cid=cid,
                            term_id=term_id)
            else:
                skey = pskey = plskey = None
                CURRENT_USER['p_lskey'] = cookies.get('p_lskey')
                CURRENT_USER['skey'] = cookies.get('skey')
                CURRENT_USER['pskey'] = cookies.get('p_skey')
                str_token = 'uin={uin};skey={skey};pskey={pskey};plskey={plskey};ext=;uid_type=0;' \
                            'uid_origin_uid_type=0;uid_origin_auth_type=0;cid={cid};term_id={term_id};' \
                            'vod_type=0'\
                    .format(uin=uin,
                            skey=CURRENT_USER.get('skey'),
                            pskey=CURRENT_USER.get('pskey'),
                            plskey=CURRENT_USER.get('plskey'),
                            cid=cid,
                            term_id=term_id)
            CURRENT_USER['token'] = str_token

    # 直接从CURRENT_USER里读取参数
    return base64.b64encode(CURRENT_USER.get('token').encode()).decode()[:-2]


def get_video_url(video_info, video_index=-1, cid=None, term_id=None):
    """
    接收来自get_video_info函数返回的视频信息
    根据video_index返回不同清晰度的视频ts下载链接
    """
    video = video_info.get('videoInfo').get('transcodeList', None)
    if video:
        video = video[video_index]
        video_url = video.get('url').replace('.m3u8', '.ts')
        key_url = (
                get_key_url_from_m3u8(video.get('url'))
                + '&token='
                + get_token_for_key_url(term_id=term_id, cid=cid)
        )
        return video_url, key_url
    return video_info.get('videoInfo').get('sourceVideo').get('url'), None


def get_key_url_from_m3u8(m3u8_url):
    # 传入带sign, t, us参数的m3u8下载链接
    m3u8_text = requests.get(m3u8_url, proxies=PROXIES).text
    pattern = re.compile(r'(https://ke.qq.com/cgi-bin/qcloud/get_dk.+)"')
    return pattern.findall(m3u8_text)[0]


def get_download_url_from_course_url(video_url, video_index=-1):
    term_id, file_id = parse_video_url(video_url)
    cid = parse_cid_url(video_url)
    tokens = get_video_token(term_id, file_id)
    video_info = get_video_info(
        file_id, tokens.get('t'), tokens.get('sign'), tokens.get('us')
    )
    return get_video_url(video_info, video_index, cid=cid, term_id=term_id)


def get_download_urls(term_id, file_id, video_index=-1, cid=None):
    tokens = get_video_token(term_id, file_id)
    video_info = get_video_info(
        file_id, tokens.get('t'), tokens.get('sign'), tokens.get('us')
    )
    return get_video_url(video_info, video_index, cid=cid, term_id=term_id)


def clear_screen():
    if sys.platform.startswith('win'):
        os.system('cls')
    else:
        os.system('clear')


def get_video_rec(cid, file_id, term_id, video_index=0):
    # 腾讯课堂现在强制绑定手机号，看样子是更新了
    # 新发现的接口，疑似wechat / qq通用，无需cookie，只要uin
    # 返回dk( ts文件密匙 )，视频文件链接，时长，生存时间，字幕等信息
    # 这里返回的rec_video_info.info里面含有不同清晰度的视频文件，越清晰的排序越靠前
    params = {
        'course_id': cid,
        'file_id': file_id,
        'term_id': term_id,
        'header': '{{"srv_appid":201,"cli_appid":"ke","uin":"{}","cli_info":{{"cli_platform":3}}}}'.format(get_uin())
    }
    response = requests.get(API.VideoRec, headers=DEFAULT_HEADERS, params=params, proxies=PROXIES).json()
    if response:
        info = response.get('result').get('rec_video_info')
        ts_url = info.get('infos')[video_index].get('url').replace('.m3u8', '.ts')
        key = info.get('dk')
        return ts_url, key


def get_uin():
    response = requests.get(API.DefaultAccount,
                            cookies=load_json_cookies(),
                            headers=DEFAULT_HEADERS,
                            proxies=PROXIES).json()
    if response.get('retcode') == 0:
        return response.get('result').get('tiny_id')
    return input('请输入你的QQ号 / 微信uin(回车结束)：')

