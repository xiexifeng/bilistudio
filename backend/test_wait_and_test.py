"""等待风控冷却后测试 bili_api"""
import sys
sys.path.insert(0, '.')

import utils.bili_api
from utils.bili_api import _create_session, reset_session_cache, clear_cache, _path_cooldown, _sign_wbi, _gen_dm_img_inter, _get_user_videos_wbi
import time
import json

# 彻底清理
print('=== 彻底清理 ===')
reset_session_cache()
clear_cache()
_path_cooldown.clear()

# 等待 60 秒让风控冷却
print('等待 60 秒让风控冷却...')
for i in range(6):
    time.sleep(10)
    print(f'  {i+1}/6...')

# 创建 session
print('\n=== 创建 session ===')
s = _create_session()
cookies = s.cookies.get_dict()
print(f'Session 创建完成，共 {len(cookies)} 个 Cookie')

# 等待 10 秒
print('等待 10 秒...')
time.sleep(10)

# 检查状态
print('\n=== 检查状态 ===')
print(f'_wbi_keys: {utils.bili_api._wbi_keys}')
print(f'_bili_ticket: {utils.bili_api._bili_ticket[:30] if utils.bili_api._bili_ticket else "None"}')

# 等待 30 秒
print('等待 30 秒...')
time.sleep(30)

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
