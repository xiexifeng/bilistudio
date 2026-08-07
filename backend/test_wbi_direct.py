"""直接测试 WBI 接口（不经过 bili_api 的熔断逻辑）"""
import sys
sys.path.insert(0, '.')

from utils.bili_api import _create_session, reset_session_cache, clear_cache, _path_cooldown
import time

# 完全清除所有缓存和状态
reset_session_cache()
clear_cache()
_path_cooldown.clear()

print('=== 创建 session ===')
s = _create_session()
cookies = s.cookies.get_dict()
print(f'Session 创建完成，共 {len(cookies)} 个 Cookie')

# 检查关键 Cookie
print('\n关键 Cookie:')
for k in ['buvid4', 'buvid_fp', '_uuid', 'b_lsid', 'SESSDATA', 'bili_ticket']:
    if k in cookies:
        val = cookies[k][:20] + '...' if len(cookies[k]) > 20 else cookies[k]
        print(f'  ✅ {k}: {val}')
    else:
        print(f'  ❌ {k} 缺失!')

# 等待 5 秒
print('\n等待 5 秒...')
time.sleep(5)

# 直接测试 WBI 接口
print('\n=== 直接测试 WBI 接口 ===')
import hashlib
import json
import urllib.parse

# 获取 WBI 密钥
print('获取 WBI 密钥...')
resp = s.get("https://api.bilibili.com/x/web-interface/nav", timeout=10)
nav_data = resp.json()
print(f'Nav code: {nav_data.get("code")}')

if nav_data.get('code') == 0:
    wbi_img = nav_data['data']['wbi_img']
    img_key = wbi_img["img_url"].rsplit("/", 1)[-1].split(".")[0]
    sub_key = wbi_img["sub_url"].rsplit("/", 1)[-1].split(".")[0]
    print(f'img_key: {img_key[:10]}...')
    print(f'sub_key: {sub_key[:10]}...')
    
    MIXIN_KEY_ENC_TAB = [
        46, 47, 18, 2, 53, 8, 23, 32, 15, 50, 10, 31, 58, 3, 45, 35,
        27, 43, 5, 49, 33, 9, 42, 19, 29, 28, 14, 39, 12, 38, 41, 13,
        37, 48, 7, 16, 24, 55, 40, 61, 26, 17, 0, 1, 60, 51, 30, 4,
        22, 25, 54, 21, 56, 59, 6, 63, 57, 62, 11, 36, 20, 34, 44, 52,
    ]
    raw = img_key + sub_key
    mixin_key = "".join(raw[i] for i in MIXIN_KEY_ENC_TAB if i < len(raw))[:32]
    print(f'mixin_key: {mixin_key}')
    
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
    
    print(f'w_rid: {w_rid}')
    print(f'wts: {params["wts"]}')
    
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
            print(f'   First video: {vlist[0].get("title", "N/A")[:50]}')
            print(f'   Total count: {data.get("data", {}).get("page", {}).get("count", 0)}')
    else:
        print(f'❌ FAILED')
        print(f'   Full response: {json.dumps(data, ensure_ascii=False)[:300]}')
        
        # 尝试检查响应头
        print(f'\n   Response headers:')
        for k, v in resp.headers.items():
            if k.lower() in ['server', 'set-cookie', 'x-']:
                print(f'     {k}: {str(v)[:100]}')
else:
    print(f'Nav failed: {json.dumps(nav_data, ensure_ascii=False)[:300]}')
