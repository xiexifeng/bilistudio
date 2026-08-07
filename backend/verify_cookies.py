"""验证 Cookie 完整性和 WBI 接口可用性"""
import sys
sys.path.insert(0, '.')

from utils.bili_api import _create_session, reset_session_cache, clear_cache, _get_user_videos_wbi
import time

# 清除缓存
reset_session_cache()
clear_cache()

print('=== 验证 Cookie 完整性 ===')
print('创建 session...')
s = _create_session()
cookies = s.cookies.get_dict()

# 检查关键 Cookie
required_cookies = [
    'buvid3', 'buvid4', 'buvid_fp', '_uuid', 'b_lsid',  # 设备指纹
    'SESSDATA', 'bili_jct', 'DedeUserID', 'sid',      # 登录态
    'bili_ticket',                                     # 新鉴权
]

print('\nCookie 检查:')
for k in required_cookies:
    status = '✅' if k in cookies else '❌ 缺失!'
    val = cookies.get(k, 'N/A')
    if len(val) > 30:
        val = val[:30] + '...'
    print(f'  {status} {k}: {val}')

# 检查是否使用了真实的设备指纹
print('\n=== 设备指纹验证 ===')
expected_buvid4 = '9BE2CE9A-8F82-8278-C03A-A923D0902FDA18545'
if cookies.get('buvid4', '').startswith(expected_buvid4):
    print('✅ buvid4 使用了真实的 Cookie（来自登录文件）')
else:
    print('❌ buvid4 可能是随机生成的！')
    print(f'   当前值: {cookies.get("buvid4", "N/A")[:50]}')

expected_buvid_fp = '6230edfabc0bd9d217de3549dc899fa5'
if cookies.get('buvid_fp') == expected_buvid_fp:
    print('✅ buvid_fp 使用了真实的 Cookie（来自登录文件）')
else:
    print('❌ buvid_fp 可能是随机生成的！')
    print(f'   当前值: {cookies.get("buvid_fp", "N/A")}')

# 等待 3 秒
print('\n等待 3 秒...')
time.sleep(3)

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
