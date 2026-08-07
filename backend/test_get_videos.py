"""直接测试 _get_user_videos_wbi 函数"""
import sys
sys.path.insert(0, '.')

from utils.bili_api import _create_session, reset_session_cache, clear_cache, _path_cooldown, _get_user_videos_wbi
import time

# 完全清除所有缓存和状态
reset_session_cache()
clear_cache()
_path_cooldown.clear()

print('=== 创建 session ===')
s = _create_session()
print('Session 创建完成')

# 等待 5 秒
print('\n等待 5 秒...')
time.sleep(5)

# 直接调用 _get_user_videos_wbi
print('\n=== 测试 _get_user_videos_wbi ===')
try:
    videos = _get_user_videos_wbi(94510621, page=1, ps=30)
    print(f'✅ SUCCESS! Total videos: {videos.total}')
    print(f'   Videos count: {len(videos.videos)}')
    if videos.videos:
        print(f'   First video: {videos.videos[0].title[:40]}')
except Exception as e:
    print(f'❌ ERROR: {e}')

# 等待 6 秒
print('\n等待 6 秒...')
time.sleep(6)

# 再次测试（模拟分页）
print('\n=== 测试第 2 页 ===')
try:
    videos2 = _get_user_videos_wbi(94510621, page=2, ps=30)
    print(f'✅ SUCCESS! Page 2 videos count: {len(videos2.videos)}')
    if videos2.videos:
        print(f'   First video on page 2: {videos2.videos[0].title[:40]}')
except Exception as e:
    print(f'❌ ERROR: {e}')
