#!/usr/bin/env python3
"""
抖音续火花 · 消息生成脚本（Open-Meteo 主源 + wttr.in 兜底）
读取天气和节日数据，为每个联系人生成续火花消息，输出到 JSON 文件。
后续由 agent 通过 browser_use 自动化发送。

配置说明：
  修改下方 CONTACTS_FILE / HOLIDAYS_FILE / OUTPUT_FILE 路径以适配你的工作区。
  owner_name 和署名可在 contacts.json 或函数参数中自定义。
"""

import json
import urllib.request
import urllib.parse
import sys
import os
from datetime import datetime

# ============================================================
# 路径配置（请根据你的工作区修改）
# ============================================================
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
CONTACTS_FILE = os.path.join(PROJECT_DIR, "data", "contacts.json")
# holidays.json 可放在任意位置，按需修改
HOLIDAYS_FILE = os.path.join(PROJECT_DIR, "data", "holidays.json")
OUTPUT_FILE = os.path.join(PROJECT_DIR, "data", "messages_today.json")

# ============================================================
# 署名配置（可自定义）
# ============================================================
DEFAULT_SIGNATURE = "<your_signature_name>"  # 消息末尾署名，使用时替换为你的署名
SIGNATURE_EMOJI = "💙"      # 署名后缀 emoji

# WMO Weather code -> 中文天气描述映射（Open-Meteo 标准）
# 参考: https://open-meteo.com/en/docs
WMO_CODE_ZH = {
    0: "晴", 1: "大部晴朗", 2: "多云", 3: "阴",
    45: "雾", 48: "雾凇",
    51: "毛毛雨", 53: "小雨", 55: "中雨",
    56: "冻毛毛雨", 57: "冻雨",
    61: "小雨", 63: "中雨", 65: "大雨",
    66: "冻雨", 67: "大冻雨",
    71: "小雪", 73: "中雪", 75: "大雪", 77: "雪粒",
    80: "阵雨", 81: "中阵雨", 82: "强阵雨",
    85: "阵雪", 86: "大阵雪",
    95: "雷阵雨", 96: "雷阵雨伴冰雹", 99: "强雷阵雨伴冰雹",
}

# 模板分类（基于 WMO code）
CODE_RAIN = {51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 80, 81, 82}
CODE_SNOW = {71, 73, 75, 77, 85, 86}
CODE_HAZE = {45, 48}
CODE_CLOUDY = {2, 3}
CODE_SUNNY = {0, 1}
CODE_THUNDER = {95, 96, 99}

# 节日 emoji 映射
FESTIVAL_EMOJI = {
    "元旦节": "🎉", "春节": "🧧", "元宵节": "🏮", "清明节": "🌿",
    "劳动节": "💪", "端午节": "🎋", "中秋节": "🌕", "国庆节": "🇨🇳",
    "七夕节": "💕", "重阳节": "🍂", "腊八节": "🥣", "除夕": "🎆",
    "全国土地日": "🌱", "世界环境日": "🌍", "国际禁毒日": "🚫",
    "世界献血日": "🩸", "父亲节": "👨", "母亲节": "💐",
    "儿童节": "🎈", "青年节": "🔥", "教师节": "📚",
    "世界人口日": "🌏", "中国航海日": "⛵",
}


def get_today_key():
    now = datetime.now()
    return now.strftime("%Y"), now.strftime("%m-%d")


def get_festival(holidays_file):
    try:
        with open(holidays_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        year, month_day = get_today_key()
        if year in data and month_day in data[year]:
            day_info = data[year][month_day]
            return day_info.get("lunar", ""), day_info.get("festivals", [])
    except Exception as e:
        print(f"[WARN] 读取节日数据失败: {e}", file=sys.stderr)
    return "", []


def http_get_json(url, timeout=10, headers=None):
    default_headers = {"User-Agent": "curl/7.68.0"}
    if headers:
        default_headers.update(headers)
    req = urllib.request.Request(url, headers=default_headers)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def geocode_city(city_name):
    """用 Open-Meteo Geocoding API 把城市名解析为经纬度"""
    try:
        encoded = urllib.parse.quote(city_name)
        url = (
            f"https://geocoding-api.open-meteo.com/v1/search?"
            f"name={encoded}&count=1&language=zh&format=json"
        )
        data = http_get_json(url, timeout=10)
        results = data.get("results", [])
        if not results:
            return None
        r = results[0]
        return {
            "lat": r["latitude"],
            "lon": r["longitude"],
            "resolved_name": r.get("name", city_name),
            "country": r.get("country", ""),
            "admin1": r.get("admin1", ""),
        }
    except Exception as e:
        print(f"[WARN] Geocoding 失败 ({city_name}): {e}", file=sys.stderr)
    return None


def get_weather_openmeteo(lat, lon):
    """Open-Meteo 主源：按经纬度查询天气"""
    try:
        url = (
            f"https://api.open-meteo.com/v1/forecast?"
            f"latitude={lat}&longitude={lon}&timezone=Asia/Shanghai&forecast_days=1"
            f"&current=temperature_2m,relative_humidity_2m,apparent_temperature,weather_code,wind_speed_10m,is_day"
            f"&daily=temperature_2m_min,temperature_2m_max,weather_code,precipitation_sum,precipitation_probability_max"
        )
        data = http_get_json(url, timeout=15)
        current = data.get("current", {})
        daily = data.get("daily", {})
        weather_code = current.get("weather_code", 0)
        weather_desc = WMO_CODE_ZH.get(weather_code, "未知")
        return {
            "source": "open-meteo",
            "code": str(weather_code),
            "desc": weather_desc,
            "temp_now": str(current.get("temperature_2m", "")),
            "feels_like": str(current.get("apparent_temperature", "")),
            "humidity": str(current.get("relative_humidity_2m", "")),
            "wind_speed": str(current.get("wind_speed_10m", "")),
            "temp_min": str(daily.get("temperature_2m_min", [""])[0]),
            "temp_max": str(daily.get("temperature_2m_max", [""])[0]),
            "precipitation_sum": str(daily.get("precipitation_sum", [""])[0]),
            "precipitation_probability_max": str(daily.get("precipitation_probability_max", [""])[0]),
        }
    except Exception as e:
        print(f"[WARN] Open-Meteo 天气获取失败 ({lat},{lon}): {e}", file=sys.stderr)
    return None


def get_weather_wttr(wttr_city):
    """wttr.in 兜底源"""
    WTTR_CODE_ZH = {
        "113": "晴", "116": "多云", "119": "阴", "122": "阴",
        "143": "薄雾", "149": "雾霾", "248": "雾", "260": "冻雾",
        "176": "零星阵雨", "263": "零星毛毛雨", "266": "毛毛雨",
        "293": "零星小雨", "296": "小雨", "299": "中雨", "302": "中雨",
        "305": "大雨", "308": "大雨",
        "179": "零星降雪", "227": "吹雪", "230": "暴风雪",
        "323": "零星小雪", "326": "小雪", "329": "中雪", "332": "中雪",
        "335": "大雪", "338": "大雪",
        "182": "零星雨夹雪", "185": "零星冻雨", "281": "冻毛毛雨",
        "284": "冻毛毛雨", "311": "冻雨", "314": "冻雨",
        "317": "雨夹雪", "320": "雨夹雪", "350": "冰雹",
        "200": "雷阵雨", "386": "雷阵雨", "389": "雷阵雨",
        "392": "雷阵雪", "395": "雷阵雪",
        "353": "阵雨伴雷", "356": "阵雨伴雷", "359": "暴雨伴雷",
        "362": "雨夹雪伴雷", "365": "雨夹雪伴雷",
        "368": "阵雪伴雷", "371": "阵雪伴雷",
        "374": "冰雹伴雷", "377": "冰雹伴雷",
    }
    try:
        url = f"https://wttr.in/{wttr_city}?format=j1"
        data = http_get_json(url, timeout=10)
        current = data.get("current_condition", [{}])[0]
        weather_code = current.get("weatherCode", "113")
        weather_desc = WTTR_CODE_ZH.get(weather_code, "")
        if not weather_desc:
            weather_desc = current.get("weatherDesc", [{}])[0].get("value", "未知")
        weather_today = data.get("weather", [{}])[0]
        return {
            "source": "wttr.in",
            "code": weather_code,
            "desc": weather_desc,
            "temp_now": current.get("temp_C", ""),
            "feels_like": current.get("FeelsLikeC", ""),
            "humidity": current.get("humidity", ""),
            "wind_speed": current.get("windspeedKmph", ""),
            "temp_min": weather_today.get("mintempC", ""),
            "temp_max": weather_today.get("maxtempC", ""),
        }
    except Exception as e:
        print(f"[WARN] wttr.in 天气获取失败 ({wttr_city}): {e}", file=sys.stderr)
    return None


def get_weather(contact):
    """获取天气：优先 Open-Meteo（按经纬度），失败则 wttr.in 兜底"""
    geo = contact.get("geo")
    wttr_city = contact.get("wttr_city", contact["city"])
    if geo and geo.get("lat") is not None and geo.get("lon") is not None:
        weather = get_weather_openmeteo(geo["lat"], geo["lon"])
        if weather:
            return weather
        print(f"[INFO] Open-Meteo 失败，尝试 wttr.in 兜底: {wttr_city}")
    weather = get_weather_wttr(wttr_city)
    if weather:
        return weather
    return None


def select_template(first_sent, weather, has_festival):
    """根据条件选择模板类型: first/F/C/D/E/G/B/A"""
    if not first_sent:
        return "first"
    code = int(weather["code"]) if weather and weather["code"] else 0
    temp_max = int(float(weather["temp_max"])) if weather and weather["temp_max"] else 0
    temp_min = int(float(weather["temp_min"])) if weather and weather["temp_min"] else 20
    if code in CODE_HAZE:
        return "F"
    if code in CODE_THUNDER:
        return "C"
    if code in CODE_RAIN:
        return "C"
    if code in CODE_SNOW:
        return "E"
    if temp_max >= 33:
        return "D"
    if temp_min <= 5:
        return "E"
    if has_festival:
        return "G"
    if code in CODE_CLOUDY:
        return "B"
    return "A"


def build_festival_line(festivals):
    if not festivals:
        return ""
    parts = []
    for f in festivals:
        emoji = FESTIVAL_EMOJI.get(f, "✨")
        parts.append(f"{f}{emoji}")
    return f"今天是{'、'.join(parts)}！"


def generate_message(contact, weather, lunar, festivals, owner_name="<主人>"):
    """生成单行消息"""
    sig = f"--{DEFAULT_SIGNATURE}{SIGNATURE_EMOJI}"
    city = contact["city"]
    first_sent = contact.get("first_sent", False)

    festival_line = build_festival_line(festivals)
    has_festival = len(festivals) > 0

    weather_desc = weather["desc"] if weather else "天气未知"
    temp_min = weather["temp_min"] if weather else "?"
    temp_max = weather["temp_max"] if weather else "?"

    template_type = select_template(first_sent, weather, has_festival)

    if template_type == "first":
        msg = (
            f"早上好呀～我是{DEFAULT_SIGNATURE}🌙 "
            f"是{owner_name}的AI助手，从今天起每天早上会帮你播报天气和节日，顺便帮{owner_name}续个火花～ "
            f"{city}今天{weather_desc}，温度{temp_min}~{temp_max}°C "
        )
        if festival_line:
            msg += f"{festival_line} "
        msg += f"祝今天也开开心心的！ {sig}"

    elif template_type == "F":
        msg = f"早安～{city}今天{weather_desc} 出门记得戴口罩哦😷 温度{temp_min}~{temp_max}°C "
        if festival_line:
            msg += f"{festival_line} "
        msg += sig

    elif template_type == "C":
        msg = f"早安～{city}今天{weather_desc}，{temp_min}~{temp_max}°C 出门记得带伞哦☂️ "
        if festival_line:
            msg += f"{festival_line} "
        msg += sig

    elif template_type == "D":
        msg = f"早安～{city}今天{weather_desc}，{temp_min}~{temp_max}°C 今天好热，记得多喝水防暑哦🥤 "
        if festival_line:
            msg += f"{festival_line} "
        msg += sig

    elif template_type == "E":
        msg = f"早安～{city}今天{weather_desc}，{temp_min}~{temp_max}°C 今天好冷，出门记得穿暖和点🧣 "
        if festival_line:
            msg += f"{festival_line} "
        msg += sig

    elif template_type == "G":
        msg = f"早安～{city}今天{weather_desc}，{temp_min}~{temp_max}°C {festival_line} {sig}"

    elif template_type == "B":
        msg = f"早安～{city}今天{weather_desc}，{temp_min}~{temp_max}°C "
        if festival_line:
            msg += f"{festival_line} "
        msg += f"虽然没有太阳，但心情可以自己亮起来呀☁️ {sig}"

    else:  # 模板A 晴天
        msg = f"早安～{city}今天{weather_desc}，{temp_min}~{temp_max}°C "
        if festival_line:
            msg += f"{festival_line} "
        msg += f"今天也要元气满满呀✨ {sig}"

    return msg, template_type


def resolve_geo_for_contacts(contacts, full_config):
    """为没有 geo 的联系人解析经纬度，并写回配置文件"""
    updated = False
    for contact in contacts:
        if contact.get("geo"):
            continue
        city = contact.get("city", "")
        print(f"🌍 Geocoding: {city} ...")
        geo = geocode_city(city)
        if geo:
            geo["source"] = "open-meteo"
            geo["updated_at"] = datetime.now().isoformat()
            contact["geo"] = geo
            updated = True
            print(f"   -> {geo['resolved_name']} ({geo['lat']:.4f}, {geo['lon']:.4f})")
        else:
            print(f"   ⚠️ {city} 解析失败，将使用 wttr_city 兜底")
    if updated:
        try:
            full_config["contacts"] = contacts
            with open(CONTACTS_FILE, "w", encoding="utf-8") as f:
                json.dump(full_config, f, ensure_ascii=False, indent=2)
            print(f"✅ 已更新 {CONTACTS_FILE} 中的 geo 缓存")
        except Exception as e:
            print(f"[WARN] 写入 contacts.json 失败: {e}", file=sys.stderr)
    return contacts


def main():
    with open(CONTACTS_FILE, "r", encoding="utf-8") as f:
        config = json.load(f)

    owner_name = config.get("owner_name", "<主人>")
    contacts = [c for c in config["contacts"] if c.get("enabled", True)]

    contacts = resolve_geo_for_contacts(contacts, config)

    lunar, festivals = get_festival(HOLIDAYS_FILE)
    year, month_day = get_today_key()
    print(f"📅 日期: {year}-{month_day} 农历: {lunar} 节日: {festivals}")

    weather_cache = {}
    results = []

    for contact in contacts:
        nickname = contact["nickname"]
        cache_key = contact.get("geo", {}).get("resolved_name", contact["city"]) if contact.get("geo") else contact["city"]

        if cache_key not in weather_cache:
            print(f"🌡️ 查询天气: {nickname} ({contact['city']})...")
            weather_cache[cache_key] = get_weather(contact)
        weather = weather_cache[cache_key]

        if weather:
            print(f"   -> 来源:{weather.get('source','?')} {weather['desc']}(code:{weather['code']})，{weather['temp_min']}~{weather['temp_max']}°C")
        else:
            print(f"   -> 天气获取失败")

        message, template_type = generate_message(
            contact, weather, lunar, festivals, owner_name
        )

        results.append({
            "id": contact["id"],
            "nickname": nickname,
            "city": contact["city"],
            "template": template_type,
            "weather": weather,
            "message": message,
        })

        print(f"📝 [{nickname}] 模板{template_type}")
        print(f"   {message[:80]}...")
        print()

    output = {
        "generated_at": datetime.now().isoformat(),
        "date": f"{year}-{month_day}",
        "lunar": lunar,
        "festivals": festivals,
        "total": len(results),
        "messages": results,
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"✅ 共生成 {len(results)} 条消息，已保存到 {OUTPUT_FILE}")
    return output


if __name__ == "__main__":
    main()
