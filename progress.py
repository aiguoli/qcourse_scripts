import requests


def download(file_url, filename):
    response = requests.get(file_url, stream=True)
    size = 0
    chunk_size = 1024
    content_size = int(response.headers['content-length'])
    print(content_size)
    if response.status_code == 200:
        print('正在下载 {filename},大小: {size:.2f} MB'.format(filename=filename,
                                                                 size=content_size / chunk_size / 1024))
        with open(filename, 'wb') as file:
            for data in response.iter_content(chunk_size=chunk_size):
                file.write(data)
                size += len(data)
                print('\r' + '[下载进度]:%s%.2f%%' % ('▋' * int(size * 50 / content_size),
                                                  float(size / content_size * 100)), end='')

