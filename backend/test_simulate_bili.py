"""调试 _create_session 的请求流程"""
import sys
import time
import json
import hashlib
import hmac
import urllib.parse
import uuid
import random
import base64
import logging

logging.basicConfig(level=logging.DEBUG)

# ============ 测试 1: 模拟 bili_api 的 _create_session 流程 ============
print('=== 测试 1: 模拟 bili_api 流程 ===')
print()

from curl_cffi import requests as _http

# 步骤 1: 创建 session
print('步骤 1: 创建 session')
s = _http.Session(impersonate="chrome120")
s.headers.update({
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "zh-CN,zh;q=0.9",
})

# 步骤 2: 访问 B 站首页
print('步骤 2: 访问 B 站首页')
resp = s.get("https://www.bilibili.com/", timeout=10)
print(f'  状态: {resp.status_code}')
print(f'  Cookie 数量: {len(s.cookies.get_dict())}')

# 步骤 3: 注入用户 cookie
print('步骤 3: 注入用户 cookie')
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

# 步骤 4: 确保访客 cookie 存在
print('步骤 4: 确保访客 cookie 存在')
existing = s.cookies.get_dict()
needed_keys = ["buvid3", "buvid4", "buvid_fp", "b_nut", "_uuid"]
for key in needed_keys:
    if key in existing:
        print(f'  {key}: ✅ 已有')
    else:
        print(f'  {key}: ❌ 缺失')

# 步骤 5: 获取 bili_ticket
print('步骤 5: 获取 bili_ticket')
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
print(f'  GenWebTicket code: {data.get("code")}')
if data.get('code') == 0:
    ticket_data = data["data"]
    ticket = ticket_data["ticket"]
    s.cookies.set("bili_ticket", ticket, domain=".bilibili.com")
    s.cookies.set("bili_ticket", ticket, domain="api.bilibili.com")
    
    # 从 GenWebTicket 获取 WBI 密钥
    nav_data = ticket_data.get("nav", {})
    if nav_data:
        img_url = nav_data.get("img", "")
        sub_url = nav_data.get("sub", "")
        if img_url and sub_url:
            img_key = img_url.rsplit("/", 1)[-1].split(".")[0]
            sub_key = sub_url.rsplit("/", 1)[-1].split(".")[0]
            print(f'  GenWebTicket WBI 密钥: ({img_key}, {sub_key})')

# 等待 5 秒
print('步骤 6: 等待 5 秒')
time.sleep(5)

# 步骤 7: 发送 WBI 请求
print('步骤 7: 发送 WBI 请求')

# 使用 GenWebTicket 获取的 WBI 密钥
MIXIN_KEY_ENC_TAB = [
    46, 47, 18, 2, 53, 8, 23, 32, 15, 50, 10, 31, 58, 3, 45, 35,
    27, 43, 5, 49, 33, 9, 42, 19, 29, 28, 14, 39, 12, 38, 41, 13,
    37, 48, 7, 16, 24, 55, 40, 61, 26, 17, 0, 1, 60, 51, 30, 4,
    22, 25, 54, 21, 56, 59, 6, 63, 57, 62, 11, 36, 20, 34, 44, 52,
]
raw = img_key + sub_key
mixin_key = "".join(raw[i] for i in MIXIN_KEY_ENC_TAB if i < len(raw))[:32]

params_wbi = {
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

sorted_params = sorted(params_wbi.items(), key=lambda x: x[0])
query = urllib.parse.urlencode({k: _filter(v) for k, v in sorted_params})
w_rid = hashlib.md5((query + mixin_key).encode("utf-8")).hexdigest()
params_wbi["w_rid"] = w_rid

resp = s.get("https://api.bilibili.com/x/space/wbi/arc/search",
             params=params_wbi,
             headers={"Referer": "https://space.bilibili.com/94510621/video"},
             timeout=10)
data = resp.json()
print(f'  Code: {data.get("code")}')
print(f'  Message: {data.get("message")}')
if data.get('code') == 0:
    vlist = data.get('data', {}).get('list', {}).get('vlist', [])
    print(f'  ✅ SUCCESS! Videos count: {len(vlist)}')
else:
    print(f'  ❌ FAILED')
    print(f'  响应: {json.dumps(data, ensure_ascii=False)[:200]}')
