"""详细调试 bili_api 模块"""
import sys
import os
import importlib

sys.path.insert(0, '.')

# 在导入前清除所有可能的缓存
for f in os.listdir('.'):
    if f.endswith('.pyc'):
        os.remove(os.path.join('.', f))

import utils.bili_api
importlib.reload(utils.bili_api)

from utils.bili_api import _create_session, reset_session_cache, clear_cache, _path_cooldown, _sign_wbi, _gen_dm_img_inter, _get_bili_ticket
import time
import json

# 彻底清理
reset_session_cache()
clear_cache()
_path_cooldown.clear()

print('=== 调试 1: 创建 session ===')
s = _create_session()
cookies = s.cookies.get_dict()
print(f'Cookie 数量: {len(cookies)}')

# 检查关键 cookie
for key in ['buvid3', 'buvid4', 'buvid_fp', '_uuid', 'SESSDATA', 'bili_jct', 'bili_ticket']:
    val = cookies.get(key, 'MISSING')
    if val != 'MISSING':
        val = val[:30] + '...'
    print(f'  {key}: {val}')

# 等待 5 秒
print('\n等待 5 秒...')
time.sleep(5)

# 检查 bili_ticket 是否有效
print('\n=== 调试 2: 检查 bili_ticket ===')
import utils.bili_api as bili
print(f'_bili_ticket: {bili._bili_ticket[:30] if bili._bili_ticket else "None"}')
print(f'_bili_ticket_expires: {bili._bili_ticket_expires}')

# 检查 WBI 密钥
print('\n=== 调试 3: 检查 WBI 密钥 ===')
print(f'_wbi_keys: {bili._wbi_keys}')
print(f'_wbi_keys_ts: {bili._wbi_keys_ts}')

# 生成 WBI 参数
print('\n=== 调试 4: 生成 WBI 参数 ===')
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

# 等待 3 秒
print('\n等待 3 秒...')
time.sleep(3)

# 直接发送请求（使用 bili_api 的 session）
print('\n=== 调试 5: 直接发送 WBI 请求 ===')
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
    print(f'完整响应: {json.dumps(data, ensure_ascii=False)[:300]}')
