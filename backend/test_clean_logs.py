"""清除日志后重新测试"""
import sys
sys.path.insert(0, '.')

import time
print('测试开始...')
print('当前时间:', time.time())

print('\n导入 bili_api 模块...')
import utils.bili_api
print('导入完成')

# 检查全局状态
print('\n检查全局状态:')
print(f'  _session_cache: {utils.bili_api._session_cache is not None}')
print(f'  _wbi_keys: {utils.bili_api._wbi_keys}')
print(f'  _bili_ticket: {utils.bili_api._bili_ticket[:30] if utils.bili_api._bili_ticket else "None"}')

# 彻底清理
utils.bili_api.reset_session_cache()
utils.bili_api.clear_cache()
utils.bili_api._path_cooldown.clear()

# 等待 30 秒
print('\n等待 30 秒让风控冷却...')
time.sleep(30)

# 创建 session
print('\n创建 session...')
s = utils.bili_api._create_session()
print(f'Session 创建完成')

# 检查 session 的 cookie
cookies = s.cookies.get_dict()
print(f'Cookie 数量: {len(cookies)}')
for key in ['buvid3', 'buvid4', 'buvid_fp', '_uuid', 'SESSDATA', 'bili_jct', 'bili_ticket']:
    val = cookies.get(key, 'MISSING')
    if val != 'MISSING':
        val = val[:20] + '...'
    print(f'  {key}: {val}')

# 等待 10 秒
print('\n等待 10 秒...')
time.sleep(10)

# 生成 WBI 参数
print('\n生成 WBI 参数...')
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

# 发送请求
print('\n发送 WBI 请求...')
try:
    import json
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
        if vlist:
            print(f'First video: {vlist[0].get("title", "")[:40]}')
    else:
        print(f'❌ FAILED')
        print(f'响应: {json.dumps(data, ensure_ascii=False)[:300]}')
except Exception as e:
    print(f'❌ ERROR: {e}')
