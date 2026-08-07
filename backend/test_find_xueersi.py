"""搜索学而思网校正确 UID"""
import sys
sys.path.insert(0, '.')

import utils.bili_api
import time

# 搜索更多关键词
searches = [
    "学而思",
    "学而思网校 官方账号",
    "学而思网校 品牌",
]

print('搜索学而思网校正确 UID...')
time.sleep(3)

for search in searches:
    print(f'\n搜索 "{search}"...')
    try:
        results = utils.bili_api.search_videos(search, page=1)
        if results.videos:
            authors = {}
            for v in results.videos:
                if '学而思' in v.author:
                    key = f"{v.author}_{v.author_mid}"
                    if key not in authors:
                        authors[key] = {'mid': v.author_mid, 'name': v.author, 'count': 0}
                    authors[key]['count'] += 1
            
            sorted_authors = sorted(authors.values(), key=lambda x: x['count'], reverse=True)
            for a in sorted_authors[:5]:
                print(f'  UID={a["mid"]}, 名称="{a["name"]}", 视频数={a["count"]}')
    except Exception as e:
        print(f'  Error: {e}')
    
    time.sleep(2)

# 测试几个可能的学而思官方 UID
print('\n测试可能的学而思官方 UID...')
candidates = [
    503133989,  # 学而思网校教师集结号
    39296715,   # 学而思网校高中官方号
]

for mid in candidates:
    time.sleep(2)
    try:
        user_info = utils.bili_api.get_user_info(mid)
        print(f'UID={mid}: 名称="{user_info.name}", 粉丝={user_info.follower}')
    except Exception as e:
        print(f'UID={mid}: Error - {e}')
