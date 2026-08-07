"""彻底清理后测试"""
import sys
sys.path.insert(0, '.')

# 在导入 bili_api 之前先清理
import importlib
import utils.bili_api
importlib.reload(utils.bili_api)

from utils.bili_api import _create_session, reset_session_cache, clear_cache, _path_cooldown, _get_user_videos_wbi
import time

# 彻底清理
print('=== 彻底清理 ===')
reset_session_cache()
clear_cache()
_path_cooldown.clear()

# 强制等待 60 秒让风控冷却
print('等待 60 秒让风控冷却...')
for i in range(6):
    time.sleep(10)
    print(f'  {i+1}/6...')

print('\n=== 创建 session ===')
s = _create_session()
cookies = s.cookies.get_dict()
print(f'Session 创建完成，共 {len(cookies)} 个 Cookie')

# 等待 5 秒
print('\n等待 5 秒...')
time.sleep(5)

# 测试 WBI 接口
print('\n=== 测试 WBI 接口 ===')
try:
    videos = _get_user_videos_wbi(94510621, page=1, ps=30)
    print(f'✅ SUCCESS! Total videos: {videos.total}')
    print(f'   Videos count: {len(videos.videos)}')
    if videos.videos:
        print(f'   First video: {videos.videos[0].title[:40]}')
except Exception as e:
    print(f'❌ ERROR: {e}')
