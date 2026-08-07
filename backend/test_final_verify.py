"""最终验证修正后的所有 UID"""
import sys
sys.path.insert(0, '.')

import utils.bili_api
import time

# 修正后的所有 UP 主
upers = [
    {"mid": 14804670, "name": "无穷小亮的科普日常"},
    {"mid": 9458053, "name": "李永乐老师官方"},
    {"mid": 280793434, "name": "手工耿"},
    {"mid": 254463269, "name": "毕导"},
    {"mid": 431569803, "name": "数学林老师"},
    {"mid": 503133989, "name": "学而思网校教师集结号"},
    {"mid": 14229967, "name": "一数"},
    {"mid": 395877542, "name": "不刷题的吴姥姥"},
    {"mid": 5581898, "name": "飞碟说"},
    {"mid": 483162496, "name": "英语兔"},
    {"mid": 388576777, "name": "英语的平行世界"},
    {"mid": 265589608, "name": "-古人云-"},
    {"mid": 354875574, "name": "牛哥小学作文秀"},
]

print('最终验证修正后的 UID...')
print('='*60)
print(f'{"状态":<8} {"UID":<12} {"前端名称":<20} {"B站实际名称":<20}')
print('='*60)

time.sleep(3)

errors = []
for i, uper in enumerate(upers):
    if i > 0:
        time.sleep(2)
    
    try:
        user_info = utils.bili_api.get_user_info(uper["mid"])
        actual_name = user_info.name
        expected_name = uper["name"]
        
        # 检查是否匹配（包含关系即可）
        if expected_name in actual_name or actual_name in expected_name:
            status = "✅"
        else:
            status = "❌"
            errors.append({
                "mid": uper["mid"],
                "expected": expected_name,
                "actual": actual_name,
            })
        
        print(f'{status:<8} {uper["mid"]:<12} {expected_name:<20} {actual_name:<20}')
    except Exception as e:
        print(f'⚠️       {uper["mid"]:<12} {uper["name"]:<20} Error: {e}')
        errors.append({
            "mid": uper["mid"],
            "expected": uper["name"],
            "actual": str(e),
        })

print('='*60)
if errors:
    print(f'\n仍有 {len(errors)} 个错误:')
    for e in errors:
        print(f'  UID={e["mid"]}: 期望="{e["expected"]}" 实际="{e["actual"]}"')
else:
    print('\n🎉 所有 UID 都正确！')
