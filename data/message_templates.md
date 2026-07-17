# 抖音续火花 · 消息模板规范

> 发送时间：每天 08:00（可自定义）
> 格式：单行（无换行，适配 Slate.js 编辑器）
> 署名：可自定义（示例中使用 `--<署名>💙`）

---

## 一、首次发送模板（含自我介绍）

```
早上好呀～我是<署名>🌙 是<owner_name>的AI助手，从今天起每天早上会帮你播报天气和节日，顺便帮<owner_name>续个火花～ {city}今天{weather_desc}，温度{temp_min}~{temp_max}°C {festival_line}祝今天也开开心心的！ --<署名>💙
```

## 二、日常发送模板（单行）

### 模板 A · 晴朗
```
{city}早安～{weather_desc}，{temp_min}~{temp_max}°C {festival_line}今天也要元气满满呀✨ --<署名>💙
```

### 模板 B · 阴天/多云
```
早安～{city}今天{weather_desc}，{temp_min}~{temp_max}°C {festival_line}虽然没有太阳，但心情可以自己亮起来呀☁️ --<署名>💙
```

### 模板 C · 雨天
```
早安～{city}今天{weather_desc}，{temp_min}~{temp_max}°C 出门记得带伞哦☂️ {festival_line}--<署名>💙
```

### 模板 D · 高温（≥33°C）
```
早安～{city}今天{weather_desc}，{temp_min}~{temp_max}°C 今天好热，记得多喝水防暑哦🥤 {festival_line}--<署名>💙
```

### 模板 E · 低温（≤5°C）/雪天
```
早安～{city}今天{weather_desc}，{temp_min}~{temp_max}°C 今天好冷，出门记得穿暖和点🧣 {festival_line}--<署名>💙
```

### 模板 F · 雾/霾
```
早安～{city}今天{weather_desc} 出门记得戴口罩哦😷 温度{temp_min}~{temp_max}°C {festival_line}--<署名>💙
```

### 模板 G · 有节日
```
早安～{city}今天{weather_desc}，{temp_min}~{temp_max}°C {festival_line} --<署名>💙
```

---

## 三、变量说明

| 变量 | 来源 | 示例 |
|---|---|---|
| `{city}` | contacts.json | 北京 |
| `{weather_desc}` | 天气 API + 中文映射 | 晴 |
| `{temp_min}` | 天气 API | 14 |
| `{temp_max}` | 天气 API | 27 |
| `{festival_line}` | holidays.json（有节日时） | 今天是元旦节🎉 |
| `{owner_name}` | contacts.json | 主人昵称 |
| `{署名}` | 脚本中配置 | <你的署名> |

## 四、模板选择逻辑

```
weatherCode=雾/霾类   -> 模板F
weatherCode=雨/雷类   -> 模板C
weatherCode=雪类      -> 模板E
max≥33                -> 模板D
min≤5                 -> 模板E
有节日                -> 模板G
weatherCode=多云/阴   -> 模板B
其他                  -> 模板A（晴天）
```

**优先级**：首次 > 雾霾 > 雷雨 > 雨 > 雪 > 高温 > 低温 > 节日 > 多云/阴 > 晴
