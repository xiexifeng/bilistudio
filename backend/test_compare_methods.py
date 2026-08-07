"""对比直接测试和通过函数测试的区别"""
import sys
sys.path.insert(0, '.')

from utils.bili_api import _create_session, reset_session_cache, clear_cache, _path_cooldown, _sign_wbi, _gen_dm_img_inter
import time

# 完全清除所有缓存和状态
reset_session_cache()
clear_cache()
_path_cooldown.clear()

print('=== 方法 1: 直接使用 session 测试 ===')
s = _create_session()

# 生成参数
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

# 直接发送请求
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

# 清除缓存
clear_cache()
_path_cooldown.clear()

print('\n=== 方法 2: 使用 _request 函数测试 ===')
from utils.bili_api import _request

try:
    data2 = _request(
        "https://api.bilibili.com/x/space/wbi/arc/search",
        params=params,
        extra_headers={"Referer": "https://space.bilibili.com/94510621/video"}
    )
    print(f'✅ SUCCESS! Code: {data2.get("code")}')
except Exception as e:
    print(f'❌ ERROR: {e}')
