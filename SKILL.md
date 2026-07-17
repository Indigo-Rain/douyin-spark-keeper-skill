# 抖音续火花自动化 · Douyin Spark Keeper

> Use this skill when the user wants to automatically send daily private messages to Douyin (抖音) friends to maintain "fire" (火花) streaks, or when the user mentions 抖音续火花, Douyin streak, 抖音私信自动化, or similar. Also use when setting up recurring Douyin messaging tasks via cron.

## 概述

本 skill 通过 `browser_use` 直接操作抖音网页版（`https://www.douyin.com/chat`），为每位联系人发送一条个性化的天气+节日播报消息，以维持每日私信火花（🔥streak）。

**核心流程**：生成消息（Python 脚本）-> 浏览器登录检查 -> 遍历联系人逐个发送 -> 记录结果。

---

## 文件结构

```
skills/douyin-spark-keeper/
├── SKILL.md                          # 本文件（使用说明）
├── scripts/
│   └── generate_messages.py          # 消息生成脚本（天气+节日+模板选择）
├── data/
│   ├── contacts.example.json         # 联系人配置模板（示例数据）
│   └── message_templates.md          # 消息模板规范
├── references/
│   └── technical_manual.md           # 核心技术手册（浏览器操作、坑点、解决方案）
└── README.md                         # 项目说明
```

> **注意**：`holidays.json`（节日数据）需要用户提供或自建。格式见下文「节日数据」章节。

---

## 快速开始

### 1. 配置联系人

复制 `data/contacts.example.json` 为 `data/contacts.json`，填入真实联系人信息：

```json
{
  "last_updated": "2026-01-01T00:00:00+08:00",
  "account": "<你的手机号>",
  "owner_name": "<你的昵称>",
  "send_time": "08:00",
  "total_contacts": 2,
  "contacts": [
    {
      "id": 1,
      "nickname": "好友备注名",
      "city": "北京",
      "wttr_city": "Beijing",
      "fire_status": "正常",
      "first_sent": false,
      "enabled": true
    }
  ]
}
```

**字段说明**：

| 字段 | 必填 | 说明 |
|---|---|---|
| `nickname` | ✅ | 抖音私信列表中显示的备注名（必须完全匹配） |
| `city` | ✅ | 联系人所在城市（中文） |
| `wttr_city` | ✅ | wttr.in 查询用的英文城市名 |
| `geo` | ❌ | 经纬度（脚本会自动解析并缓存，无需手填） |
| `first_sent` | ✅ | 是否已发过首次自我介绍消息 |
| `enabled` | ✅ | 是否启用此联系人 |
| `fire_status` | ❌ | 火花状态（仅供人工参考） |

### 2. 配置节日数据

脚本依赖一个 `holidays.json` 文件，格式如下：

```json
{
  "2026": {
    "01-01": { "lunar": "冬月十三", "festivals": ["元旦节"] },
    "02-17": { "lunar": "正月初一", "festivals": ["春节"] }
  }
}
```

可以通过 `lunar_python` 库预生成，或手动维护。路径在 `generate_messages.py` 中配置（`HOLIDAYS_FILE` 变量）。

### 3. 修改脚本路径

编辑 `scripts/generate_messages.py`，修改以下路径常量：

```python
CONTACTS_FILE = "<your_workspace>/data/contacts.json"
HOLIDAYS_FILE = "<your_workspace>/data/holidays.json"
OUTPUT_FILE   = "<your_workspace>/data/messages_today.json"
```

### 4. 运行消息生成

```bash
python3 scripts/generate_messages.py
```

输出到 `data/messages_today.json`。

### 5. 通过浏览器发送

按照 `references/technical_manual.md` 中的流程，使用 `browser_use` 逐个发送。

### 6. 设置 cron 定时任务（可选）

```bash
copaw cron create \
  --agent-id <your_agent_id> \
  --type agent \
  --name "抖音续火花" \
  --cron "0 8 * * *" \
  --channel <your_channel> \
  --target-user <your_user_id> \
  --target-session <your_session_id> \
  --text "<执行指令，见下文模板>"
```

---

## Cron 执行指令模板

将以下内容作为 `--text` 参数传给 cron 任务（需替换 `<占位符>`）：

```
请执行抖音续火花任务（每天给好友发私信维持火花）：

**第0步：确认登录状态（每次任务必须）**
用 browser_use 打开 https://www.douyin.com/chat ，等待3秒后 snapshot 检查是否有联系人列表。如果有则跳到第1步。如果没有（跳转登录页），则：
- navigate 到 https://www.douyin.com/
- 点击密码登录
- 输入手机号 <手机号> 和密码
- 登录成功后 navigate 到 https://www.douyin.com/chat

**第1步：生成消息**
运行 python3 <generate_messages.py 的绝对路径>

**第2步：读取消息**
读取 <messages_today.json 的绝对路径> 获取每条消息内容

**第3步：查找并发送**
对每个联系人：
1. evaluate 执行JS查找联系人DOM
   - 抖音联系人列表是虚拟滚动，首屏可能只渲染约10个联系人
   - 如果直接 querySelectorAll 找不到目标，需要逐步滚动左侧联系人面板：
     ```javascript
     var panel = document.querySelector("[class*=\"conversationConversationListwrapper\"]");
     for (var step = 0; step < 20; step++) {
       panel.scrollTop = step * 200;
       await new Promise(r => setTimeout(r, 300));
       // 每步都 querySelectorAll 查找目标
     }
     ```
2. 找到后派发 MouseEvent+PointerEvent 点击（mousedown+mouseup+click+pointerdown+pointerup）
3. wait 2秒
4. type 消息到 [contenteditable="true"][class*="editor-kit"] （单行文本，不要换行）
5. evaluate 派发点击事件到发送按钮（查找 svg[class*="send"] 元素）

**重要**：
- 消息是单行格式，不要换行
- 跳过群聊（在 contacts.json 中 enabled=false 即可）
- 联系人可能被虚拟滚动隐藏，找不到时务必滚动左侧列表
- 全部发送完后 stop 浏览器
- 如果过程中遇到验证码，停止并记录，不要反复重试

发送完成后总结发送结果。
```

---

## 消息模板

脚本内置 7 种天气模板 + 1 种首次介绍模板，根据天气状况和温度自动选择：

| 模板 | 触发条件 | 特色 |
|---|---|---|
| first | `first_sent=false` | 含自我介绍 |
| A | 晴天（默认） | 元气满满 |
| B | 多云/阴天 | 心情自己亮起来 |
| C | 雨/雷阵雨 | 带伞提醒 |
| D | 高温（≥33°C） | 防暑提醒 |
| E | 低温（≤5°C）/雪天 | 保暖提醒 |
| F | 雾/霾 | 戴口罩提醒 |
| G | 有节日 | 突出节日 |

**选择优先级**：首次 > 雾霾 > 雷雨 > 雨 > 雪 > 高温 > 低温 > 节日 > 多云/阴 > 晴

所有模板均为**单行格式**（无换行），适配抖音的 Slate.js 富文本编辑器。

---

## 天气数据源

双数据源，自动降级：

1. **Open-Meteo**（主源）：按经纬度查询，WMO weather_code 标准
2. **wttr.in**（兜底）：按英文城市名查询，自定义 weatherCode 映射

脚本会自动调用 Open-Meteo Geocoding API 将中文城市名解析为经纬度，并缓存到 `contacts.json` 的 `geo` 字段中。

---

## 核心技术要点（摘要）

> 完整版见 `references/technical_manual.md`

### 浏览器登录
- 入口：`https://www.douyin.com/`
- 推荐密码登录（短信验证码可能被风控）
- Cookie 在 session 内有效，浏览器 stop 后需重新登录
- **每次任务执行前必须检查登录状态**

### 联系人查找
- DOM class：`conversationConversationItemwrapper`
- **虚拟滚动陷阱**：首屏只渲染约 10 个联系人，必须逐步滚动 `[class*="conversationConversationListwrapper"]` 触发渲染
- 查找代码：`document.querySelectorAll('[class*="conversationConversationItemwrapper"]')`，遍历匹配 textContent

### 点击联系人
- ❌ `element.click()` 不生效
- ✅ 必须 dispatch 完整事件序列：`MouseEvent(mousedown)` + `MouseEvent(mouseup)` + `MouseEvent(click)` + `PointerEvent(pointerdown)` + `PointerEvent(pointerup)`

### 输入消息
- 编辑器是 **Slate.js**（`contenteditable="true"`），非普通 textarea
- ❌ `innerText`、`execCommand` 不触发 React 状态更新
- ✅ 使用 `browser_use(action="type", selector='[contenteditable="true"][class*="editor-kit"]', text="...")`
- **必须单行**，不要换行（Slate.js 换行不稳定）

### 发送消息
- 发送按钮是 SVG 元素：`svg[class*="send"]` 或 `svg[class*="publishBtn"]`
- ❌ SVG 元素无 `.click()` 方法
- ✅ dispatch 事件到 SVG 及其父元素

### 验证发送
- 搜索消息内容是否出现在 `TextMessageTextpureText` 中

---

## 配置检查清单

在开始使用前，确认以下事项：

- [ ] Python 3 运行环境可用
- [ ] `contacts.json` 已配置（昵称与抖音备注名完全匹配）
- [ ] `holidays.json` 已准备（或路径已修改）
- [ ] `generate_messages.py` 中路径已修改
- [ ] 抖音账号可密码登录
- [ ] browser_use 工具可用
- [ ] cron 工具可用（如需定时执行）
- [ ] 联系人 `first_sent` 标记已正确设置

---

## 常见问题

**Q: 联系人找不到怎么办？**
A: 抖音使用虚拟滚动，必须逐步滚动左侧面板。详见技术手册 §2.2a。

**Q: 消息输入了但发送按钮没变红？**
A: Slate.js 编辑器需要真实键盘事件。必须用 `browser_use` 的 `type` 动作，不能用 `innerText` 或 `execCommand`。

**Q: 登录状态丢了？**
A: 浏览器 stop 后 Cookie 不保留。每次任务开始前检查登录状态，必要时重新登录。

**Q: 遇到验证码？**
A: 停止任务，记录状态，不要反复重试。可尝试改用 `headed=true` 模式手动处理。

**Q: 群聊怎么排除？**
A: 在 `contacts.json` 中将群聊的 `enabled` 设为 `false`，或在 cron 指令中指定跳过。

**Q: 如何更换天气 API？**
A: 修改 `generate_messages.py` 中的 `get_weather_openmeteo()` 或 `get_weather_wttr()` 函数。只要返回的 dict 包含 `code`、`desc`、`temp_min`、`temp_max` 字段即可。

---

## 自定义指南

### 修改消息署名/称呼

编辑 `generate_messages.py` 中的 `generate_message()` 函数：
- `owner_name`：消息中提到的主人称呼
- 所有模板末尾的 `--<署名>💙` 可替换为自定义署名

### 添加新模板

1. 在 `select_template()` 中添加触发条件
2. 在 `generate_message()` 中添加对应的 `elif` 分支
3. 更新 `data/message_templates.md`

### 修改发送时间

修改 cron 表达式（`--cron "0 8 * * *"` 表示每天 8:00）。

### 添加新联系人

编辑 `contacts.json`，添加新的联系人对象。脚本会自动解析经纬度。
