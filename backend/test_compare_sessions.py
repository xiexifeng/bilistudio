"""对比 bili_api 模块与最小化测试的区别"""
import sys
sys.path.insert(0, '.')

import utils.bili_api
from utils.bili_api import _create_session, reset_session_cache, clear_cache, _path_cooldown, _sign_wbi, _gen_dm_img_inter
import time
import json
from curl_cffi import requests as _http
import hashlib
import hmac
import urllib.parse

# 彻底清理
reset_session_cache()
clear_cache()
_path_cooldown.clear()

# ============ 方法 1: 使用 bili_api 模块的 session ============
print('=== 方法 1: 使用 bili_api 模块 ===')
s_bili = _create_session()
print(f'Session 创建完成')

# 等待 10 秒让风控冷却
print('等待 10 秒...')
time.sleep(10)

# 检查 bili_api 的 WBI 密钥
print('\nbili_api WBI 密钥检查:')
print(f'  _wbi_keys: {utils.bili_api._wbi_keys}')
print(f'  _bili_ticket: {utils.bili_api._bili_ticket[:30] if utils.bili_api._bili_ticket else "None"}')

# 生成 WBI 参数
params_bili = _sign_wbi({
    'mid': 94510621, 'ps': 30, 'pn': 1,
    'tid': 0, 'keyword': '', 'order': 'pubdate',
    'index': 0,
    'special_type': '',
    'order_avoided': 'true',
    'platform': 'web',
    'web_location': '333.1387',
    'dm_img_list': '[]',
    'dm_img_str': 'V2ViR0wgMS4wIChPcGVuR0wgRVMgMi4wIENocm9taXVtKQ',
    'dm_cover_img_str': 'QU5HTEUgKEludGVsLCBJbnRlbChSKSBBcmMoVE0pIDEzMFQgR1BVICgxNkdCKSAoMHgwMDAwN0Q1MSkgRGlyZWN0M0QxMSB2c181XzAgcHNfNV8wLCBEM0QxMSlHb29nbGUgSW5jLiAoSW50ZWw=',
    'dm_img_inter': _gen_dm_img_inter(),
})
print(f'  w_rid: {params_bili["w_rid"]}')
print(f'  wts: {params_bili["wts"]}')

# 发送请求
print('\n发送 WBI 请求...')
resp = s_bili.get("https://api.bilibili.com/x/space/wbi/arc/search",
                  params=params_bili,
                  headers={"Referer": "https://space.bilibili.com/94510621/video"},
                  timeout=10)
data = resp.json()
print(f'Code: {data.get("code")}')
print(f'Message: {data.get("message")}')
if data.get('code') == 0:
    vlist = data.get('data', {}).get('list', {}).get('vlist', [])
    print(f'✅ SUCCESS! Videos count: {len(vlist)}')
else:
    print(f'❌ FAILED')

# 等待 10 秒
print('\n等待 10 秒...')
time.sleep(10)

# ============ 方法 2: 使用全新 session（不经过 bili_api）============
print('\n=== 方法 2: 使用全新 session ===')

s_fresh = _http.Session(impersonate="chrome120")
s_fresh.headers.update({
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "zh-CN,zh;q=0.9",
})

# 访问首页
print('访问 B 站首页...')
s_fresh.get("https://www.bilibili.com/", timeout=10)

# 添加相同的 Cookie
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
    s_fresh.cookies.set(k, v, domain=".bilibili.com")
    s_fresh.cookies.set(k, v, domain="api.bilibili.com")

# 获取 bili_ticket
timestamp = int(time.time())
key = b"XgwSnGZ1p"
msg = f"ts{timestamp}"
hexsign = hmac.new(key, msg.encode(), hashlib.sha256).hexdigest()
csrf = s_fresh.cookies.get_dict().get("bili_jct", "")

url = "https://api.bilibili.com/bapis/bilibili.api.ticket.v1.Ticket/GenWebTicket"
params_ticket = {
    "key_id": "ec02",
    "hexsign": hexsign,
    "context[ts]": str(timestamp),
    "csrf": csrf,
}
resp = s_fresh.post(url, params=params_ticket, timeout=10)
data = resp.json()
if data.get('code') == 0:
    ticket_data = data["data"]
    ticket = ticket_data["ticket"]
    s_fresh.cookies.set("bili_ticket", ticket, domain=".bilibili.com")
    s_fresh.cookies.set("bili_ticket", ticket, domain="api.bilibili.com")

# 等待 5 秒
print('等待 5 秒...')
time.sleep(5)

# 获取 WBI 密钥
resp = s_fresh.get("https://api.bilibili.com/x/web-interface/nav", timeout=10)
nav_data = resp.json()
if nav_data.get('code') == 0:
    wbi_img = nav_data['data']['wbi_img']
    img_key = wbi_img["img_url"].rsplit("/", 1)[-1].split(".")[0]
    sub_key = wbi_img["sub_url"].rsplit("/", 1)[-1].split(".")[0]

# 生成参数
MIXIN_KEY_ENC_TAB = [
    46, 47, 18, 2, 53, 8, 23, 32, 15, 50, 10, 31, 58, 3, 45, 35,
    27, 43, 5, 49, 33, 9, 42, 19, 29, 28, 14, 39, 12, 38, 41, 13,
    37, 48, 7, 16, 24, 55, 40, 61, 26, 17, 0, 1, 60, 51, 30, 4,
    22, 25, 54, 21, 56, 59, 6, 63, 57, 62, 11, 36, 20, 34, 44, 52,
]
raw = img_key + sub_key
mixin_key = "".join(raw[i] for i in MIXIN_KEY_ENC_TAB if i < len(raw))[:32]

params_fresh = {
    "mid": 94510621, "ps": 30, "pn": 1,
    "tid": 0, "keyword": "", "order": "pubdate",
    "index": 0,
    "special_type": "",
    "order_avoided": "true",
    "platform": "web",
    "web_location": "333.1387",
    "dm_img_list": "[]",
    "dm_img_str": "V2ViR0wgMS4wIChPcGVuR0wgRVMgMi4wIENocm9taXVtKQ",
    "dm_cover_img_str": "QU5HTEUgKEludGVsLCBJbnRlbChSKSBBcmMoVE0pIDEzMFQgR1BVICgxNkdCKSAoMHgwMDAwN0Q1MSkgRGlyZWN0M0QxMSB2c181XzAgcHNfNV8wLCBEM0QxMSlHb29nbGUgSW5jLiAoSW50ZWw=",
    "dm_img_inter": '{"ds":[],"wh":[3018,3156,88],"of":[284,568,284]}',
    "wts": int(time.time()),
}

def _filter(s):
    return "".join(ch for ch in str(s) if ch not in "!'()*")

sorted_params = sorted(params_fresh.items(), key=lambda x: x[0])
query = urllib.parse.urlencode({k: _filter(v) for k, v in sorted_params})
w_rid = hashlib.md5((query + mixin_key).encode("utf-8")).hexdigest()
params_fresh["w_rid"] = w_rid

# 发送请求
print('\n发送 WBI 请求...')
resp = s_fresh.get("https://api.bilibili.com/x/space/wbi/arc/search",
                   params=params_fresh,
                   headers={"Referer": "https://space.bilibili.com/94510621/video"},
                   timeout=10)
data = resp.json()
print(f'Code: {data.get("code")}')
print(f'Message: {data.get("message")}')
if data.get('code') == 0:
    vlist = data.get('data', {}).get('list', {}).get('vlist', [])
    print(f'✅ SUCCESS! Videos count: {len(vlist)}')
else:
    print(f'❌ FAILED')
