"""验证 headers 覆盖问题"""
from curl_cffi import requests as _http
import time
import hashlib
import json
import hmac
import urllib.parse

# ============ 测试 1: 不传递 extra_headers ============
print('=== 测试 1: 不传递 extra_headers ===')
s1 = _http.Session(impersonate="chrome120")
s1.headers.update({
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "zh-CN,zh;q=0.9",
})

# 访问首页
s1.get("https://www.bilibili.com/", timeout=10)

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
    s1.cookies.set(k, v, domain=".bilibili.com")
    s1.cookies.set(k, v, domain="api.bilibili.com")

# 获取 bili_ticket
timestamp = int(time.time())
key = b"XgwSnGZ1p"
msg = f"ts{timestamp}"
hexsign = hmac.new(key, msg.encode(), hashlib.sha256).hexdigest()
csrf = s1.cookies.get_dict().get("bili_jct", "")

url = "https://api.bilibili.com/bapis/bilibili.api.ticket.v1.Ticket/GenWebTicket"
params_ticket = {
    "key_id": "ec02",
    "hexsign": hexsign,
    "context[ts]": str(timestamp),
    "csrf": csrf,
}
resp = s1.post(url, params=params_ticket, timeout=10)
data = resp.json()
if data.get('code') == 0:
    ticket = data["data"]["ticket"]
    s1.cookies.set("bili_ticket", ticket, domain=".bilibili.com")
    s1.cookies.set("bili_ticket", ticket, domain="api.bilibili.com")

# 等待 5 秒
time.sleep(5)

# 获取 WBI 密钥
resp = s1.get("https://api.bilibili.com/x/web-interface/nav", timeout=10)
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

params = {
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

sorted_params = sorted(params.items(), key=lambda x: x[0])
query = urllib.parse.urlencode({k: _filter(v) for k, v in sorted_params})
w_rid = hashlib.md5((query + mixin_key).encode("utf-8")).hexdigest()
params["w_rid"] = w_rid

# 不传递 extra_headers
resp = s1.get("https://api.bilibili.com/x/space/wbi/arc/search",
             params=params,
             timeout=10)
data = resp.json()
print(f'Code: {data.get("code")}')
if data.get('code') == 0:
    vlist = data.get('data', {}).get('list', {}).get('vlist', [])
    print(f'✅ SUCCESS! Videos count: {len(vlist)}')
else:
    print(f'❌ FAILED: {data.get("message")}')

# 等待 10 秒
print('\n等待 10 秒...')
time.sleep(10)

# ============ 测试 2: 传递 extra_headers ============
print('\n=== 测试 2: 传递 extra_headers ===')
s2 = _http.Session(impersonate="chrome120")
s2.headers.update({
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "zh-CN,zh;q=0.9",
})

# 访问首页
s2.get("https://www.bilibili.com/", timeout=10)

# 添加用户 cookie
for k, v in user_cookies.items():
    s2.cookies.set(k, v, domain=".bilibili.com")
    s2.cookies.set(k, v, domain="api.bilibili.com")

# 获取 bili_ticket
timestamp = int(time.time())
hexsign = hmac.new(key, f"ts{timestamp}".encode(), hashlib.sha256).hexdigest()
csrf = s2.cookies.get_dict().get("bili_jct", "")
resp = s2.post(url, params={
    "key_id": "ec02",
    "hexsign": hexsign,
    "context[ts]": str(timestamp),
    "csrf": csrf,
}, timeout=10)
data = resp.json()
if data.get('code') == 0:
    ticket = data["data"]["ticket"]
    s2.cookies.set("bili_ticket", ticket, domain=".bilibili.com")
    s2.cookies.set("bili_ticket", ticket, domain="api.bilibili.com")

# 等待 5 秒
time.sleep(5)

# 获取 WBI 密钥
resp = s2.get("https://api.bilibili.com/x/web-interface/nav", timeout=10)
nav_data = resp.json()
if nav_data.get('code') == 0:
    wbi_img = nav_data['data']['wbi_img']
    img_key = wbi_img["img_url"].rsplit("/", 1)[-1].split(".")[0]
    sub_key = wbi_img["sub_url"].rsplit("/", 1)[-1].split(".")[0]

# 生成参数
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

sorted_params = sorted(params2.items(), key=lambda x: x[0])
query = urllib.parse.urlencode({k: _filter(v) for k, v in sorted_params})
w_rid = hashlib.md5((query + mixin_key).encode("utf-8")).hexdigest()
params2["w_rid"] = w_rid

# 传递 extra_headers
extra_headers = {"Referer": "https://space.bilibili.com/94510621/video"}
resp = s2.get("https://api.bilibili.com/x/space/wbi/arc/search",
             params=params2,
             headers=extra_headers,
             timeout=10)
data = resp.json()
print(f'Code: {data.get("code")}')
if data.get('code') == 0:
    vlist = data.get('data', {}).get('list', {}).get('vlist', [])
    print(f'✅ SUCCESS! Videos count: {len(vlist)}')
else:
    print(f'❌ FAILED: {data.get("message")}')
