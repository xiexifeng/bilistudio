# BiliStudio — 个人B站内容聚合收藏站

面向小学生家长的少儿教育版 B站内容站，聚合科普/数学/英语/语文等教育视频，支持搜索、收藏、播放、UP主追踪，扫码登录后可同步 B站个人收藏夹、关注列表和观看历史。

## 功能总览

### 内容发现
| 功能 | 说明 |
|---|---|
| 🔍 B站搜索 | 搜索 B站全站视频，**自动过滤广告/推广/营销号** |
| 🎯 分类快捷搜索 | 预习小学数学、英语启蒙、古诗作文、科学实验、编程入门等 10 个分类 |
| 🏠 精选 UP主 | 14 位教育 UP主预览（数学林老师、学而思、英语兔、无穷小亮、李永乐等） |
| 🏆 排行榜 | （待开发） |

### 播放 & 收藏
| 功能 | 说明 |
|---|---|
| ▶️ 视频播放 | iframe 嵌入 B站官方播放器，支持弹幕 |
| 📺 画中画（浮动播放器） | **离开播放页自动缩小为右下角浮动窗口**，视频不中断。可收起/展开/关闭，点击标题回到全屏 |
| ⭐ 本地收藏 | 一键收藏到本地 SQLite，支持按 UP主筛选/关键词搜索/删除 |
| 📤 导出/导入 | JSON 格式备份收藏，按 bvid 自动去重 |

### B站账号集成
| 功能 | 说明 |
|---|---|
| 📱 扫码登录 | B站 App 扫码登录，cookie 本地持久化 |
| 👤 UP主追踪 | 查看 UP主全部视频，按发布时间排序 |
| 📂 B站收藏夹同步 | 登录后查看 B站收藏夹内容，可一键转存到本地 |
| 📋 关注列表 | 查看 B站关注的 UP主 |
| 📜 历史记录 | 查看 B站观看历史 |

### 防限流系统
| 层 | 策略 |
|---|---|
| 前端请求队列 | 同一时间只允许 1 个 B站请求在飞，间隔 ≥800ms |
| 后端全局节流 | 两次请求最小间隔 1s |
| TTL 内存缓存 | 搜索结果缓存 60s，视频详情 60s，-799 风控错误也缓存（冷却标记） |
| 指数退避重试 | 遇到 -799 自动等待 2→4→8 秒重试 3 次 |
| WBI 签名备选 | UP主视频支持切到 WBI 签名接口 |
| 图片代理缓存 | 图片代理带 `Cache-Control: max-age=3600`，后端内存 LRU 缓存 |

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
│   ├── schemas.py               # Pydantic 请求/响应模型
│   ├── main.py                  # FastAPI 入口
│   ├── routers/
│   │   ├── auth.py              # B站扫码登录
│   │   ├── bilibili.py          # B站内容接口
│   │   └── collection.py        # 本地收藏 CRUD
│   └── utils/
│       ├── bili_api.py          # B站 API 封装（风控/缓存/WBI/清洗）
│       └── bili_auth.py         # 扫码登录管理器
│
└── frontend/                    # Vue 3
    ├── package.json
    ├── vite.config.js           # 构建配置 + 开发代理
    ├── index.html
    └── src/
        ├── main.js              # Vue 入口
        ├── App.vue              # 根组件（顶栏/登录/迷你播放器/Toast）
        ├── api.js               # API 封装（请求队列/图片代理）
        ├── curated.js           # 精选 UP主数据 & 快捷搜索分类
        ├── router/index.js      # Hash 路由
        ├── components/
        │   └── VideoCard.vue    # 视频卡片组件
        └── views/
            ├── Home.vue         # 首页（精选/搜索/分类）
            ├── Player.vue       # 播放页（iframe/侧边收藏/画中画）
            ├── Collection.vue   # 收藏页（本地/B站收藏夹）
            └── User.vue         # UP主主页（信息/视频/双通道）
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
GET    /bilibili/search          ?keyword=&page=        搜索视频（自动过滤广告）
GET    /bilibili/video/{bvid}    视频详情
GET    /bilibili/user/{mid}      UP主信息
GET    /bilibili/user/{mid}/videos  ?page=&source=      UP主视频列表
                                                  source=default|wbi
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
GET    /collection               ?author=&keyword=&page=&page_size=  查询列表
DELETE /collection/{bvid}        删除收藏
GET    /collection/authors       所有 UP主（带视频数）
GET    /collection/export        导出 JSON
POST   /collection/import        { data: [...] }  导入 JSON
```

### 系统

```
GET    /health                  健康检查
GET    /api/config/rate         查看频率限制配置
POST   /api/config/rate         调整频率限制配置
```

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
                                                         │
                                                   SQLite + Cookie
```

---

## 常见问题

### Q: 搜索/UP主页面提示 "-799 请求过于频繁"
A: 系统已内置自动退避重试，等几十秒再操作即可。如果频繁触发，调大 `.env` 中 `BILI_MIN_INTERVAL` 到 2~3 秒。UP主页面可切到 WBI 签名接口（右上角按钮）。

### Q: 视频封面图片不显示
A: 图片都走后端代理了，检查后端 8000 端口是否正常。图片代理有内存缓存（1小时），首次访问稍慢。

### Q: 扫码登录后看不到收藏夹
A: 切换到"收藏"页面，点击顶部的"B站收藏夹"标签页。

### Q: 迷你播放器没声音/没画面
A: 刷新页面重试。迷你播放器依赖完整 iframe DOM 不被销毁，首次使用或长时间闲置后可能需要重新进入播放页激活。

### Q: 如何备份数据
A: 收藏页有"导出"按钮（JSON），同时建议定期备份 `backend/data.db` 和 `backend/.bili_cookies.json`。

### Q: 可以部署到服务器多人使用吗
A: 可以，但需注意：B站 Cookie 是全局的（一个账号登录所有人共用），收藏数据也是共享的。如需多用户隔离需要改造认证和数据库层。

### Q: 可以改端口吗
A: 前端端口在 `vite.config.js` 的 `server.port`。后端端口在 `main.py` 的 `uvicorn.run(port=8000)` 和前端 `vite.config.js` 代理 target。同时需要更新 `main.py` 的 CORS `allow_origins`。

---

## License

个人项目，仅供学习使用。
