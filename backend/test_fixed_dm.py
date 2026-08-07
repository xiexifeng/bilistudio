"""测试修复后的 dm_* 参数生成"""
import sys
sys.path.insert(0, '.')

import time
import json

# 彻底清理
import utils.bili_api
utils.bili_api.reset_session_cache()
utils.bili_api.clear_cache()
utils.bili_api._path_cooldown.clear()

# 等待 30 秒
print('等待 30 秒让风控冷却...')
time.sleep(30)

# 创建 session
print('\n创建 session...')
s = utils.bili_api._create_session()

# 等待 10 秒
print('等待 10 秒...')
time.sleep(10)

# 使用新的 _sign_with_dm 函数
print('\n使用新的 _sign_with_dm 函数...')
params = utils.bili_api._sign_with_dm({
    "mid": 94510621, "ps": 30, "pn": 1,
    "tid": 0, "keyword": "", "order": "pubdate",
    "index": 0,
    "special_type": "",
    "order_avoided": "true",
    "platform": "web",
    "web_location": "333.1387",
})

# 显示生成的参数
print(f'w_rid: {params["w_rid"]}')
print(f'wts: {params["wts"]}')
print(f'dm_img_str: {params["dm_img_str"][:30]}...')
print(f'dm_cover_img_str: {params["dm_cover_img_str"][:30]}...')
print(f'dm_img_inter: {params["dm_img_inter"]}')

# 发送请求
print('\n发送 WBI 请求...')
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
