"""直接测试 B 站 API 对不同 UID 的返回"""
import sys
sys.path.insert(0, '.')

from curl_cffi import requests as _http
import time
import hashlib
import hmac
import urllib.parse
import json

# 创建 session
print('创建 session...')
s = _http.Session(impersonate="chrome120")
s.headers.update({
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "zh-CN,zh;q=0.9",
})

# 访问首页
s.get("https://www.bilibili.com/", timeout=10)

# 添加用户 cookie
user_cookies = {
    "buvid3": "365FC941-E43B-E635-D10B-14A06092BDCE13280infoc",
    "b_nut": "1768464613",
    "_uuid": "5A847668-5593-FD71-2FA2-49AED449FDB615603infoc",
    "buvid_fp": "6230edfabc0bd9d217de3549dc899fa5",
    "buvid4": "9BE2CE9A-8F82-8278-C03A-A923D0902FDA18545-026011516-PaAP8UZVM/MV+25M0j4AEg%3D%3D",
    "SESSDATA": "2e6f20cd%2C1801460870%2C91462%2A82CjANJ6g0mpYcDsDbm9vsFgsRLSbDmflBOGv6xCLflbQNyLLUQf8uxI_TREKQA_kjyGASVmF5Mk5fbzlMR1JNRV9LRkhNOV9BZHdlRkpBS2JCWHFZME5zaVNHanJVX3Z0NVFmU2xQU0prR1MwekJMOENjNFNtdncyNHdFU1B5RVVYUF8xNmZrZEd3IIEC",
    "bili_jct": "6eb5f972c375cd9885f1a03d71866534",
    "DedeUserID": "3546612563446355",
    "sid": "5s9l2e1c",
}
for k, v in user_cookies.items():
    s.cookies.set(k, v, domain=".bilibili.com")
    s.cookies.set(k, v, domain="api.bilibili.com")

# 获取 bili_ticket
timestamp = int(time.time())
key = b"XgwSnGZ1p"
msg = f"ts{timestamp}"
hexsign = hmac.new(key, msg.encode(), hashlib.sha256).hexdigest()
csrf = s.cookies.get_dict().get("bili_jct", "")

url = "https://api.bilibili.com/bapis/bilibili.api.ticket.v1.Ticket/GenWebTicket"
params_ticket = {
    "key_id": "ec02",
    "hexsign": hexsign,
    "context[ts]": str(timestamp),
    "csrf": csrf,
}
resp = s.post(url, params=params_ticket, timeout=10)
data = resp.json()
if data.get('code') == 0:
    ticket = data["data"]["ticket"]
    s.cookies.set("bili_ticket", ticket, domain=".bilibili.com")
    s.cookies.set("bili_ticket", ticket, domain="api.bilibili.com")

# 等待 5 秒
print('等待 5 秒...')
time.sleep(5)

# 直接测试 UID 94510621（李永乐老师）
print('\n=== 测试 UID 94510621 (李永乐老师) ===')
resp = s.get("https://api.bilibili.com/x/space/wbi/acc/info",
            params={"mid": 94510621},
            headers={"Referer": "https://space.bilibili.com/94510621"},
            timeout=10)
user_data = resp.json()
if user_data.get('code') == 0:
    data = user_data['data']
    print(f'  Name: {data.get("name")}')
    print(f'  Mid: {data.get("mid")}')
    print(f'  Fans: {data.get("fans")}')
    print(f'  Level: {data.get("level")}')
else:
    print(f'  Error: {user_data.get("message")}')

# 等待 3 秒
time.sleep(3)

# 使用 legacy 接口测试视频列表
print('\n=== 使用 legacy 接口测试视频列表 ===')
resp = s.get("https://api.bilibili.com/x/space/arc/search",
            params={"mid": 94510621, "ps": 30, "pn": 1, "order": "pubdate"},
            headers={"Referer": "https://space.bilibili.com/94510621/video"},
            timeout=10)
video_data = resp.json()
if video_data.get('code') == 0:
    vlist = video_data['data']['list']['vlist']
    count = video_data['data']['page']['count']
    print(f'  Total videos: {count}')
    if vlist:
        print(f'  First few videos:')
        for i, v in enumerate(vlist[:3]):
            print(f'    [{i}] {v.get("title", "")[:40]}')
            print(f'        author: {v.get("author")}')
            print(f'        mid: {v.get("mid")}')
else:
    print(f'  Error: {video_data.get("message")}')
