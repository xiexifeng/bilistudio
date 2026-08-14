# BiliStudio — 个人B站内容聚合收藏站

面向小学生家长的少儿教育版，聚合 B站教育/科普/知识类视频。支持多用户（家庭账号）、学习路线、统计面板、PWA 离线访问。扫码登录后可同步 B站个人收藏夹、关注列表和观看历史。

## 功能总览

### 内容发现
| 功能 | 说明 |
|---|---|
| 🔍 B站搜索 | 搜索 B站全站视频，**自动过滤广告/推广/营销号** |
| 🎯 分类快捷搜索 | 预习小学数学、英语启蒙、古诗作文、科学实验、编程入门等 10 个分类 |
| 🏠 精选 UP主 | 14 位教育 UP主预览（数学林老师、学而思、英语兔、无穷小亮、李永乐等） |

### 播放 & 收藏
| 功能 | 说明 |
|---|---|
| ▶️ 视频播放 | DPlayer（JS 播放器），支持弹幕，默认有声音。播放结束自动连播下一集（可开关） |
| 📚 合集 & 多P 选集 | 视频详情页右侧自动显示合集列表或多P选集，点击直接切换，**不刷新页面** |
| ⭐ 本地收藏 | 一键收藏到本地 SQLite，支持按 UP主筛选/关键词搜索/删除 |
| 📤 导出/导入 | JSON 格式备份收藏，按 bvid 自动去重 |
| 📝 学习状态 | 每个收藏可标记「待学习→学习中→已完成」循环切换，卡片上显示对应标签 |

### 多用户 & 学习管理
| 功能 | 说明 |
|---|---|
| 👨‍👩‍👧 多用户 | 一键创建用户（自动随机命名如小兔、小方），可改名、删除。切换用户后收藏/浏览/课程数据完全隔离 |
| 📊 统计面板 | 总收藏数、待学习/学习中/已完成分布、最爱 UP主排行、近30天学习天数 |
| 📖 学习路线 | 5 条预设路线（数学启蒙、英语自然拼读、科学探索、编程入门、大语文），分关卡打卡 |
| ⭐ 学习进度 | 学习路线中每个关卡可打卡标记完成，显示进度百分比和当前关卡 |

### PWA 离线支持
| 功能 | 说明 |
|---|---|
| 📲 安装到桌面 | 浏览器地址栏显示安装按钮，桌面图标打开后为独立窗口（无浏览器地址栏） |
| 🔌 离线浏览 | 断网时仍可打开 App，查看已缓存的收藏列表、学习进度、统计面板 |
| 💾 双层缓存 | Service Worker 缓存前端壳 + API 响应；localStorage 缓存收藏/用户数据，后端不可用时兜底 |

### B站账号集成
| 功能 | 说明 |
|---|---|
| 📱 扫码登录 | B站 App 扫码登录，cookie 本地持久化。session 自动检测登录态变化 |
| 👤 UP主追踪 | 查看 UP主全部视频，按发布时间排序，WBI 签名接口 + 动态指纹 + bili_ticket 鉴权 |
| 📂 B站收藏夹同步 | 登录后查看 B站收藏夹内容，可一键转存到本地 |
| 📋 关注列表 | 查看 B站关注的 UP主 |
| 📜 历史记录 | 查看 B站观看历史 |

### 防限流系统（7层防护）
| 层 | 策略 |
|---|---|
| 前端请求队列 | 同一时间只允许 1 个 B站请求在飞，间隔 ≥800ms |
| 后端全局节流 | 两次请求最小间隔 1s，_fetch_wbi_keys 也纳入节流 |
| 全局熔断器 | 遇到 -799 自动 60s 冷却，所有 B站请求暂停；搜索接口遇到 `v_voucher` 风控自动回退 legacy 接口 |
| 动态浏览器指纹 | `dm_img_str`、`dm_cover_img_str` 等参数每次请求随机生成 |
| bili_ticket JWT 鉴权 | 自动获取 B站新鉴权 token，提前 1h 刷新 |
| WBI 签名 + 接口参数修正 | 空间页使用正确的 `web_location`，Sec-CH-UA 头模拟 Chrome |
| TTL 内存缓存 | 搜索结果 60s，视频详情 60s，playurl CDN 直链 3600s（1 小时），合集数据也在 view 接口响应中一并缓存 |

## 技术栈

| 层 | 技术 | 说明 |
|---|---|---|
| 前端 | Vue 3 + Vite + 纯 CSS | SPA，Hash 路由 |
| 后端 | Python 3.10+ + FastAPI | ASGI 框架 |
| 数据库 | SQLite（默认）/ MySQL | 零配置开箱即用 |
| B站接入 | requests + B站公开 API + 扫码登录 | 全 session 代理 |

## 项目结构

```
bilistudio/
├── README.md
├── start.bat                    # Windows 一键启动（开发模式）
│
├── backend/                     # Python FastAPI
│   ├── .env                     # 环境变量（频率控制参数）
│   ├── .bili_cookies.json       # B站登录 Cookie（勿提交 Git）
│   ├── data.db                  # SQLite 数据库（勿提交 Git）
│   ├── requirements.txt         # Python 依赖
│   ├── config.py                # Pydantic Settings 配置
│   ├── database.py              # 数据库引擎（SQLite/MySQL）
│   ├── models.py                # SQLAlchemy ORM 模型
│   ├── schemas.py               # Pydantic 请求/响应模型（含 BiliCollection/BiliCollectionItem）
│   ├── main.py                  # FastAPI 入口
│   ├── routers/
│   │   ├── auth.py              # B站扫码登录
│   │   ├── bilibili.py          # B站内容接口（搜索/详情/UP主/合集/登录态内容）
│   │   ├── collection.py        # 本地收藏 CRUD（含学习状态管理）
│   │   ├── users.py             # 多用户管理（创建/列表/改名/删除/活跃标记）
│   │   ├── stats.py             # 统计面板（收藏分布/UP主排行/学习天数）
│   │   └── courses.py           # 学习路线进度（关卡打卡/查询）
│   └── utils/
│       ├── bili_api.py          # B站 API 封装（7层风控/缓存/WBI签名/动态指纹/bili_ticket/合集/playurl CDN直链/v_voucher 回退/数据清洗）
│       └── bili_auth.py         # 扫码登录管理器
│
    └── frontend/                    # Vue 3
        ├── package.json
        ├── vite.config.js           # 构建配置 + 开发代理
        ├── index.html               # PWA 配置（manifest + theme-color）
        └── src/
            ├── main.js              # Vue 入口 + Service Worker 注册
            ├── App.vue              # 根组件（顶栏/用户切换/登录/Toast）
            ├── api.js               # API 封装（请求队列/图片代理/playurl 前端 Map 缓存/localStorage 离线缓存）
            ├── curated.js           # 精选 UP主数据 & 快捷搜索分类 & 5条学习路线
            ├── router/index.js      # Hash 路由
            ├── components/
            │   └── VideoCard.vue    # 视频卡片组件（含学习状态标签）
            └── views/
                ├── Home.vue         # 首页（精选/搜索/分类）
                ├── Player.vue       # 播放页（DPlayer/合集&多P选集/侧边收藏/自动连播/playurl 前端缓存）
                ├── Collection.vue   # 收藏页（本地/B站收藏夹/学习状态切换）
                ├── User.vue         # UP主主页（信息/视频列表）
                ├── Stats.vue        # 统计面板（收藏分布/UP主排行/学习天数）
                └── Courses.vue      # 学习路线（关卡打卡/进度追踪）
        └── public/
            ├── manifest.json        # PWA 应用清单
            └── sw.js                # Service Worker（分层缓存策略）
```

## 开发环境启动

### 前置要求

- Python 3.10+
- Node.js 18+

### 1. 安装后端依赖

```bash
cd backend
pip install -r requirements.txt
```

### 2. 安装前端依赖

```bash
cd frontend
npm install
```

### 3. 启动后端（端口 8000）

```bash
cd backend
python main.py
```

### 4. 启动前端（端口 5173，新终端）

```bash
cd frontend
npm run dev
```

### 5. 打开浏览器

```
http://localhost:5173
```

或者 Windows 下直接双击 `start.bat` 一键启动两个窗口。

> 首次启动后端会自动在 `backend/` 下创建 `data.db`（SQLite 数据库）和表结构。

---

## 📦 生产构建 & 部署

### 构建前端

```bash
cd frontend
npm run build
```

构建产物在 `frontend/dist/`，是一组静态文件（HTML + JS + CSS）。

### 部署方案一：Nginx 反向代理（推荐）

前端静态文件 + 后端 API 通过 Nginx 统一入口，推荐用于生产环境。

**1. 构建前端并放到 Nginx 目录：**

```bash
cd frontend && npm run build
cp -r dist/* /var/www/bilistudio/
```

**2. 启动后端：**

```bash
cd backend
pip install -r requirements.txt
python main.py    # 监听 127.0.0.1:8000 cd backend && python -c "import uvicorn; uvicorn.run('main:app', host='0.0.0.0', port=8000, reload=False)"

```

> 如需后台运行，自己用 `nohup` / `screen` / `systemd` 套一层。

**3. Nginx 配置 (`/etc/nginx/sites-available/bilistudio`)：**

```nginx
server {
    listen 80;
    server_name your-domain.com;  # 改为你的域名

    # 前端静态文件
    root /var/www/bilistudio;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;  # SPA fallback
    }

    # API 反向代理
    location /api/ {
        proxy_pass http://127.0.0.1:8000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

启用：

```bash
sudo ln -s /etc/nginx/sites-available/bilistudio /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

### 部署方案二：FastAPI 直接服务前端（零配置）

在 `backend/main.py` 末尾添加静态文件服务，让后端同时提供前端页面和 API：

```python
# 在 main.py 的 app 定义之后添加：
from fastapi.staticfiles import StaticFiles

# 挂载前端构建产物（放在所有路由之后）
app.mount("/", StaticFiles(directory="../frontend/dist", html=True), name="frontend")
```

然后仅需启动后端即可：

```bash
cd backend
python main.py
# 访问 http://localhost:8000
```

> 注意：这种方式下 CORS 可以移除，但图片代理等需要 `allow_origins` 的逻辑要检查。

### 部署方案三：Docker（推荐标准化）

创建 `Dockerfile`：

```dockerfile
# ---- 阶段 1：构建前端 ----
FROM node:22-alpine AS frontend-build
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# ---- 阶段 2：运行后端 + 服务前端 ----
FROM python:3.12-slim
WORKDIR /app

# Python 依赖
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# 后端代码
COPY backend/ ./

# 前端构建产物
COPY --from=frontend-build /app/frontend/dist ./frontend/dist

# 挂载前端静态文件
RUN echo '\nfrom fastapi.staticfiles import StaticFiles\napp.mount("/", StaticFiles(directory="./frontend/dist", html=True), name="frontend")' >> main.py

# 运行
EXPOSE 8000
CMD ["sh", "-c", "python -c \"import uvicorn; uvicorn.run('main:app', host='0.0.0.0', port=8000, reload=False)\""]
```

```bash
docker build -t bilistudio .
docker run -d -p 8000:8000 -v $(pwd)/backend/data.db:/app/data.db bilistudio
```

### systemd 服务（按需）

### 关键注意事项

| 项目 | 说明 |
|---|---|
| **前端路由** | 使用 Hash 模式（`#/play/xxx`），无需 Nginx `try_files` 也能工作。如改为 History 模式，需要 Nginx fallback |
| **跨域配置** | 后端 `main.py` 中 CORS `allow_origins` 需包含部署后的域名。用 Nginx 或 FastAPI 直接服务前端时不需要 CORS |
| **B站 Cookie** | `.bili_cookies.json` 包含敏感登录信息，**不要提交到 Git**。已在 `.gitignore` 中忽略 |
| **数据库** | `data.db` 是持久化数据，部署时确保有读写权限且做定期备份 |
| **端口** | 开发模式前后端各自监听（5173+8000）。生产部署建议统一用 80/443 通过 Nginx 转发 |

---

## 配置项

### `.env` 文件（`backend/.env`）

```env
# B站 API 请求最小间隔（秒），触发风控时调大
BILI_MIN_INTERVAL=1.0

# 遇到 -799 风控时的自动重试次数
BILI_RETRY_COUNT=3

# 搜索接口缓存时间（秒）
BILI_SEARCH_CACHE_TTL=60
```

### 运行时调整

```bash
# 查看当前频率参数
curl http://localhost:8000/api/config/rate

# 调大请求间隔（触发风控后）
curl -X POST http://localhost:8000/api/config/rate \
  -H "Content-Type: application/json" \
  -d '{"bili_min_interval": 2.0, "bili_retry_count": 3, "bili_search_cache_ttl": 120}'
```

> 运行时修改在重启后重置为 `.env` 默认值。

---

## API 文档

### B站登录

```
GET    /auth/qrcode              获取登录二维码
GET    /auth/qrcode/status       ?qrcode_key=  轮询扫码状态
GET    /auth/status              登录状态
POST   /auth/logout              登出
```

### B站内容（无需登录）

```
GET    /bilibili/search          ?keyword=&page=        搜索视频（自动过滤广告，WBI 风控时自动回退 legacy 接口）
GET    /bilibili/video/{bvid}    视频详情（含 WBI view 数据、合集、多P）
GET    /bilibili/video/{bvid}/playurl  ?cid=&qn=      获取视频 CDN 直链（WBI 签名，后端缓存 1h + 前端 Map 缓存，切回已播视频秒播）
GET    /bilibili/video/{bvid}/collection  视频所属合集/多P选集
GET    /bilibili/user/{mid}      UP主信息
GET    /bilibili/user/{mid}/videos  ?page=&source=      UP主视频列表
```

### B站个人内容（需登录）

```
GET    /bilibili/followings      ?page=        关注列表
GET    /bilibili/favorites       ?page=        收藏夹列表
GET    /bilibili/favorites/{id}  ?page=        收藏夹内容
GET    /bilibili/history         ?page=        观看历史
```

### 图片代理

```
GET    /bilibili/proxy/image     ?url=         代理 B站图片（防盗链）
```

### 本地收藏

```
POST   /collection               { bvid, title, author, ... }  添加收藏
GET    /collection               ?user_id=&author=&keyword=&page=&page_size=  查询列表
PUT    /collection/{bvid}        ?user_id=  { status }  更新学习状态
DELETE /collection/{bvid}        ?user_id=  删除收藏
GET    /collection/authors       ?user_id=  所有 UP主（带视频数）
GET    /collection/export        导出 JSON
POST   /collection/import        { data: [...] }  导入 JSON
```

### 用户管理

```
GET    /users                    用户列表
POST   /users                    创建用户（自动随机命名+颜色）
PUT    /users/{id}               { name }  改名
DELETE /users/{id}               删除用户（含所有收藏数据）
POST   /users/{id}/active        标记用户活跃（更新时间戳）
```

### 统计

```
GET    /stats                    ?user_id=  统计面板数据
       → { total, todo, in_progress, done, top_authors, active_days }
```

### 学习路线

```
GET    /courses/progress         ?user_id=  所有路线打卡进度
PUT    /courses/check            ?user_id=  { stage_id, checked }  关卡打卡/取消

### 系统

```
GET    /health                  健康检查
GET    /api/config/rate         查看频率限制配置
POST   /api/config/rate         调整频率限制配置
```

---

## 合集 & 多P 选集实现

视频详情页右侧会自动显示合集列表或视频选集，无需额外 API 请求。

**实现原理**：B站的合集信息嵌入在视频详情（`WBI view`）接口响应的 `data.ugc_season` 字段中，一次请求即可拿到合集中所有视频（含缩略图、时长）。多P视频的 `data.pages` 数组同理。

| 类型 | 识别方式 | 实现 |
|---|---|---|
| UGC 合集 | `data.ugc_season` 存在且含 `id` | 提取 sections → episodes，生成合集列表。点击跳转路由 `/play/{bvid}` |
| 多P 视频 | `data.pages` 长度 > 1 | 伪合集（`season_id=0`），点击直接切换 `currentPage`，**不刷新页面** |

**后端**：`get_video_collection(bvid)` 在 `bili_api.py` → 路由 `GET /bilibili/video/{bvid}/collection`，view 接口响应有 60s TTL 缓存。
**前端**：`Player.vue` 中 `loadCollection()` → `api.videoCollection(bvid)` → 渲染 `collection.videos` 列表。

**同合集内切换**：检测新视频 BVID 是否在当前合集列表中，如果是则跳过合集刷新，只更新播放器。

---

## 架构

```
浏览器 ──→ Nginx(:80) ──→ frontend/dist (静态文件)
                  │
                  └── /api/* ──→ FastAPI(:8000) ──→ B站 API
                                           │
                                     SQLite (data.db)
                                  .bili_cookies.json
```

```
开发模式：
浏览器 ──→ Vite Dev Server(:5173) ──→ /api → FastAPI(:8000) ──→ B站 API
     │                                              │
     │  Service Worker  离线降级                     │
     │  ├─ shell 缓存 (HTML/JS/CSS)                 SQLite (data.db)
     │  ├─ api 缓存 (收藏/用户/统计)                  │
     │  └─ image 缓存 (封面图)                        ├─ users 表
     │                                               ├─ collection 表
     localStorage                                     └─ stage_progress 表
       └─ bilistudio_cache_*  断网兜底缓存
```

---

## 常见问题

### Q: 搜索/UP主页面提示 "-799 请求过于频繁"
A: 系统已内置 7 层防限流保护（全局熔断 60s + 动态指纹 + bili_ticket），通常几秒后自动恢复。如果频繁触发，调大 `.env` 中 `BILI_MIN_INTERVAL` 到 2~3 秒。

### Q: 视频封面图片不显示
A: 图片都走后端代理了，检查后端 8000 端口是否正常。图片代理有内存缓存（1小时），首次访问稍慢。

### Q: 播放器没声音
A: DPlayer 播放器默认不静音。如果仍然没声音，检查浏览器是否阻止了自动播放（Chrome 等浏览器对有声自动播放有限制），手动点一下播放按钮即可。

### Q: 合集列表不显示
A: 并非所有视频都有合集。只有 UP主创建的 B站官方合集（ugc_season）或多P分集视频才会显示。合集数据从视频详情接口的 `ugc_season` 字段提取，一次请求即获取完整列表。

### Q: 扫码登录后看不到收藏夹
A: 切换到"收藏"页面，点击顶部的"B站收藏夹"标签页。

### Q: 如何备份数据
A: 收藏页有"导出"按钮（JSON），同时建议定期备份 `backend/data.db` 和 `backend/.bili_cookies.json`。

### Q: 可以部署到服务器多人使用吗
A: 可以，但需注意：B站 Cookie 是全局的（一个账号登录所有人共用）。**v2.0 已支持多用户**：本地用户系统独立于 B站登录，收藏/浏览/课程数据按本地用户隔离。B站扫码登录作为"内容源"，不影响本地用户切换。

### Q: 如何创建和切换用户
A: 首次访问自动创建随机名用户（如小兔、小方）。点击顶栏"用户 ▾"下拉菜单可创建新用户、改名、删除或切换到其他用户。切换后全页刷新，所有数据跟随当前用户。

### Q: 可以离线使用吗
A: PWA 离线支持：后端在线时正常使用（SW 后台静默缓存 API 响应），后端不可用时自动从缓存读取收藏/用户/统计数据。完全断网时仍可打开 App 浏览缓存内容，搜索和视频播放需要网络。

### Q: 如何安装到桌面
A: 浏览器地址栏右侧会出现安装图标（PWA），点击即可添加到桌面。后续从桌面图标打开为独立窗口（无浏览器地址栏）。

### Q: 学习路线数据是B站提供的吗
A: 不是。5 条学习路线（数学、英语、科学、编程、语文）由项目内置的 `curated.js` 定义，关卡打卡进度存储在本地数据库，完全自主可控。

### Q: 可以改端口吗
A: 前端端口在 `vite.config.js` 的 `server.port`。后端端口在 `main.py` 的 `uvicorn.run(port=8000)` 和前端 `vite.config.js` 代理 target。同时需要更新 `main.py` 的 CORS `allow_origins`。

### Q: 为什么点合集/多P 视频不刷新页面
A: 这是设计行为。多P视频通过切换 `currentPage` 只更新播放器（同一个 BVID，不同 `p` 参数）。合集视频切换 BVID 时需要路由跳转，但如果新视频仍在当前合集中，会跳过合集列表的重新加载。目的是减少不必要的请求和页面闪烁。

---

## License

个人项目，仅供学习使用。
