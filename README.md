### 腾讯课堂脚本
要学一些东西，但腾讯课堂不支持自定义变速，播放时有水印，且有些老师的课一遍不够看，于是这个脚本诞生了。

这次更新了超多功能，测试效率非常不错！如果有问题，欢迎给我提issue！

里面可能还有bug，欢迎斧正。

> 2021.9.2测试可用

### 使用方法
下载代码并解压，确保你安装了python，版本>=3.5

windows：
依次运行下面的命令(保姆级教程)
``` shell
cd qcourse_scripts

python -m venv qcourse-venv

qcourse-venv\scripts\activate

pip install -r requirements.txt

playwright install msedge

python qcourse.py
```

linux:  
- `python` -> `python3`
- `pip` -> `pip3`
##### Tips
- cid是你登录后url里面的参数，代表course_id
- 若登录失效，删除`cookies.json`再重新运行脚本
### 功能
- 模拟登录，获取cookies
- 下载单个视频
- 按章节下载
- 下载整个课程
- 视频下载后自动转换为`mp4`格式(ffmpeg)
### 本次更新
- 采用playwright替换selenium
- 除了登录时必要操作，其他请求全改成腾讯课堂api，大幅度增加效率
- pathlib替换os.path
- 优化代码，修复bug
- 异步下载
