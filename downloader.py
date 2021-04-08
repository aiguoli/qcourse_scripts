import re
import requests
from Crypto import Random
from Crypto.Cipher import AES
import uuid
import os


def get_ts_url(url):
    parsed_url = re.sub('start=\d+&end=\d+', 'start=0', url)
    return parsed_url.replace('\n', '')


def download(file_url, filename):
    res = requests.get(file_url)
    with open(filename, 'wb') as f:
        f.write(res.content)
    print('downloaded')
    return 0


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


def random_filename():
    uuid_str = uuid.uuid4().hex
    return uuid_str


def download_single(ts_url, key_url, filename):
    ts_url = get_ts_url(ts_url)
    download(file_url=ts_url, filename=filename + '.ts')
    download(file_url=key_url, filename=filename)
    key = get_key(filename)
    decrypt_file(filename + '.ts', key)
    os.remove(filename)
    print(filename+' 下载完成！')


def main():
    with open('1.txt', 'r', encoding='utf-8') as f:
        urls = f.readlines()
    for i in range(0, len(urls), 3):
        ts_url = get_ts_url(urls[i])
        key_url = urls[i+1]
        filename = urls[i+2].replace('\n', '').replace('u_', '')
        download(file_url=ts_url, filename=filename+'.ts')
        download(file_url=key_url, filename=filename)
        key = get_key(filename)
        decrypt_file(filename+'.ts', key)
        os.remove(filename)
        print('done')


if __name__ == '__main__':
    main()
