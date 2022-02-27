import os
import requests
from pathlib import Path
from downloader import ts2mp4, progress


def get_m3u8_body(url):
    print('read m3u8 file:', url)
    with requests.Session() as session:
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=10, pool_maxsize=10, max_retries=10
        )
        session.mount('http://', adapter)
        session.mount('https://', adapter)
        r = session.get(url, timeout=10)
    return r.text


def get_url_list(host, body):
    lines = body.split('\n')
    ts_url_list = []
    for line in lines:
        if not line.startswith('#') and line != '':
            if line.lower().startswith('http'):
                ts_url_list.append(line)
            else:
                ts_url_list.append('%s/%s' % (host, line))
    return ts_url_list


def _download_ts_file(ts_url_list, file):
    i = 0
    total = len(ts_url_list)
    for ts_url in ts_url_list:
        i += 1
        r = requests.get(ts_url)
        with open(file, 'ab') as f:
            f.write(r.content)
        progress(i / total * 100)
    print(f'{file}下载完成')
    return file


def _check_dir(path):
    if os.path.exists(path):
        return
    os.makedirs(path)


def get_download_url_list(host, m3u8_url, url_list=None):
    if url_list is None:
        url_list = []
    body = get_m3u8_body(m3u8_url)
    ts_url_list = get_url_list(host, body)
    for url in ts_url_list:
        if url.lower().endswith('.m3u8'):
            url_list = get_download_url_list(host, url, url_list)
        else:
            url_list.append(url)
    return url_list


def download_ts(m3u8_url, path: Path, filename, begin=0):
    _check_dir(path)
    host = m3u8_url[: m3u8_url.rindex('/')]
    ts_url_list = get_download_url_list(host, m3u8_url)[begin:]
    print('Total file count:', len(ts_url_list))
    return _download_ts_file(ts_url_list, path.joinpath(filename))


def download_m3u8_raw(m3u8_url, path: Path, filename, trash_first):
    if trash_first:
        begin = 2
    else:
        begin = 0
    ts2mp4(download_ts(m3u8_url, path, filename, begin))


__all__ = ['download_ts']
