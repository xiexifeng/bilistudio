"""测试不同 UID 的视频获取"""
import sys
sys.path.insert(0, '.')

import utils.bili_api

# 清理缓存
utils.bili_api.reset_session_cache()
utils.bili_api.clear_cache()
utils.bili_api._path_cooldown.clear()

import time

# 测试李永乐老师
mid1 = 94510621
print(f'=== 测试 UID {mid1} (李永乐老师) ===')
time.sleep(5)

try:
    videos = utils.bili_api.get_user_videos(mid1, page=1)
    print(f'✅ SUCCESS! Total videos: {videos.total}')
    print(f'   Videos count: {len(videos.videos)}')
    if videos.videos:
        for i, v in enumerate(videos.videos[:3]):
            print(f'   [{i}] title: {v.title[:40]}')
            print(f'       author: {v.author}')
            print(f'       author_mid: {v.author_mid}')
            print(f'       play_count: {v.play_count}')
except Exception as e:
    print(f'❌ ERROR: {e}')

# 等待 5 秒
time.sleep(5)

# 测试另一个 UP 主
mid2 = 316568752  # 梗指南
print(f'\n=== 测试 UID {mid2} (梗指南) ===')

try:
    videos2 = utils.bili_api.get_user_videos(mid2, page=1)
    print(f'✅ SUCCESS! Total videos: {videos2.total}')
    print(f'   Videos count: {len(videos2.videos)}')
    if videos2.videos:
        for i, v in enumerate(videos2.videos[:3]):
            print(f'   [{i}] title: {v.title[:40]}')
            print(f'       author: {v.author}')
            print(f'       author_mid: {v.author_mid}')
except Exception as e:
    print(f'❌ ERROR: {e}')
