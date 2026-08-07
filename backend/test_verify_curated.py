"""验证 curated.js 中所有 UP 主的 UID 是否正确"""
import sys
sys.path.insert(0, '.')

import utils.bili_api
import time
import json

# 清理缓存
utils.bili_api.reset_session_cache()
utils.bili_api.clear_cache()
utils.bili_api._path_cooldown.clear()

# curated.js 中的所有 UP 主
upers = [
    {"mid": 316568752, "name": "无穷小亮的科普日常"},
    {"mid": 94510621, "name": "李永乐老师"},
    {"mid": 71712064, "name": "手工耿"},
    {"mid": 254463269, "name": "毕导THU"},
    {"mid": 431569803, "name": "数学林老师"},
    {"mid": 503133989, "name": "学而思网校"},
    {"mid": 81945446, "name": "一数"},
    {"mid": 163637592, "name": "不刷题的吴姥姥"},
    {"mid": 946974, "name": "飞碟说"},
    {"mid": 483162496, "name": "英语兔"},
    {"mid": 388576777, "name": "英语的平行世界"},
    {"mid": 265589608, "name": "古人云"},
    {"mid": 354875574, "name": "牛哥小学作文秀"},
]

print('等待 3 秒...')
time.sleep(3)

results = []
for i, uper in enumerate(upers):
    mid = uper["mid"]
    expected_name = uper["name"]
    
    # 每次请求间隔 2 秒
    if i > 0:
        time.sleep(2)
    
    try:
        user_info = utils.bili_api.get_user_info(mid)
        actual_name = user_info.name
        
        if actual_name == expected_name:
            status = "✅ 正确"
        else:
            status = f"❌ 错误 (实际: {actual_name})"
        
        results.append({
            "mid": mid,
            "expected": expected_name,
            "actual": actual_name,
            "status": status,
            "follower": user_info.follower,
        })
        print(f'{status} UID={mid}: 期望="{expected_name}" 实际="{actual_name}"')
    except Exception as e:
        results.append({
            "mid": mid,
            "expected": expected_name,
            "actual": str(e),
            "status": f"⚠️ 失败: {e}",
        })
        print(f'⚠️ 失败 UID={mid}: {e}')

print('\n' + '='*60)
print('检查结果汇总:')
print('='*60)
errors = [r for r in results if '❌' in r['status']]
if errors:
    print(f'\n发现 {len(errors)} 个错误 UID:')
    for r in errors:
        print(f'  UID={r["mid"]}: 期望="{r["expected"]}" 实际="{r["actual"]}"')
else:
    print('\n所有 UID 都正确！')
