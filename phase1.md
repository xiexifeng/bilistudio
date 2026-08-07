---

## BiliStudio 项目进度总览

### 架构
**技术栈**：Vue 3 + FastAPI + SQLite | 部署：Nginx 反代 + uvicorn

### ✅ 已完成功能

| 模块 | 状态 | 说明 |
|------|:--:|------|
| B站视频搜索 | ✅ | WBI 签名 + dm_* 指纹，失败回退 legacy |
| 视频播放 | ✅ | iframe 嵌入 B站 播放器 |
| UP主信息 | ✅ | `acc/info` WBI 通过，105ms |
| UP主视频列表 | ✅ | WBI -403 → 自动回退 legacy，134ms |
| 视频详情 | ✅ | WBI 优先 + legacy 兜底 |
| 本地收藏 CRUD | ✅ | SQLite 持久化 + JSON 导入导出 |
| B站扫码登录 | ✅ | cookie 持久化到 `.bili_cookies.json` |
| B站收藏/关注/历史 | ✅ | 需登录态 |
| 迷你播放器（画中画） | ✅ | keep-alive + Teleport，切换页面不中断 |
| 预制教育UP主 | ✅ | 数学/英语/语文 共 12 位 |
| 图片代理（防盗链） | ✅ | `/bilibili/proxy/image?url=xxx` |
| 后端日志 | ✅ | 文件轮转，B站请求详情全记录 |
| 部署 | ✅ | Nginx + uvicorn，已验证可用 |

### 🔧 B站风控对抗策略（5层）

```
1. WBI 签名 + dm_* 浏览器指纹（4个无登录态接口）
2. TLS 指纹伪装（curl_cffi，Linux 生效）
3. UA 轮换池（5个，每次随机）
4. 3s间隔 + 随机抖动 + 指数退避重试(3次)
5. TTL缓存 + -799冷却标记（60s不穿透）
```

### 📋 待解决 / 已知问题

- **curl_cffi**：Windows 本地被安全策略拦截，Linux 服务器上 `pip install curl_cffi` 后生效
- **arc/search WBI**：返回 -403（权限不足），legacy fallback 稳定可用
- **频繁测试同一 UP 会导致风控**：生产环境 10 分钟缓存会大幅缓解

---

所有 B站请求涉及的域名只有两个：

---

### 域名汇总

| 域名 | 用途 | 接口数 |
|------|------|:--:|
| `https://www.bilibili.com/` | Cookie 预热（获取访客身份） | 1 |
| `https://api.bilibili.com/` | 所有 API 调用 | 10 |

---

### 完整 URL 列表

| # | 完整接口 | 用途 |
|:--:|------|------|
| 1 | `https://www.bilibili.com/` | Cookie 预热 |
| 2 | `https://api.bilibili.com/x/web-interface/nav` | WBI 签名密钥 |
| 3 | `https://api.bilibili.com/x/space/wbi/acc/info` | UP主信息（WBI） |
| 4 | `https://api.bilibili.com/x/space/acc/info` | UP主信息（legacy） |
| 5 | `https://api.bilibili.com/x/space/wbi/arc/search` | UP主视频（WBI） |
| 6 | `https://api.bilibili.com/x/space/arc/search` | UP主视频（legacy） |
| 7 | `https://api.bilibili.com/x/web-interface/wbi/search/type` | 搜索（WBI） |
| 8 | `https://api.bilibili.com/x/web-interface/search/type` | 搜索（legacy） |
| 9 | `https://api.bilibili.com/x/web-interface/wbi/view` | 视频详情（WBI） |
| 10 | `https://api.bilibili.com/x/web-interface/view` | 视频详情（legacy） |
| 11 | `https://api.bilibili.com/x/relation/followings` | 关注列表 |
| 12 | `https://api.bilibili.com/x/v3/fav/folder/created/list` | 收藏夹列表 |
| 13 | `https://api.bilibili.com/x/v3/fav/resource/list` | 收藏夹内容 |
| 14 | `https://api.bilibili.com/x/web-interface/history/cursor` | 历史记录 |

共 **14 个请求入口**，涉及 **2 个域名**，去重后 **11 个唯一 API 端点**。