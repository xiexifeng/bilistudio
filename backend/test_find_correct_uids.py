"""搜索正确的 UID"""
import sys
sys.path.insert(0, '.')

import utils.bili_api
import time

# 需要查找正确 UID 的 UP 主
search_names = [
    "无穷小亮的科普日常",
    "李永乐老师",
    "手工耿",
    "毕导THU",
    "学而思网校",
    "一数",
    "不刷题的吴姥姥",
    "飞碟说",
    "古人云",
]

print('等待 3 秒...')
time.sleep(3)

for name in search_names:
    print(f'\n搜索 "{name}"...')
    try:
        results = utils.bili_api.search_videos(name, page=1)
        if results.videos:
            # 统计不同的作者
            authors = {}
            for v in results.videos:
                key = f"{v.author}_{v.author_mid}"
                if key not in authors:
                    authors[key] = {'mid': v.author_mid, 'name': v.author, 'count': 0}
                authors[key]['count'] += 1
            
            # 按视频数排序
            sorted_authors = sorted(authors.values(), key=lambda x: x['count'], reverse=True)
            
            print(f'  找到 {len(sorted_authors)} 个作者:')
            for a in sorted_authors[:5]:
                print(f'    UID={a["mid"]}, 名称="{a["name"]}", 视频数={a["count"]}')
    except Exception as e:
        print(f'  Error: {e}')
    
    time.sleep(2)
