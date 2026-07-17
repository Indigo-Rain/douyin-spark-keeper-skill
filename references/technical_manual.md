# 抖音续火花 · 技术参考手册

> 本手册记录了从零到成功发送抖音私信的全过程经验，包含所有踩过的坑和最终解决方案。
> 适用于任何使用 `browser_use` 操作抖音网页版私信的自动化场景。

---

## 一、浏览器会话管理

### 1.1 启动浏览器

```python
browser_use(action="start")  # headless，CDP 端口自动分配
```

- 使用 managed CDP 模式
- headless 模式可能触发验证码，如遇验证码改用 `headed=true`
- 浏览器进程会在 `action="stop"` 时销毁

### 1.2 登录抖音网页版

**入口 URL**：`https://www.douyin.com/`

**登录方式**：
| 方式 | 可行性 | 备注 |
|---|---|---|
| 短信验证码 | ❌ 未能触发 | 抖音可能有风控 |
| 密码登录 | ✅ 已验证 | 点击「密码登录」切换 |

**登录步骤**：
1. 导航到 `https://www.douyin.com/`
2. 点击「密码登录」切换登录模式
3. 输入手机号和密码
4. 点击登录按钮
5. 登录按钮定位：class `aoUKHqSw` / `.r7j70rK2`（class 名可能随版本变化，建议用 snapshot 识别）
6. 输入框可能需要点击按钮后才出现

**登录状态持久化**：
- Cookie 保存于浏览器上下文中
- 同一 session 内保持登录
- Session 关闭（browser stop）需重新登录

### 1.3 Cookie 过期与重新登录

```python
# 检测是否需要重新登录
browser_use(action="open", url="https://www.douyin.com/chat")
# 如 snapshot 中无联系人列表 -> 需重新登录
```

**经验**：
- 首次登录后 Cookie 在 session 内有效
- 浏览器 stop 后无法恢复 session
- 每次任务执行前必须检查登录状态

### 1.4 退出/刷新

```python
# 停止浏览器
browser_use(action="stop")
# 直接刷新
browser_use(action="navigate", url="https://www.douyin.com/chat")
```

---

## 二、私信发送流程

### 2.0 发送前必须：检查登录状态

**规则**：每次续火花任务执行前，必须先确认登录状态。

**检查方法**：
```python
browser_use(action="open", url="https://www.douyin.com/chat")
# 等待 3s
browser_use(action="wait_for", wait_time=3)
# 检查快照中是否有联系人列表
# 如有「搜索」输入框 + 联系人列表项 -> 已登录
# 如跳转到登录页或无联系人 -> 需重新登录
```

**登录流程**（如需要）：
1. `https://www.douyin.com/` -> 点击密码登录
2. 输入手机号 + 密码
3. 点击登录按钮（`.aoUKHqSw`）
4. 验证登录成功后导航到 `/chat`

### 2.1 进入私信页面

```
URL: https://www.douyin.com/chat
```

进入后自动显示联系人列表（左侧面板）。

### 2.2 联系人列表结构

**关键 DOM**：
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

### 2.2a 虚拟滚动陷阱（重要）

**问题**：联系人列表采用虚拟滚动，只渲染视口附近约 10 个联系人。如果目标联系人在列表较下方，`querySelectorAll` 首次只能拿到当前渲染出的项，会找不到目标。

**表现**：
- 搜索框输入昵称提示「未搜索到相关内容」
- `querySelectorAll` 遍历不到目标
- 即使滚动到页面最底部也可能只显示旧会话

**✅ 解决方案**：逐步滚动左侧联系人面板，触发虚拟列表渲染
```javascript
var panel = document.querySelector('[class*="conversationConversationListwrapper"]');
for (var step = 0; step < 20; step++) {
    panel.scrollTop = step * 200;
    await new Promise(r => setTimeout(r, 300));
    var items = document.querySelectorAll('[class*="conversationConversationItemwrapper"]');
    // 遍历 items 查找目标联系人
}
```

**建议**：发送脚本中不要假设所有联系人都出现在首屏，应先枚举+滚动查找。

### 2.3 点击联系人（关键坑点）

**❌ 失败方法**：
- `element.click()` - 不行
- 坐标点击 (`page_x`/`page_y`) - 不行
- 单独的 `MouseEvent('click')` dispatch - 不行

**✅ 成功方法**：Dispatch 完整的事件序列
```javascript
var opts = {bubbles: true, cancelable: true, clientX: x, clientY: y, view: window};
element.dispatchEvent(new MouseEvent('mousedown', opts));
element.dispatchEvent(new MouseEvent('mouseup', opts));
element.dispatchEvent(new MouseEvent('click', opts));
element.dispatchEvent(new PointerEvent('pointerdown', opts));
element.dispatchEvent(new PointerEvent('pointerup', opts));
```

**关键**：必须同时 dispatch `MouseEvent` 和 `PointerEvent`，缺一不可。

### 2.4 等待聊天加载

```python
browser_use(action="wait_for", wait_time=2)
```

验证聊天已打开：
```javascript
// 检查右侧面板不再是空的
var empty = document.querySelector('[class*="RightPanelEmptywrapper"]');
// 检查编辑器出现
var editor = document.querySelector('[contenteditable="true"][class*="editor-kit"]');
```

### 2.5 消息编辑器（核心难点）

**技术栈**：Slate.js 富文本编辑器（非普通 textarea）

**识别特征**：
```
contenteditable="true"
class="zone-container editor-kit-container messageEditorinputArea"
内部结构：<div class="ace-line" data-node="true"><span data-string="true" data-leaf="true">...</span></div>
```

**❌ 失败方法**：
- `editor.innerText = msg` - 不触发 React 状态更新
- `document.execCommand('insertText', ...)` - 不触发 React 状态更新
- 直接 dispatch `InputEvent` - 不触发 React 状态更新
- 以上方法文本能显示，但**发送按钮不会变红**（React 内部状态未更新）

**✅ 成功方法**：使用 `browser_use` 的 `type` 动作
```python
browser_use(action="type", 
    selector='[contenteditable="true"][class*="editor-kit"]',
    text="消息内容")
```

**原理**：`type` 动作底层使用 Playwright 的 `keyboard.type()`，会发送真实的 `keydown`/`keypress`/`keyup`/`input` 事件序列，完整触发 React 的合成事件系统和 Slate.js 的编辑管道。

### 2.6 消息格式（最终方案：单行）

**结论**：全部使用单行消息，不用换行。

**原因**：
- Slate.js 编辑器中 `type` + `Shift+Enter` 分段不稳定（光标错位、内容覆盖）
- `batch` action 对 Slate.js 太快，文本被吞
- 单行消息简洁且发送 100% 可靠

**单行示例**：
```
红安早安～晴，20~32°C 今天也要元气满满呀✨ --署名💙
```

### 2.7 发送消息

**发送按钮**：
```html
<svg class="messageMsgInputpublishBtn messageMsgInputpublishRedBtn e2e-send-msg-btn">
```

**❌ 失败方法**：
- `sendBtn.click()` - SVG 元素无 click 方法
- 坐标点击 `(740, 459)` - 可能坐标不准

**✅ 成功方法**：Dispatch 事件 + 坐标点击兜底
```javascript
// 先尝试事件派发
var opts = {bubbles: true, cancelable: true, clientX: x, clientY: y, view: window};
sendBtn.dispatchEvent(new PointerEvent('pointerdown', opts));
sendBtn.dispatchEvent(new PointerEvent('pointerup', opts));
sendBtn.dispatchEvent(new MouseEvent('click', opts));

// 再对父元素派发
sendBtn.parentElement.dispatchEvent(new MouseEvent('click', opts));
```

### 2.8 验证发送成功

```javascript
// 搜索消息内容是否出现在聊天区
var elements = document.querySelectorAll('*');
for (var i = 0; i < elements.length; i++) {
  if (elements[i].textContent.indexOf('消息关键词') !== -1) {
    // 找到消息气泡
    // class: TextMessageTextpureText (在聊天区)
  }
}
```

**关键标志**：
- 消息气泡在 `TextMessageTextpureText` 中 ✅
- 编辑器内容也被显示在 `ConversationItemHinttextBox` 中（这是正常现象，表示草稿/最后消息）

### 2.9 完整发送流程图

```
0. 确认登录状态（每次任务必须）
   -> navigate https://www.douyin.com/chat
   -> 检查联系人列表是否存在
   -> 未登录 -> 执行登录流程
1. navigate -> https://www.douyin.com/chat（已确认登录）
2. 对每个联系人：
   a. evaluate: 找到联系人 wrapper（含虚拟滚动查找）
   b. dispatch MouseEvent+PointerEvent 序列点击
   c. wait 2s
   d. 检查右侧面板不再空
   e. type 单行消息内容
   f. evaluate: 点击发送按钮（事件+坐标）
   g. wait 2s
   h. 验证发送成功
3. 记录发送日志
4. stop 浏览器
```

---

## 三、消息生成脚本设计

### 3.1 数据源

| 数据 | 来源 | 格式 |
|---|---|---|
| 天气 | Open-Meteo API（主）+ wttr.in（兜底） | JSON |
| 节日 | `holidays.json`（预生成） | JSON |
| 联系人 | `contacts.json`（本地配置） | JSON |

### 3.2 天气数据获取

**Open-Meteo（主源）**：
- Geocoding API：中文城市名 -> 经纬度
- Forecast API：经纬度 -> 天气数据
- 使用 WMO weather_code 标准

**wttr.in（兜底）**：
- URL：`https://wttr.in/{city}?format=j1`
- 使用自定义 weatherCode 中文映射

### 3.3 模板选择逻辑

```
first_sent==false -> 首次模板（含自我介绍）
↓
weatherCode 判断：
  雾/霾 -> 模板F（戴口罩提醒）
  雷/雨 -> 模板C（带伞提醒）
  雪    -> 模板E（保暖提醒）
↓
温度判断：
  max≥33 -> 模板D（防暑提醒）
  min≤5  -> 模板E（保暖提醒）
↓
有节日 -> 模板G（突出节日）
多云/阴 -> 模板B
晴天 -> 模板A
```

### 3.4 输出格式

脚本输出到 `messages_today.json`：
```json
{
  "generated_at": "2026-01-01T...",
  "date": "2026-01-01",
  "lunar": "冬月十三",
  "festivals": ["元旦节"],
  "total": 2,
  "messages": [
    {
      "id": 1,
      "nickname": "好友备注名",
      "city": "北京",
      "template": "A",
      "weather": { "source": "open-meteo", "code": "0", "desc": "晴", ... },
      "message": "早安～北京今天晴，..."
    }
  ]
}
```

---

## 四、踩过的坑

| # | 问题 | 原因 | 解决 |
|---|---|---|---|
| 1 | `element.click()` 不生效 | 抖音用了 PointerEvent 监听 | Dispatch MouseEvent+PointerEvent 序列 |
| 2 | `innerText` 设置后发送按钮不红 | Slate.js 编辑器依赖 keyboard 事件 | 用 `type` 动作模拟键盘输入 |
| 3 | `\n` 在 type 中被解释为 Enter | Playwright keyboard.type 映射 | 改用单行消息（最终方案） |
| 4 | SVG 元素无 `.click()` | SVG DOM 不支持 | 用坐标点击或事件派发到父元素 |
| 5 | `eval` 不支持 `var`/`const` | 代码在严格模式 eval 中执行 | 用 IIFE `(function(){...})()` 包裹 |
| 6 | `evaluate` 支持 `var` 但 `eval` 不行 | 两个 action 使用不同上下文 | 优先用 `evaluate` |
| 7 | 联系人列表项无 ref | 快照只捕获可交互元素 | 用 evaluate 查找特定 class |
| 8 | wttr.in 返回英文天气描述 | lang=zh 对 JSON 不生效 | 用 weatherCode 映射中文 |
| 9 | 单引号 JSON 序列化失败 | JavaScript 字符串拼接问题 | 统一用双引号 JSON.stringify |
| 10 | 联系人因虚拟滚动"消失" | 列表只渲染视口附近项 | 逐步滚动 scrollTop 触发渲染 |

---

## 五、DOM class 速查表

> 抖音前端 class 名使用 CSS Modules，可能随版本更新变化。以下为已知的关键 class 片段（用 `[class*="..."]` 模糊匹配）：

| 用途 | class 片段 |
|---|---|
| 左侧面板容器 | `componentsLeftPanelwrapper` |
| 联系人列表容器 | `conversationConversationListwrapper` |
| 单个联系人项 | `conversationConversationItemwrapper` |
| 联系人昵称 | `conversationConversationItemtitle` |
| 火花状态标签 | `ConversationItemTagNextToTitlewrapper` |
| 头像 | `commonIMAvataravatarContainer` |
| 空白右侧面板 | `RightPanelEmptywrapper` |
| 消息编辑器 | `editor-kit`（配合 `contenteditable="true"`） |
| 发送按钮 | `messageMsgInputpublishBtn` / `e2e-send-msg-btn` |
| 消息气泡文本 | `TextMessageTextpureText` |
| 最后消息预览 | `ConversationItemHinttextBox` |
