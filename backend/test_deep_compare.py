"""详细对比 _create_session 和直接创建 session 的区别"""
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
print(f'Session 1 创建完成')

# 检查 cookie
cookies1 = s1.cookies.get_dict()
print(f'Cookie 数量: {len(cookies1)}')

# 检查 headers
print(f'Session headers 数量: {len(s1.headers)}')
for k, v in s1.headers.items():
    print(f'  {k}: {str(v)[:50]}')

# 检查 bili_api 模块的状态
print(f'\nbili_api 模块状态:')
print(f'  _wbi_keys: {utils.bili_api._wbi_keys}')
print(f'  _bili_ticket: {utils.bili_api._bili_ticket[:30] if utils.bili_api._bili_ticket else "None"}')

# 等待 10 秒
print('\n等待 10 秒...')
time.sleep(10)

# 使用 bili_api 的 _sign_wbi 生成参数
params1 = utils.bili_api._sign_wbi({
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
    'dm_img_inter': utils.bili_api._gen_dm_img_inter(),
})
print(f'\n参数 1:')
print(f'  w_rid: {params1["w_rid"]}')
print(f'  wts: {params1["wts"]}')
print(f'  dm_img_inter: {params1["dm_img_inter"]}')

# 发送请求
print('\n发送 WBI 请求...')
resp1 = s1.get("https://api.bilibili.com/x/space/wbi/arc/search",
              params=params1,
              headers={"Referer": "https://space.bilibili.com/94510621/video"},
              timeout=10)
data1 = resp1.json()
print(f'Code: {data1.get("code")}')
print(f'Message: {data1.get("message")}')
if data1.get('code') == 0:
    vlist = data1.get('data', {}).get('list', {}).get('vlist', [])
    print(f'✅ SUCCESS! Videos count: {len(vlist)}')
else:
    print(f'❌ FAILED')

# 等待 10 秒
print('\n等待 10 秒...')
time.sleep(10)

# ============ 方法 2: 直接创建 session ============
print('\n=== 方法 2: 直接创建 session ===')

s2 = _http.Session(impersonate="chrome120")
s2.headers.update({
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "zh-CN,zh;q=0.9",
})

# 访问首页
print('访问 B 站首页...')
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

# 等待 5 秒
print('等待 5 秒...')
time.sleep(5)

# 获取 WBI 密钥
resp = s2.get("https://api.bilibili.com/x/web-interface/nav", timeout=10)
nav_data = resp.json()
if nav_data.get('code') == 0:
    wbi_img = nav_data['data']['wbi_img']
    img_key = wbi_img["img_url"].rsplit("/", 1)[-1].split(".")[0]
    sub_key = wbi_img["sub_url"].rsplit("/", 1)[-1].split(".")[0]

# 检查 headers
print(f'Session headers 数量: {len(s2.headers)}')
for k, v in s2.headers.items():
    print(f'  {k}: {str(v)[:50]}')

# 生成参数
MIXIN_KEY_ENC_TAB = [
    46, 47, 18, 2, 53, 8, 23, 32, 15, 50, 10, 31, 58, 3, 45, 35,
    27, 43, 5, 49, 33, 9, 42, 19, 29, 28, 14, 39, 12, 38, 41, 13,
    37, 48, 7, 16, 24, 55, 40, 61, 26, 17, 0, 1, 60, 51, 30, 4,
    22, 25, 54, 21, 56, 59, 6, 63, 57, 62, 11, 36, 20, 34, 44, 52,
]
raw = img_key + sub_key
mixin_key = "".join(raw[i] for i in MIXIN_KEY_ENC_TAB if i < len(raw))[:32]

params2 = {
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

sorted_params = sorted(params2.items(), key=lambda x: x[0])
query = urllib.parse.urlencode({k: _filter(v) for k, v in sorted_params})
w_rid = hashlib.md5((query + mixin_key).encode("utf-8")).hexdigest()
params2["w_rid"] = w_rid

print(f'\n参数 2:')
print(f'  w_rid: {params2["w_rid"]}')
print(f'  wts: {params2["wts"]}')
print(f'  dm_img_inter: {params2["dm_img_inter"]}')

# 发送请求
print('\n发送 WBI 请求...')
resp2 = s2.get("https://api.bilibili.com/x/space/wbi/arc/search",
              params=params2,
              headers={"Referer": "https://space.bilibili.com/94510621/video"},
              timeout=10)
data2 = resp2.json()
print(f'Code: {data2.get("code")}')
print(f'Message: {data2.get("message")}')
if data2.get('code') == 0:
    vlist = data2.get('data', {}).get('list', {}).get('vlist', [])
    print(f'✅ SUCCESS! Videos count: {len(vlist)}')
else:
    print(f'❌ FAILED')
