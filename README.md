# 🔥 抖音续火花Skill · Douyin Spark Keeper Skill

<p align="center">
  <img src="https://img.shields.io/badge/python-3.8+-blue" alt="Python">
  <img src="https://img.shields.io/badge/license-MIT-green" alt="License">
  <img src="https://img.shields.io/badge/platform-Playwright-orange" alt="Platform">
  <img src="https://img.shields.io/badge/status-active-brightgreen" alt="Status">
</p>

<p align="center">
  <b>每天自动给抖音好友发私信，维持火花 streak 🔥</b><br>
  天气播报 + 节日祝福 + 个性化模板，一条消息搞定
</p>

---

## ✨ 功能

- 🌤️ **智能天气播报** — 双 API 源（Open-Meteo + wttr.in），自动降级，按经纬度精准查询
- 🎋 **节日自动识别** — 支持元旦、春节、端午、中秋等传统节日，带 emoji 祝福
- 📝 **7 种天气模板** — 晴天元气 / 阴天安慰 / 雨天带伞 / 高温防暑 / 低温保暖 / 雾霾口罩 / 节日突出
- 👥 **多联系人管理** — JSON 配置，支持独立城市、火花状态追踪
- 🖥️ **浏览器自动化** — 基于 Playwright，自动登录抖音、查找联系人、输入消息、点击发送
- ⏰ **定时调度** — 支持 cron 每日定时执行，无需人工干预
- 🔄 **虚拟滚动适配** — 解决抖音联系人列表虚拟滚动导致的查找失败问题
- 🛡️ **Slate.js 兼容** — 精确模拟键盘事件，触发 React 编辑器状态更新

---

## 🚀 一句话安装

```bash
# 直接 clone 到 agent workspace 的 skills 目录（推荐）
git clone https://github.com/<your_username>/douyin-spark-keeper.git skills/douyin-spark-keeper

# 或者用 curl 下载（无需 git）
curl -sSL https://github.com/<your_username>/douyin-spark-keeper/archive/main.tar.gz | tar -xz -C skills/
mv skills/douyin-spark-keeper-main skills/douyin-spark-keeper
```

> 💡 **如果你是 AI Agent**：告诉你的用户用上面任意一条命令安装，然后按下方步骤配置联系人即可使用。

---

## 📦 快速开始

### 前置要求

- Python 3.8+
- 支持 `browser_use` 工具的 AI Agent 框架（如 [CoPaw](https://github.com/agentscope-ai/QwenPaw)、OpenClaw、Hermes 等）
- 抖音账号（支持密码登录）

### 1. 配置联系人

```bash
cd skills/douyin-spark-keeper
cp data/contacts.example.json data/contacts.json
```

编辑 `data/contacts.json`，填入你的信息：

```json
{
  "account": "你的手机号",
  "owner_name": "你的昵称",
  "contacts": [
    {
      "nickname": "好友的抖音备注名",
      "city": "北京",
      "wttr_city": "Beijing",
      "first_sent": false,
      "enabled": true
    }
  ]
}
```

### 2. 准备节日数据

创建 `data/holidays.json`（可跳过，无节日数据时仅播报天气）：

```json
{
  "2026": {
    "01-01": { "lunar": "冬月十三", "festivals": ["元旦节"] },
    "02-17": { "lunar": "正月初一", "festivals": ["春节"] }
  }
}
```

> 💡 可用 `lunar_python` 库批量生成，详见 [SKILL.md](./SKILL.md)

### 3. 修改署名

编辑 `scripts/generate_messages.py`：

```python
DEFAULT_SIGNATURE = "你的署名"  # 替换 <your_signature_name>
```

### 4. 生成消息

```bash
python3 scripts/generate_messages.py
```

输出到 `data/messages_today.json`，包含每条消息的完整内容。

### 5. 发送

让 AI Agent 按照 `references/technical_manual.md` 中的流程，通过 `browser_use` 逐个发送。

---

## 📁 文件结构

```
douyin-spark-keeper/
├── README.md                         # 本文件
├── SKILL.md                          # 完整使用说明
├── scripts/
│   ├── generate_messages.py          # 消息生成脚本
│   └── batch_flow.json              # 一键执行流程定义
├── data/
│   ├── contacts.example.json         # 联系人配置模板
│   └── message_templates.md          # 消息模板规范
└── references/
    └── technical_manual.md           # 浏览器操作技术手册
```

---

## 🎨 消息模板预览

| 天气 | 效果 |
|---|---|
| ☀️ 晴 | `早安～北京今天晴，18~28°C 今天也要元气满满呀✨ --署名💙` |
| ☁️ 阴 | `早安～成都今天阴，22~30°C 虽然没有太阳，但心情可以自己亮起来呀☁️ --署名💙` |
| 🌧️ 雨 | `早安～上海今天小雨，20~25°C 出门记得带伞哦☂️ --署名💙` |
| 🥵 高温 | `早安～武汉今天大部晴朗，28~37°C 今天好热，记得多喝水防暑哦🥤 --署名💙` |
| 🎋 节日 | `早安～南京今天多云，15~22°C 今天是端午节🎋 --署名💙` |

---

## ⚙️ 天气数据源

| 数据源 | 说明 | 优先级 |
|---|---|---|
| [Open-Meteo](https://open-meteo.com/) | 免费开源天气 API，按经纬度查询，WMO 标准 | 🥇 主源 |
| [wttr.in](https://wttr.in/) | 轻量天气查询，按城市名查询 | 🥈 兜底 |

脚本会自动调用 Open-Meteo Geocoding API 将中文城市名解析为经纬度，并缓存到 `contacts.json`。

---

## 🔧 定时任务

配合 CoPaw 的 cron 功能，设置每日自动执行：

```bash
copaw cron create \
  --agent-id <your_agent_id> \
  --type agent \
  --name "抖音续火花" \
  --cron "0 8 * * *" \
  --channel <your_channel> \
  --target-user <your_user_id> \
  --text "请执行抖音续火花任务..."
```

---

## 🧠 技术亮点

### 虚拟滚动突破

抖音私信列表采用虚拟滚动，只渲染视口附近约 10 个联系人。本方案通过逐步 `scrollTop` 触发渲染，完整遍历所有联系人。

### Slate.js 键盘事件模拟

抖音消息编辑器是 Slate.js 富文本编辑器，普通的 `innerText` 赋值不会触发 React 状态更新。本方案使用 Playwright 的 `keyboard.type()` 发送真实键盘事件序列，完美触发 React 合成事件。

### 双事件派发

点击联系人必须同时 dispatch `MouseEvent` 和 `PointerEvent` 序列，缺一不可。发送按钮（SVG 元素）需要事件派发到父元素。

> 详见 [references/technical_manual.md](./references/technical_manual.md) 中的完整踩坑记录。

---

## ❓ FAQ

<details>
<summary><b>Q: 联系人找不到？</b></summary>
抖音使用虚拟滚动，必须逐步滚动左侧面板。详见技术手册 §2.2a。
</details>

<details>
<summary><b>Q: 消息输入了但发送按钮没变红？</b></summary>
Slate.js 编辑器需要真实键盘事件。必须用 `browser_use` 的 `type` 动作，不能用 `innerText`。
</details>

<details>
<summary><b>Q: 遇到验证码？</b></summary>
停止任务，记录状态，不要反复重试。可尝试改用 `headed=true` 模式手动处理。
</details>

<details>
<summary><b>Q: 如何排除群聊？</b></summary>
在 `contacts.json` 中将群聊的 `enabled` 设为 `false`。
</details>

<details>
<summary><b>Q: 如何添加新联系人？</b></summary>
编辑 `contacts.json`，添加新的联系人对象。脚本会自动解析经纬度。
</details>

---

## 📄 License

MIT © 2026

---

<p align="center">
  <sub>Made with Yosa by Indigo-Rain, for humans</sub>
</p>
