### 腾讯课堂脚本
![pypi supported versions](https://img.shields.io/badge/python-3.5%20%7C%203.6%20%7C%203.7%20%7C%203.8-blue)  
要学一些东西，但腾讯课堂不支持自定义变速，播放时有水印，且有些老师的课一遍不够看，于是这个脚本诞生了。  

### 使用方法

cid是你登录后url里面的参数，代表course_id  
很简单，三部完成

> 下载代码, 配置环境为python3 + edge 89

> pip install -r requirements.txt

> python qcourse.py

### 功能
- 模拟登录，获取cookies（若cookies失效，删除`cookies.json`）
- 下载单个视频
- 按章节下载
- 下载整个课程
