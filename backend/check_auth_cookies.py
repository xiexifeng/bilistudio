"""检查 bili_auth.get_cookies() 返回的 Cookie"""
import sys
sys.path.insert(0, '.')

from utils import bili_auth

print('=== bili_auth.get_cookies() 返回的 Cookie ===')
cookies = bili_auth.get_cookies()
print(f'共 {len(cookies)} 个 Cookie')
for k, v in cookies.items():
    val = v[:30] + '...' if len(v) > 30 else v
    print(f'  {k}: {val}')

# 检查关键 Cookie
print('\n=== 关键 Cookie 检查 ===')
required = ['buvid4', 'buvid_fp', '_uuid', 'b_lsid', 'SESSDATA', 'bili_jct', 'DedeUserID', 'sid']
for k in required:
    if k in cookies:
        print(f'  ✅ {k}')
    else:
        print(f'  ❌ {k} 缺失!')
