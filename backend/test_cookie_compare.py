"""对比两个 session 的 cookie 细节"""
import sys
sys.path.insert(0, '.')

import time
import json
import hashlib
import hmac
import urllib.parse
from curl_cffi import requests as _http

# ============ 方法 1: 使用 _create_session ============
print('=== 方法 1: 使用 bili_api._create_session ===')

import utils.bili_api
utils.bili_api.reset_session_cache()
utils.bili_api.clear_cache()
utils.bili_api._path_cooldown.clear()

# 等待 30 秒
print('等待 30 秒...')
time.sleep(30)

s1 = utils.bili_api._create_session()

# 详细检查 cookie
print('\n方法 1 Cookie 详情:')
cookies1 = s1.cookies.get_dict()
for k, v in sorted(cookies1.items()):
    if len(v) > 50:
        v = v[:50] + '...'
    print(f'  {k}: {v}')

# ============ 方法 2: 直接创建 session ============
print('\n=== 方法 2: 直接创建 session ===')

s2 = _http.Session(impersonate="chrome120")
s2.headers.update({
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "zh-CN,zh;q=0.9",
})

# 访问首页
s2.get("https://www.bilibili.com/", timeout=10)

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
    s2.cookies.set(k, v, domain=".bilibili.com")
    s2.cookies.set(k, v, domain="api.bilibili.com")

# 获取 bili_ticket
timestamp = int(time.time())
key = b"XgwSnGZ1p"
msg = f"ts{timestamp}"
hexsign = hmac.new(key, msg.encode(), hashlib.sha256).hexdigest()
csrf = s2.cookies.get_dict().get("bili_jct", "")

url = "https://api.bilibili.com/bapis/bilibili.api.ticket.v1.Ticket/GenWebTicket"
params_ticket = {
    "key_id": "ec02",
    "hexsign": hexsign,
    "context[ts]": str(timestamp),
    "csrf": csrf,
}
resp = s2.post(url, params=params_ticket, timeout=10)
data = resp.json()
if data.get('code') == 0:
    ticket = data["data"]["ticket"]
    s2.cookies.set("bili_ticket", ticket, domain=".bilibili.com")
    s2.cookies.set("bili_ticket", ticket, domain="api.bilibili.com")

# 详细检查 cookie
print('\n方法 2 Cookie 详情:')
cookies2 = s2.cookies.get_dict()
for k, v in sorted(cookies2.items()):
    if len(v) > 50:
        v = v[:50] + '...'
    print(f'  {k}: {v}')

# 对比差异
print('\n=== Cookie 差异对比 ===')
all_keys = set(list(cookies1.keys()) + list(cookies2.keys()))
for k in sorted(all_keys):
    v1 = cookies1.get(k, 'MISSING')
    v2 = cookies2.get(k, 'MISSING')
    if v1 != v2:
        if len(v1) > 30: v1 = v1[:30] + '...'
        if len(v2) > 30: v2 = v2[:30] + '...'
        print(f'  {k}:')
        print(f'    方法1: {v1}')
        print(f'    方法2: {v2}')
