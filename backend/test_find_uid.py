"""查找李永乐老师的真实 UID"""
import sys
sys.path.insert(0, '.')

import utils.bili_api
import time

# 清理缓存
utils.bili_api.reset_session_cache()
utils.bili_api.clear_cache()
utils.bili_api._path_cooldown.clear()

print('等待 5 秒...')
time.sleep(5)

# 搜索"李永乐老师"
print('搜索"李永乐老师"...')
try:
    results = utils.bili_api.search_videos('李永乐老师', page=1)
    print(f'Total results: {results.total}')
    if results.videos:
        # 统计不同的作者
        authors = {}
        for v in results.videos:
            if v.author not in authors:
                authors[v.author] = {'mid': v.author_mid, 'count': 0}
            authors[v.author]['count'] += 1
        
        print('\n作者列表:')
        for author, info in authors.items():
            print(f'  {author}: UID={info["mid"]}, 视频数={info["count"]}')
            
        # 显示前几个视频
        print('\n前几个视频:')
        for i, v in enumerate(results.videos[:5]):
            print(f'  [{i}] author={v.author}, mid={v.author_mid}, title={v.title[:40]}')
except Exception as e:
    print(f'Error: {e}')
