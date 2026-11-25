# 拾刻学习 · Shike Studio

现代轻透极简风（Apple / Craft 质感）学习打卡与专注伴侣。基于 **Vue 3 + TypeScript + Vite + FastAPI + SQLite**，零重型 UI 框架，纯定制通透毛玻璃设计系统，并完全兼容原版 `study-chekin-rebuild` 的 v1 备份 JSON 导入。

## 核心亮点

- **现代轻透极简美学**：微光弥散画布 + 磨砂毛玻璃层次 + 5 套精选通透配色（晴空蓝 / 青岚翠 / 暮雾紫 / 暖砂金 / 晨樱绯）+ 浅色 / 午夜深色 / 跟随系统。
- **今日可视化时间轴 & 当日临时任务**：清晨/上午/下午/晚间优雅分组、实时「当前时段」脉冲指针、支持在今日随时增删改临时任务（且修改主计划时不丢失当日临时任务）。
- **沉浸专注剧场 & 环境白噪音**：番茄钟 / 正计时 / 倒计时 + 快捷时长预设 + Web Audio API 实时合成细雨 / 深棕噪 / 林风 / 书咖环境音 + 全屏无干扰沉浸剧场 + 悬浮灵动时钟。
- **目标倒计时里程碑 & 成就徽章**：考试/阶段倒计时卡片（可置顶至今日页）、每日专注目标进度环、10 枚动态学习成就徽章。
- **复盘手账 & 打卡分享海报**：心情与 5 分专注度评分、独立「复盘手账」历史时间线检索、基于高清 Canvas 的一键学习打卡海报生成与下载。
- **完整多账号、备份与后台**：Argon2id 密码哈希、CSRF 防护、每日 SQLite 快照、V1/V2 备份导入导出、超级管理员账号管理与批量定时站内消息。

## 目录结构

- `frontend/`：Vue 3 + TypeScript + Vite 前端源码与构建产物（`webui/`）
- `backend/`：FastAPI + SQLite 后端服务（`study/`）、测试（`tests/`）、运行数据（`data/`）与部署入口（`server.py`）

## 快速启动

需要 Node.js 20+、Python 3.11+ 和 `uv`：

```sh
# 1. 构建前端
cd frontend
npm install
npm run build

# 2. 启动后端
cd ../backend
uv sync
uv run python -m study.cli init-admin
uv run python -m study.cli serve
```

浏览器打开 `http://127.0.0.1:8765/today`。

本地演示预览可快速初始化含示例数据的本地环境：

```sh
cd backend
uv run python -m study.cli seed-demo --port 8765
```
