"""验证正确的 UID"""
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

# 测试李永乐老师正确的 UID
mid = 9458053
print(f'=== 测试 UID {mid} (李永乐老师官方) ===')

try:
    user_info = utils.bili_api.get_user_info(mid)
    print(f'用户信息:')
    print(f'  Name: {user_info.name}')
    print(f'  Mid: {user_info.mid}')
    print(f'  Followers: {user_info.follower}')
    
    print('\n视频列表:')
    videos = utils.bili_api.get_user_videos(mid, page=1)
    print(f'  Total videos: {videos.total}')
    print(f'  Videos count: {len(videos.videos)}')
    if videos.videos:
        for i, v in enumerate(videos.videos[:3]):
            print(f'    [{i}] title: {v.title[:40]}')
            print(f'        author: {v.author}')
except Exception as e:
    print(f'Error: {e}')
