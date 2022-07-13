### 腾讯课堂脚本
要学一些东西，但腾讯课堂不支持自定义变速，播放时有水印，且有些老师的课一遍不够看，于是这个脚本诞生了。

项目中可能还有bug，欢迎斧正。

> 2022.7.13测试可用

### 使用方法
下载代码并解压，确保你安装了python，版本>=3.5

windows：
依次运行下面的命令(保姆级教程)
``` shell
cd qcourse_scripts

python -m venv qcourse-venv

qcourse-venv\scripts\activate

pip install -Ur requirements.txt

playwright install msedge

python qcourse.py
```

linux:  
- `python` -> `python3`
- `pip` -> `pip3`
##### Tips
~- cid是你登录后url里面的参数，代表course_id~
- 若登录失效，删除`cookies.json`再重新运行脚本
- 遇到msedgedriver版本不匹配，可在该地址下载最新版的驱动 https://msedgewebdriverstorage.z22.web.core.windows.net/
### 功能
- 模拟登录，支持QQ / 微信，获取cookies
- 下载单个视频
- 按章节下载
- 下载整个课程
- 视频下载后自动转换为`mp4`格式(ffmpeg)

