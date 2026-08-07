"""测试完整的 _get_user_videos_wbi 函数"""
import sys
sys.path.insert(0, '.')

import utils.bili_api

# 彻底清理
utils.bili_api.reset_session_cache()
utils.bili_api.clear_cache()
utils.bili_api._path_cooldown.clear()

import time
print('等待 30 秒让风控冷却...')
time.sleep(30)

print('\n测试 _get_user_videos_wbi 函数...')
try:
    videos = utils.bili_api._get_user_videos_wbi(94510621, page=1, ps=30)
    print(f'✅ SUCCESS! Total videos: {videos.total}')
    print(f'   Videos count: {len(videos.videos)}')
    if videos.videos:
        print(f'   First video: {videos.videos[0].title[:40]}')
        print(f'   Play count: {videos.videos[0].play_count}')
        print(f'   Author: {videos.videos[0].author}')
except Exception as e:
    print(f'❌ ERROR: {e}')

# 测试另一个 UID
print('\n测试另一个 UID...')
try:
    videos2 = utils.bili_api._get_user_videos_wbi(316568752, page=1, ps=30)
    print(f'✅ SUCCESS! Total videos: {videos2.total}')
    print(f'   Videos count: {len(videos2.videos)}')
    if videos2.videos:
        print(f'   First video: {videos2.videos[0].title[:40]}')
except Exception as e:
    print(f'❌ ERROR: {e}')
