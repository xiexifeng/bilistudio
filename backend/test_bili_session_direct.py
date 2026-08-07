"""使用 bili_api 的 cookie 但直接发送请求"""
import sys
sys.path.insert(0, '.')

import time
import json
import hashlib
import hmac
import urllib.parse
from curl_cffi import requests as _http

# ============ 使用 bili_api 创建的 session，但绕过 _request 函数 ============
print('=== 使用 bili_api 创建 session，但直接发送请求 ===')

import utils.bili_api
utils.bili_api.reset_session_cache()
utils.bili_api.clear_cache()
utils.bili_api._path_cooldown.clear()

# 等待 30 秒
print('等待 30 秒...')
time.sleep(30)

# 使用 bili_api 创建 session
s = utils.bili_api._create_session()
print('Session 创建完成')

# 等待 10 秒
print('等待 10 秒...')
time.sleep(10)

# 使用 bili_api 的 _sign_wbi 生成参数
params = utils.bili_api._sign_wbi({
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
print(f'w_rid: {params["w_rid"]}')
print(f'wts: {params["wts"]}')

# 直接使用 session 发送请求（绕过 _request 函数）
print('\n直接发送请求（不通过 _request）...')
resp = s.get("https://api.bilibili.com/x/space/wbi/arc/search",
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

# 等待 10 秒
print('\n等待 10 秒...')
time.sleep(10)

# ============ 使用 bili_api 创建的 session，但使用简单参数 ============
print('\n=== 使用 bili_api 创建 session，发送简单请求 ===')

# 重新获取 session（因为可能已被修改）
s2 = utils.bili_api._create_session()

# 使用简单参数（不带 dm_* 参数）
MIXIN_KEY_ENC_TAB = [
    46, 47, 18, 2, 53, 8, 23, 32, 15, 50, 10, 31, 58, 3, 45, 35,
    27, 43, 5, 49, 33, 9, 42, 19, 29, 28, 14, 39, 12, 38, 41, 13,
    37, 48, 7, 16, 24, 55, 40, 61, 26, 17, 0, 1, 60, 51, 30, 4,
    22, 25, 54, 21, 56, 59, 6, 63, 57, 62, 11, 36, 20, 34, 44, 52,
]

wbi_keys = utils.bili_api._wbi_keys
if wbi_keys:
    img_key, sub_key = wbi_keys
    raw = img_key + sub_key
    mixin_key = "".join(raw[i] for i in MIXIN_KEY_ENC_TAB if i < len(raw))[:32]
    
    simple_params = {
        "mid": 94510621,
        "ps": 30,
        "pn": 1,
        "tid": 0,
        "keyword": "",
        "order": "pubdate",
        "wts": int(time.time()),
    }
    
    def _filter(s):
        return "".join(ch for ch in str(s) if ch not in "!'()*")
    
    sorted_params = sorted(simple_params.items(), key=lambda x: x[0])
    query = urllib.parse.urlencode({k: _filter(v) for k, v in sorted_params})
    w_rid = hashlib.md5((query + mixin_key).encode("utf-8")).hexdigest()
    simple_params["w_rid"] = w_rid
    
    print(f'使用简单参数（无 dm_*）:')
    print(f'  w_rid: {simple_params["w_rid"]}')
    print(f'  wts: {simple_params["wts"]}')
    
    # 发送请求
    print('\n发送简单请求...')
    resp = s2.get("https://api.bilibili.com/x/space/wbi/arc/search",
                 params=simple_params,
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
