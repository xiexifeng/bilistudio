"""检查 bili_api 模块导入时的请求"""
import sys
sys.path.insert(0, '.')
import time

print('测试开始...')
print('当前时间:', time.time())

# 导入 bili_api
print('导入 bili_api 模块...')
import utils.bili_api
print('导入完成')

# 检查是否有全局状态
print('\n检查全局状态:')
print(f'  _session_cache: {utils.bili_api._session_cache is not None}')
print(f'  _wbi_keys: {utils.bili_api._wbi_keys}')
print(f'  _bili_ticket: {utils.bili_api._bili_ticket[:30] if utils.bili_api._bili_ticket else "None"}')
print(f'  _path_cooldown: {utils.bili_api._path_cooldown}')
