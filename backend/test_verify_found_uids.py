"""验证找到的 UID 并搜索学而思网校"""
import sys
sys.path.insert(0, '.')

import utils.bili_api
import time

# 需要验证的 UID
to_verify = [
    {"mid": 14804670, "expected": "无穷小亮的科普日常"},
    {"mid": 9458053, "expected": "李永乐老师官方"},
    {"mid": 280793434, "expected": "手工耿"},
    {"mid": 254463269, "expected": "毕导THU (毕导)"},
    {"mid": 14229967, "expected": "一数"},
    {"mid": 395877542, "expected": "不刷题的吴姥姥"},
    {"mid": 5581898, "expected": "飞碟说"},
    {"mid": 265589608, "expected": "古人云 (-古人云-)"},
]

print('验证找到的 UID...')
print('='*60)

time.sleep(3)

for i, v in enumerate(to_verify):
    if i > 0:
        time.sleep(2)
    
    try:
        user_info = utils.bili_api.get_user_info(v["mid"])
        actual = user_info.name
        status = "✅" if actual == v["expected"] or v["expected"].startswith(actual) else "❌"
        print(f'{status} UID={v["mid"]}: 实际="{actual}" (期望: {v["expected"]})')
    except Exception as e:
        print(f'⚠️ UID={v["mid"]}: Error - {e}')

# 搜索学而思网校
print('\n搜索"学而思网校官方"...')
time.sleep(2)
try:
    results = utils.bili_api.search_videos("学而思网校官方", page=1)
    if results.videos:
        authors = {}
        for v in results.videos:
            key = f"{v.author}_{v.author_mid}"
            if key not in authors:
                authors[key] = {'mid': v.author_mid, 'name': v.author, 'count': 0}
            authors[key]['count'] += 1
        
        sorted_authors = sorted(authors.values(), key=lambda x: x['count'], reverse=True)
        for a in sorted_authors[:3]:
            print(f'  UID={a["mid"]}, 名称="{a["name"]}", 视频数={a["count"]}')
except Exception as e:
    print(f'  Error: {e}')
