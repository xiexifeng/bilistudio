"""对比两种方式获取 WBI 密钥的区别"""
from curl_cffi import requests as _http
import time
import hashlib
import json
import hmac
import urllib.parse

# ============ 方法 1: 通过 nav 接口获取 WBI 密钥 ============
print('=== 方法 1: 通过 nav 接口获取 ===')

s1 = _http.Session(impersonate="chrome120")
s1.headers.update({
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "zh-CN,zh;q=0.9",
})

# 访问首页
s1.get("https://www.bilibili.com/", timeout=10)

# 添加 Cookie
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
params = {
    "key_id": "ec02",
    "hexsign": hexsign,
    "context[ts]": str(timestamp),
    "csrf": csrf,
}
resp = s1.post(url, params=params, timeout=10)
data = resp.json()
if data.get('code') == 0:
    ticket_data = data["data"]
    ticket = ticket_data["ticket"]
    s1.cookies.set("bili_ticket", ticket, domain=".bilibili.com")
    s1.cookies.set("bili_ticket", ticket, domain="api.bilibili.com")
    
    # 从 GenWebTicket 获取的 nav 数据
    nav_data = ticket_data.get("nav", {})
    if nav_data:
        print(f'GenWebTicket nav 数据: {json.dumps(nav_data, ensure_ascii=False)[:200]}')

# 等待 5 秒
print('等待 5 秒...')
time.sleep(5)

# 通过 nav 接口获取 WBI 密钥
resp = s1.get("https://api.bilibili.com/x/web-interface/nav", timeout=10)
nav_resp = resp.json()
if nav_resp.get('code') == 0:
    wbi_img = nav_resp['data']['wbi_img']
    img_key_nav = wbi_img["img_url"].rsplit("/", 1)[-1].split(".")[0]
    sub_key_nav = wbi_img["sub_url"].rsplit("/", 1)[-1].split(".")[0]
    print(f'nav 接口 img_key: {img_key_nav}')
    print(f'nav 接口 sub_key: {sub_key_nav}')

# 等待 3 秒
print('\n等待 3 秒...')
time.sleep(3)

# ============ 方法 2: GenWebTicket 获取的 WBI 密钥 ============
print('\n=== 方法 2: 使用 GenWebTicket 的 WBI 密钥 ===')

# 从 GenWebTicket 获取的 WBI 密钥
img_key_ticket = nav_data.get("img", "").rsplit("/", 1)[-1].split(".")[0] if nav_data else ""
sub_key_ticket = nav_data.get("sub", "").rsplit("/", 1)[-1].split(".")[0] if nav_data else ""
print(f'GenWebTicket img_key: {img_key_ticket}')
print(f'GenWebTicket sub_key: {sub_key_ticket}')

# 检查是否一致
if img_key_nav == img_key_ticket and sub_key_nav == sub_key_ticket:
    print('✅ WBI 密钥一致！')
else:
    print('❌ WBI 密钥不一致！')
    print(f'  nav: ({img_key_nav}, {sub_key_nav})')
    print(f'  GenWebTicket: ({img_key_ticket}, {sub_key_ticket})')

# 使用 GenWebTicket 的密钥生成签名并测试
MIXIN_KEY_ENC_TAB = [
    46, 47, 18, 2, 53, 8, 23, 32, 15, 50, 10, 31, 58, 3, 45, 35,
    27, 43, 5, 49, 33, 9, 42, 19, 29, 28, 14, 39, 12, 38, 41, 13,
    37, 48, 7, 16, 24, 55, 40, 61, 26, 17, 0, 1, 60, 51, 30, 4,
    22, 25, 54, 21, 56, 59, 6, 63, 57, 62, 11, 36, 20, 34, 44, 52,
]

# 分别用两种密钥测试
for method, (img_k, sub_k) in [("nav", (img_key_nav, sub_key_nav)), ("GenWebTicket", (img_key_ticket, sub_key_ticket))]:
    if not img_k or not sub_k:
        continue
    
    print(f'\n--- 测试 {method} 密钥 ---')
    raw = img_k + sub_k
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
    
    resp = s1.get("https://api.bilibili.com/x/space/wbi/arc/search",
                 params=params,
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
