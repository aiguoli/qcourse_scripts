### 腾讯课堂脚本
要学一些东西，但腾讯课堂不支持自定义变速，播放时有水印，且有些老师的课一遍不够看，于是这个脚本诞生了。

时间比较紧张，只会不定时修复重大bug。多线程下载之类的功能更新短期内不会有，如果你想一起完善这个脚本，欢迎pr

> 2020.5.22测试可用

### 使用方法
很简单，三部完成

``` python
下载代码, 配置环境为python3 + edge 89
```
``` python
> pip install -r requirements.txt
```
``` python
> python qcourse.py
```
##### Tips
- cid是你登录后url里面的参数，代表course_id
- 若登录失效，删除`cookies.json`再重新运行脚本
### 功能
- 模拟登录，获取cookies
- 下载单个视频
- 按章节下载
- 下载整个课程
- 视频下载后自动转换为`mp4`格式(ffmpeg)
