import re
import requests
from Crypto import Random
from Crypto.Cipher import AES
import os


def get_ts_url(url):
    parsed_url = re.sub('start=\d+&end=\d+', 'start=0', url)
    return parsed_url.replace('\n', '')


def download(file_url, filename):
    res = requests.get(file_url)
    with open(filename, 'wb') as f:
        f.write(res.content)
    return 0


def lg_download(file_url, filename):
    response = requests.get(file_url, stream=True)
    size = 0
    chunk_size = 1024
    content_size = int(response.headers['content-length'])
    if response.status_code == 200:
        print('正在下载 {filename},大小: {size:.2f} MB'.format(filename=filename,
                                                                 size=content_size / chunk_size / 1024))
        with open(filename, 'wb') as file:
            for data in response.iter_content(chunk_size=chunk_size):
                file.write(data)
                size += len(data)
                print('\r' + '[下载进度]:%s%.2f%%' % ('▋' * int(size * 50 / content_size),
                                                  float(size / content_size * 100)), end='')


def add_to_16(value):
    while len(value) % 16 != 0:
        value += '\0'
    return str.encode(value)


def encrypt(message, key, key_size=256):
    message = add_to_16(message)
    iv = Random.new().read(AES.block_size)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    return iv + cipher.encrypt(message)


def decrypt(ciphertext, key):
    iv = ciphertext[:AES.block_size]
    cipher = AES.new(key, AES.MODE_CBC, iv)
    plaintext = cipher.decrypt(ciphertext[AES.block_size:])
    return plaintext.rstrip(b"\0")


def decrypt_file(filename, key):
    with open(filename, 'rb') as f:
        ciphertext = f.read()
    dec = decrypt(ciphertext, key)
    with open(filename, 'wb') as f:
        f.write(dec)


def get_key(filename):
    with open(filename, 'rb') as f:
        key = f.read()
    return key


def download_single(ts_url, key_url, filename):
    ts_url = get_ts_url(ts_url)
    lg_download(file_url=ts_url, filename=filename + '.ts')
    download(file_url=key_url, filename=filename)
    key = get_key(filename)
    decrypt_file(filename + '.ts', key)
    os.remove(filename)
    print(filename+' 下载完成！')
    return 0
#
#
# def main():
#     with open('1.txt', 'r', encoding='utf-8') as f:
#         urls = f.readlines()
#     for i in range(0, len(urls), 3):
#         ts_url = get_ts_url(urls[i])
#         key_url = urls[i+1]
#         filename = urls[i+2].replace('\n', '').replace('u_', '')
#         download(file_url=ts_url, filename=filename+'.ts')
#         download(file_url=key_url, filename=filename)
#         key = get_key(filename)
#         decrypt_file(filename+'.ts', key)
#         os.remove(filename)
#         print('done')
#
#
# if __name__ == '__main__':
#     main()
