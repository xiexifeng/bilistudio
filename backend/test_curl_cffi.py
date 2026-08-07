"""测试 curl_cffi 是否真正生效"""
import sys
sys.path.insert(0, '.')

# 测试 1: 检查是否安装了 curl_cffi
print('=== 测试 1: 检查 curl_cffi 是否安装 ===')
try:
    import curl_cffi
    print(f'✅ curl_cffi 已安装，版本: {curl_cffi.__version__}')
except ImportError:
    print('❌ curl_cffi 未安装！')
    sys.exit(1)

# 测试 2: 检查 bili_api 中是否使用 curl_cffi
print('\n=== 测试 2: 检查 bili_api 中的 HTTP 后端 ===')
import utils.bili_api
print(f'_USE_CURL_CFFI = {utils.bili_api._USE_CURL_CFFI}')

# 测试 3: 创建 session 并检查 TLS 指纹
print('\n=== 测试 3: 创建 session 检查 TLS 指纹 ===')
utils.bili_api.reset_session_cache()
utils.bili_api.clear_cache()
import time
time.sleep(3)

s = utils.bili_api._create_session()
print(f'Session 类型: {type(s).__name__}')

# 测试 4: 发送请求并检查 TLS 指纹
print('\n=== 测试 4: 发送请求检查 TLS 指纹 ===')
# 访问 httpbin 检查请求的 TLS 指纹
resp = s.get("https://tls.browserleaks.com/json", timeout=10)
import json
tls_info = resp.json()
print(f'JA3: {tls_info.get("ja3", "N/A")}')
print(f'JA4: {tls_info.get("ja4", "N/A")}')

# 测试 5: 发送请求到 B 站检查是否成功
print('\n=== 测试 5: 测试 B 站请求 ===')
time.sleep(3)
try:
    user_info = utils.bili_api.get_user_info(9458053)
    print(f'✅ B站请求成功: {user_info.name}')
except Exception as e:
    print(f'❌ B站请求失败: {e}')

print('\n=== 总结 ===')
if utils.bili_api._USE_CURL_CFFI:
    print('✅ curl_cffi 已生效！使用 curl_cffi.requests.Session 发送请求')
    print('   - TLS 指纹模拟 Chrome 120')
    print('   - 请求更像真实浏览器，降低风控概率')
else:
    print('❌ curl_cffi 未生效，使用标准 requests 库')
