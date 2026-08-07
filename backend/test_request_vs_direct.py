"""深入对比 bili_api _request 和直接调用"""
import sys
sys.path.insert(0, '.')

import utils.bili_api
from utils.bili_api import _create_session, reset_session_cache, clear_cache, _path_cooldown, _sign_wbi, _gen_dm_img_inter, _request, _throttle
import time
import json
import hashlib
import hmac
import urllib.parse
from curl_cffi import requests as _http

# 彻底清理
reset_session_cache()
clear_cache()
_path_cooldown.clear()

# ============ 方法 1: 使用 bili_api 的 _request 函数 ============
print('=== 方法 1: 使用 bili_api 的 _request 函数 ===')

# 创建 session
s = _create_session()
print(f'Session 创建完成')

# 等待 10 秒
print('等待 10 秒...')
time.sleep(10)

# 生成 WBI 参数
params = _sign_wbi({
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
print(f'w_rid: {params["w_rid"]}')
print(f'wts: {params["wts"]}')

# 使用 _request 函数
print('\n使用 _request 函数发送请求...')
try:
    data = _request(
        "https://api.bilibili.com/x/space/wbi/arc/search",
        params=params,
        extra_headers={"Referer": "https://space.bilibili.com/94510621/video"}
    )
    print(f'✅ SUCCESS! Code: {data.get("code")}')
except Exception as e:
    print(f'❌ ERROR: {e}')

# 等待 10 秒
print('\n等待 10 秒...')
time.sleep(10)

# ============ 方法 2: 使用相同的 session 但不走 _request 函数 ============
print('\n=== 方法 2: 直接使用相同的 session ===')

# 重新生成参数（时间戳已过期）
params2 = _sign_wbi({
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
print(f'w_rid: {params2["w_rid"]}')
print(f'wts: {params2["wts"]}')

# 直接使用 session 发送请求
print('\n直接使用 session 发送请求...')
resp = s.get("https://api.bilibili.com/x/space/wbi/arc/search",
             params=params2,
             headers={"Referer": "https://space.bilibili.com/94510621/video"},
             timeout=10)
data = resp.json()
print(f'Code: {data.get("code")}')
if data.get('code') == 0:
    vlist = data.get('data', {}).get('list', {}).get('vlist', [])
    print(f'✅ SUCCESS! Videos count: {len(vlist)}')
else:
    print(f'❌ FAILED: {data.get("message")}')
    print(f'完整响应: {json.dumps(data, ensure_ascii=False)[:300]}')
