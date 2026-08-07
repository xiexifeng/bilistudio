"""测试搜索和用户信息功能"""
import sys
sys.path.insert(0, '.')

import utils.bili_api

# 彻底清理
utils.bili_api.reset_session_cache()
utils.bili_api.clear_cache()
utils.bili_api._path_cooldown.clear()

import time
print('等待 10 秒让风控冷却...')
time.sleep(10)

# 测试搜索
print('\n测试 search_videos 函数...')
try:
    results = utils.bili_api.search_videos('手工耿', page=1)
    print(f'✅ SUCCESS! Total results: {results.total}')
    print(f'   Videos count: {len(results.videos)}')
    if results.videos:
        print(f'   First video: {results.videos[0].title[:40]}')
except Exception as e:
    print(f'❌ ERROR: {e}')

# 等待 5 秒
print('\n等待 5 秒...')
time.sleep(5)

# 测试用户信息
print('\n测试 get_user_info 函数...')
try:
    user_info = utils.bili_api.get_user_info(94510621)
    print(f'✅ SUCCESS!')
    print(f'   Name: {user_info.name}')
    print(f'   Level: {user_info.level}')
    print(f'   Followers: {user_info.follower}')
except Exception as e:
    print(f'❌ ERROR: {e}')

# 等待 5 秒
print('\n等待 5 秒...')
time.sleep(5)

# 测试视频详情
print('\n测试 get_video_detail 函数...')
try:
    video_detail = utils.bili_api.get_video_detail('BV1vt411c7f8')
    print(f'✅ SUCCESS!')
    print(f'   Title: {video_detail.title[:40]}')
    print(f'   Author: {video_detail.author}')
    print(f'   Duration: {video_detail.duration}s')
except Exception as e:
    print(f'❌ ERROR: {e}')
