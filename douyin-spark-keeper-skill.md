# 抖音续火花自动化 · Douyin Spark Keeper Skill

> **用途**：通过 `browser_use` 自动操作抖音网页版私信，为指定好友每日发送天气+节日播报，维持火花 streak。
> **适用 agent**：任何支持 `browser_use` 工具的 agent（OpenClaw / Hermes / CoPaw 等）
> **敏感信息**：已全部脱敏，所有真实账号/姓名/手机号已替换为占位符

---

## 📁 文件结构

```
skills/douyin-spark-keeper/
├── SKILL.md                          # 使用说明（入口文档）
├── scripts/
│   ├── generate_messages.py          # 消息生成脚本（天气+节日+模板选择）
│   └── batch_flow.json              # 一键执行 batch 流程
├── data/
│   ├── contacts.example.json         # 联系人配置模板（示例数据）
│   └── message_templates.md          # 消息模板规范
├── references/
│   └── technical_manual.md           # 核心技术手册（浏览器操作、坑点、解决方案）
└── README.md                         # 项目说明
```

---

# 📄 文件1：SKILL.md

> Use this skill when the user wants to automatically send daily private messages to Douyin (抖音) friends to maintain "fire" (火花) streaks, or when the user mentions 抖音续火花, Douyin streak, 抖音私信自动化, or similar. Also use when setting up recurring Douyin messaging tasks via cron.

## 概述

本 skill 通过 `browser_use` 直接操作抖音网页版（`https://www.douyin.com/chat`），为每位联系人发送一条个性化的天气+节日播报消息，以维持每日私信火花（🔥streak）。

**核心流程**：生成消息（Python 脚本）-> 浏览器登录检查 -> 遍历联系人逐个发送 -> 记录结果。

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

### 2. 配置节日数据

脚本依赖 `holidays.json`，格式：

```json
{
  "2026": {
    "01-01": { "lunar": "冬月十三", "festivals": ["元旦节"] },
    "02-17": { "lunar": "正月初一", "festivals": ["春节"] }
  }
}
```

可用 `lunar_python` 库预生成，或手动维护。

### 3. 修改脚本配置

编辑 `scripts/generate_messages.py`：

```python
# 路径配置
CONTACTS_FILE = "<your_workspace>/data/contacts.json"
HOLIDAYS_FILE = "<your_workspace>/data/holidays.json"
OUTPUT_FILE   = "<your_workspace>/data/messages_today.json"

# 署名配置
DEFAULT_SIGNATURE = "<your_signature_name>"  # 替换为你的署名
```

### 4. 运行 & 发送

```bash
python3 scripts/generate_messages.py   # 生成消息
# 然后按技术手册流程用 browser_use 发送
```

### 5. Cron 定时任务（可选）

```bash
copaw cron create \
  --agent-id <your_agent_id> \
  --type agent \
  --name "抖音续火花" \
  --cron "0 8 * * *" \
  --channel <your_channel> \
  --target-user <your_user_id> \
  --target-session <your_session_id> \
  --text "<执行指令模板，见下文>"
```

## Cron 执行指令模板

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
1. evaluate 执行JS查找联系人DOM（含虚拟滚动查找）
2. 找到后派发 MouseEvent+PointerEvent 点击（mousedown+mouseup+click+pointerdown+pointerup）
3. wait 2秒
4. type 消息到 [contenteditable="true"][class*="editor-kit"] （单行文本，不要换行）
5. evaluate 派发点击事件到发送按钮（svg[class*="send"]）

**重要**：
- 消息是单行格式，不要换行
- 跳过群聊（contacts.json 中 enabled=false）
- 联系人可能被虚拟滚动隐藏，找不到时务必滚动左侧列表
- 全部发送完后 stop 浏览器
- 遇到验证码，停止并记录，不要反复重试
```

## 消息模板

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

## 天气数据源

1. **Open-Meteo**（主源）：按经纬度查询，WMO weather_code 标准
2. **wttr.in**（兜底）：按英文城市名查询

自动调用 Open-Meteo Geocoding API 解析经纬度并缓存。

---

# 📄 文件2：references/technical_manual.md

## 一、浏览器会话管理

### 1.1 启动浏览器

```python
browser_use(action="start")  # headless，CDP 端口自动分配
```

- headless 模式可能触发验证码，如遇验证码改用 `headed=true`

### 1.2 登录抖音网页版

**入口 URL**：`https://www.douyin.com/`

| 登录方式 | 可行性 | 备注 |
|---|---|---|
| 短信验证码 | ❌ | 抖音风控 |
| 密码登录 | ✅ | 点击「密码登录」切换 |

**步骤**：导航 -> 点击「密码登录」-> 输入手机号+密码 -> 点击登录按钮 -> 导航到 `/chat`

**登录状态持久化**：Cookie 在 session 内有效，browser stop 后需重新登录。

### 1.3 登录状态检查（每次任务必须）

```python
browser_use(action="open", url="https://www.douyin.com/chat")
browser_use(action="wait_for", wait_time=3)
# snapshot 中有联系人列表 -> 已登录
# 跳转登录页 -> 需重新登录
```

## 二、私信发送流程

### 2.1 进入私信页面

```
URL: https://www.douyin.com/chat
```

### 2.2 联系人列表 DOM 结构

```
componentsLeftPanelwrapper
  └── conversationConversationListwrapper
       └── conversationConversationItemwrapper (每个联系人)
            ├── commonIMAvataravatarContainer (头像)
            └── conversationConversationItemrowArea2
                 ├── conversationConversationItemtitle (昵称)
                 └── ConversationItemTagNextToTitlewrapper (火花状态)
```

**查找联系人**：
```javascript
var items = document.querySelectorAll('[class*="conversationConversationItemwrapper"]');
// 遍历 items，匹配 textContent 中的昵称
```

### 2.2a 虚拟滚动陷阱（⚠️ 重要）

联系人列表采用**虚拟滚动**，只渲染视口附近约 10 个联系人。

**✅ 解决方案**：逐步滚动左侧面板触发渲染
```javascript
var panel = document.querySelector('[class*="conversationConversationListwrapper"]');
for (var step = 0; step < 20; step++) {
    panel.scrollTop = step * 200;
    await new Promise(r => setTimeout(r, 300));
    var items = document.querySelectorAll('[class*="conversationConversationItemwrapper"]');
    // 每步查找目标联系人
}
```

### 2.3 点击联系人（关键坑点）

**❌ 失败**：`element.click()`、坐标点击、单独 `MouseEvent('click')`

**✅ 成功**：Dispatch 完整事件序列
```javascript
var opts = {bubbles: true, cancelable: true, clientX: x, clientY: y, view: window};
element.dispatchEvent(new MouseEvent('mousedown', opts));
element.dispatchEvent(new MouseEvent('mouseup', opts));
element.dispatchEvent(new MouseEvent('click', opts));
element.dispatchEvent(new PointerEvent('pointerdown', opts));
element.dispatchEvent(new PointerEvent('pointerup', opts));
```

> 必须同时 dispatch `MouseEvent` 和 `PointerEvent`，缺一不可。

### 2.4 消息编辑器（Slate.js）

**识别特征**：`contenteditable="true"` + `class*="editor-kit"`

**❌ 失败**：`innerText`、`execCommand('insertText')`、直接 `InputEvent` —— 文本能显示但发送按钮不变红

**✅ 成功**：使用 `browser_use` 的 `type` 动作
```python
browser_use(action="type", 
    selector='[contenteditable="true"][class*="editor-kit"]',
    text="消息内容")
```

> `type` 底层用 Playwright 的 `keyboard.type()`，发送真实 keydown/keypress/keyup/input 事件序列，触发 React 合成事件。

### 2.5 消息格式：必须单行

Slate.js 换行不稳定（光标错位、内容覆盖）。所有消息单行发送。

### 2.6 发送消息

发送按钮是 SVG 元素：`svg[class*="publishBtn"]` 或 `svg[class*="send"]`

**✅ 方法**：dispatch 事件到 SVG 及父元素
```javascript
var opts = {bubbles: true, cancelable: true, clientX: x, clientY: y, view: window};
sendBtn.dispatchEvent(new PointerEvent('pointerdown', opts));
sendBtn.dispatchEvent(new PointerEvent('pointerup', opts));
sendBtn.dispatchEvent(new MouseEvent('click', opts));
sendBtn.parentElement.dispatchEvent(new MouseEvent('click', opts));
```

### 2.7 验证发送成功

搜索消息内容是否出现在 `TextMessageTextpureText` 中。

### 2.8 完整流程

```
0. 检查登录状态
1. navigate -> /chat
2. 对每个联系人：
   a. evaluate 查找联系人（含虚拟滚动）
   b. dispatch 事件序列点击
   c. wait 2s
   d. type 单行消息
   e. evaluate 点击发送按钮
   f. wait 2s
   g. 验证发送
3. stop 浏览器
```

## 三、踩坑记录

| # | 问题 | 原因 | 解决 |
|---|---|---|---|
| 1 | `element.click()` 不生效 | PointerEvent 监听 | Dispatch MouseEvent+PointerEvent |
| 2 | innerText 后按钮不红 | Slate.js 依赖 keyboard | 用 `type` 动作 |
| 3 | `\n` 被解释为 Enter | Playwright 映射 | 单行消息 |
| 4 | SVG 无 `.click()` | SVG DOM 限制 | 事件派发到父元素 |
| 5 | `eval` 不支持 `var` | 严格模式 | 用 IIFE 包裹 |
| 6 | 联系人"消失" | 虚拟滚动 | 逐步 scrollTop |

## 四、DOM class 速查表

| 用途 | class 片段 |
|---|---|
| 左侧面板 | `componentsLeftPanelwrapper` |
| 联系人列表 | `conversationConversationListwrapper` |
| 联系人项 | `conversationConversationItemwrapper` |
| 昵称 | `conversationConversationItemtitle` |
| 火花标签 | `ConversationItemTagNextToTitlewrapper` |
| 空白右面板 | `RightPanelEmptywrapper` |
| 编辑器 | `editor-kit` + `contenteditable="true"` |
| 发送按钮 | `messageMsgInputpublishBtn` / `e2e-send-msg-btn` |
| 消息气泡 | `TextMessageTextpureText` |

---

# 📄 文件3：data/contacts.example.json

```json
{
  "last_updated": "2026-01-01T00:00:00+08:00",
  "account": "<your_phone_number>",
  "owner_name": "<your_nickname>",
  "send_time": "08:00",
  "total_contacts": 3,
  "contacts": [
    {
      "id": 1,
      "nickname": "好友A",
      "city": "北京",
      "wttr_city": "Beijing",
      "fire_status": "正常",
      "fire_detail": "100天",
      "danger_level": "safe",
      "first_sent": true,
      "enabled": true
    },
    {
      "id": 2,
      "nickname": "好友B",
      "city": "上海",
      "wttr_city": "Shanghai",
      "fire_status": "正常",
      "fire_detail": "50天",
      "danger_level": "safe",
      "first_sent": true,
      "enabled": true
    },
    {
      "id": 3,
      "nickname": "好友C",
      "city": "成都",
      "wttr_city": "Chengdu",
      "fire_status": "正常",
      "fire_detail": "1天",
      "danger_level": "warning",
      "first_sent": false,
      "enabled": true
    }
  ]
}
```

---

# 📄 文件4：data/message_templates.md

> 格式：单行（无换行，适配 Slate.js 编辑器）
> 署名：可自定义（示例用 `--<署名>💙`）

## 首次发送（含自我介绍）

```
早上好呀～我是<署名>🌙 是<owner_name>的AI助手，从今天起每天早上会帮你播报天气和节日，顺便帮<owner_name>续个火花～ {city}今天{weather_desc}，温度{temp_min}~{temp_max}°C {festival_line}祝今天也开开心心的！ --<署名>💙
```

## 日常模板

| 模板 | 触发 | 内容 |
|---|---|---|
| A 晴 | 默认 | `{city}早安～{weather_desc}，{temp_min}~{temp_max}°C {festival_line}今天也要元气满满呀✨ --<署名>💙` |
| B 阴 | 多云/阴 | `早安～{city}今天{weather_desc}，{temp_min}~{temp_max}°C {festival_line}虽然没有太阳，但心情可以自己亮起来呀☁️ --<署名>💙` |
| C 雨 | 雨/雷 | `早安～{city}今天{weather_desc}，{temp_min}~{temp_max}°C 出门记得带伞哦☂️ {festival_line}--<署名>💙` |
| D 热 | ≥33°C | `早安～{city}今天{weather_desc}，{temp_min}~{temp_max}°C 今天好热，记得多喝水防暑哦🥤 {festival_line}--<署名>💙` |
| E 冷 | ≤5°C/雪 | `早安～{city}今天{weather_desc}，{temp_min}~{temp_max}°C 今天好冷，出门记得穿暖和点🧣 {festival_line}--<署名>💙` |
| F 雾 | 雾/霾 | `早安～{city}今天{weather_desc} 出门记得戴口罩哦😷 温度{temp_min}~{temp_max}°C {festival_line}--<署名>💙` |
| G 节日 | 有节日 | `早安～{city}今天{weather_desc}，{temp_min}~{temp_max}°C {festival_line} --<署名>💙` |

## 变量说明

| 变量 | 来源 | 示例 |
|---|---|---|
| `{city}` | contacts.json | 北京 |
| `{weather_desc}` | 天气 API + 中文映射 | 晴 |
| `{temp_min}` / `{temp_max}` | 天气 API | 14 / 27 |
| `{festival_line}` | holidays.json | 今天是元旦节🎉 |
| `{owner_name}` | contacts.json | 主人昵称 |
| `{署名}` | 脚本配置 | <你的署名> |

---

# 📄 文件5：scripts/generate_messages.py

> 完整 Python 脚本（411行），双天气源 + 自动 geocoding + 7种模板 + 节日播报
> 
> **核心功能**：
> - Open-Meteo API（主源）按经纬度查天气，wttr.in（兜底）按城市名查
> - 自动调用 Geocoding API 解析中文城市名为经纬度，缓存到 contacts.json
> - WMO weather_code 标准中文映射
> - 7种天气模板 + 首次介绍模板，按优先级自动选择
> - 节日数据从 holidays.json 读取
> - 输出 messages_today.json 供浏览器发送

**关键函数**：

| 函数 | 功能 |
|---|---|
| `geocode_city(city_name)` | Open-Meteo Geocoding API 解析城市名 |
| `get_weather_openmeteo(lat, lon)` | Open-Meteo 天气查询（主源） |
| `get_weather_wttr(wttr_city)` | wttr.in 天气查询（兜底） |
| `get_weather(contact)` | 双源降级获取天气 |
| `select_template(first_sent, weather, has_festival)` | 按优先级选择模板 |
| `generate_message(contact, weather, lunar, festivals, owner_name)` | 生成单行消息 |
| `resolve_geo_for_contacts(contacts, full_config)` | 自动解析并缓存经纬度 |
| `main()` | 主流程：读配置 -> 查天气 -> 生成消息 -> 输出 JSON |

**自定义项**：
- `DEFAULT_SIGNATURE`：消息署名（默认 `"<your_signature_name>"`，替换为你的署名）
- `SIGNATURE_EMOJI`：署名 emoji（默认 `"💙"`）
- `CONTACTS_FILE` / `HOLIDAYS_FILE` / `OUTPUT_FILE`：文件路径

**WMO weather_code 中文映射**（天气描述）：
```
0:晴  1:大部晴朗  2:多云  3:阴
45:雾  48:雾凇
51:毛毛雨  53:小雨  55:中雨
56:冻毛毛雨  57:冻雨
61:小雨  63:中雨  65:大雨  66:冻雨  67:大冻雨
71:小雪  73:中雪  75:大雪  77:雪粒
80:阵雨  81:中阵雨  82:强阵雨
85:阵雪  86:大阵雪
95:雷阵雨  96:雷阵雨伴冰雹  99:强雷阵雨伴冰雹
```

---

# 📄 文件6：scripts/batch_flow.json

> 一键执行 batch 流程定义（JSON），供支持 batch 工具的 agent 使用。

```json
{
  "name": "douyin-spark-keeper-batch",
  "description": "抖音续火花一键执行流程：生成消息 → 浏览器登录 → 逐个发送",
  "version": "1.0.0",
  "steps": [
    {
      "step": 1,
      "name": "生成消息",
      "tool": "execute_shell_command",
      "params": {
        "command": "python3 {{SKILL_DIR}}/scripts/generate_messages.py"
      }
    },
    {
      "step": 2,
      "name": "读取消息",
      "tool": "read_file",
      "params": {
        "file_path": "{{SKILL_DIR}}/data/messages_today.json"
      }
    },
    {
      "step": 3,
      "name": "启动浏览器",
      "tool": "browser_use",
      "params": { "action": "start" }
    },
    {
      "step": 4,
      "name": "检查登录",
      "tool": "browser_use",
      "params": {
        "action": "open",
        "url": "https://www.douyin.com/chat"
      },
      "on_fail": "goto_login"
    },
    {
      "step": "goto_login",
      "name": "登录抖音",
      "substeps": [
        { "tool": "browser_use", "params": { "action": "open", "url": "https://www.douyin.com/" } },
        { "tool": "browser_use", "params": { "action": "snapshot" } },
        { "description": "点击密码登录，输入手机号+密码，点击登录" }
      ]
    },
    {
      "step": 5,
      "name": "逐个发送",
      "loop": {
        "over": "messages",
        "substeps": [
          {
            "name": "查找+点击联系人",
            "tool": "browser_use",
            "params": {
              "action": "evaluate",
              "code": "虚拟滚动查找 + MouseEvent+PointerEvent 点击"
            }
          },
          { "name": "等待加载", "tool": "browser_use", "params": { "action": "wait_for", "wait_time": 2 } },
          {
            "name": "输入消息",
            "tool": "browser_use",
            "params": {
              "action": "type",
              "selector": "[contenteditable=\"true\"][class*=\"editor-kit\"]",
              "text": "{{item.message}}"
            }
          },
          {
            "name": "点击发送",
            "tool": "browser_use",
            "params": {
              "action": "evaluate",
              "code": "dispatch PointerEvent+MouseEvent 到 svg[class*=\"send\"]"
            }
          },
          { "name": "等待完成", "tool": "browser_use", "params": { "action": "wait_for", "wait_time": 2 } }
        ]
      }
    },
    {
      "step": 6,
      "name": "停止浏览器",
      "tool": "browser_use",
      "params": { "action": "stop" }
    }
  ],
  "variables": {
    "SKILL_DIR": "skills/douyin-spark-keeper 的绝对路径",
    "douyin_phone": "抖音账号手机号（从 contacts.json 的 account 字段读取）",
    "douyin_password": "抖音账号密码（需用户提供或配置在安全位置）"
  }
}
```

---

# ✅ 脱敏检查

以下敏感信息已全部替换为占位符：

| 类型 | 替换前 | 替换后 |
|---|---|---|
| 手机号 | 真实手机号 | `<your_phone_number>` |
| 昵称 | 真实联系人姓名 | `好友A/B/C` |
| 主人称呼 | 真实称呼 | `<你的昵称>` / `<owner_name>` |
| 署名 | 真实署名 | `<your_signature_name>` / `<署名>` |
| 城市 | 真实城市 | 示例城市（北京/上海/成都） |
| 火花天数 | 真实天数 | 示例天数（100/50/1） |

**分发前请确认**：以上所有占位符均可被使用者替换为自己的真实信息，无任何原始数据泄露。