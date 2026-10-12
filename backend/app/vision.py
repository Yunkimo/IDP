"""课表图片视觉识别：httpx 调用 OpenAI 兼容 vision API（如硅基流动 Qwen2.5-VL）。"""

import base64
import json
import re

import httpx
from pydantic import ValidationError

from . import config
from .schemas import CourseIn

# 图片大小上限（小程序端已压缩，正常远小于此）
MAX_IMAGE_BYTES = 10 * 1024 * 1024

# 视觉模型推理较慢，放宽超时
_VISION_TIMEOUT = httpx.Timeout(90.0, connect=10.0)


class VisionNotConfigured(Exception):
    """未配置 LLM_API_KEY / LLM_BASE_URL / LLM_VISION_MODEL（对外 503）。"""


class VisionError(Exception):
    """视觉模型调用或输出解析失败（对外 502）。"""


class VisionTimeout(VisionError):
    """视觉模型响应超时（对外 504）。"""


VISION_SYSTEM_PROMPT = """你是课表识别助手。分析用户上传的课表图片，提取其中所有课程。
严格只输出一个 JSON 数组，不要输出任何其它文字、解释或 Markdown 代码块。
数组每项是一个对象，字段要求：
- name: 课程名称（字符串）
- day_of_week: 上课星期（整数 1-7，1=周一，2=周二，…，7=周日）
- start_time: 开始时间（字符串 "HH:MM"，24 小时制，如 "08:00"）
- end_time: 结束时间（字符串 "HH:MM"，24 小时制）
- location: 上课地点（字符串；图片中没有地点时用空字符串 ""）
- weeks: 上课周次（整数数组，如 [1,2,3]；图片未标注周次时省略该字段）
看不清或无法确定的行直接跳过，不要臆造。输出示例：
[{"name":"高等数学","day_of_week":1,"start_time":"08:00","end_time":"09:40","location":"A101","weeks":[1,2,3]}]"""

_FENCE_RE = re.compile(r"```(?:json)?\s*(.*?)```", re.DOTALL)


def is_configured() -> bool:
    return bool(config.LLM_API_KEY and config.LLM_BASE_URL and config.LLM_VISION_MODEL)


def to_data_url(image_bytes: bytes, mime: str) -> str:
    """图片字节转 base64 data URL（vision API 的 image_url 格式）。"""
    return f"data:{mime};base64,{base64.b64encode(image_bytes).decode('ascii')}"


def build_messages(image_bytes: bytes, mime: str) -> list[dict]:
    """构造 OpenAI 兼容 vision 消息（system + user 图文）。"""
    return [
        {"role": "system", "content": VISION_SYSTEM_PROMPT},
        {
            "role": "user",
            "content": [
                {"type": "image_url", "image_url": {"url": to_data_url(image_bytes, mime)}},
                {"type": "text", "text": "请识别这张课表图片，输出 JSON 数组。"},
            ],
        },
    ]


def extract_json_array(text: str) -> list:
    """从模型输出提取首个 JSON 数组：剥代码围栏，取首 [ 到尾 ]。失败抛 VisionError。"""
    if not text:
        raise VisionError("模型返回内容为空")
    fence = _FENCE_RE.search(text)
    candidate = fence.group(1).strip() if fence else text
    start, end = candidate.find("["), candidate.rfind("]")
    if start == -1 or end <= start:
        raise VisionError("模型输出中没有 JSON 数组")
    try:
        data = json.loads(candidate[start : end + 1])
    except json.JSONDecodeError as exc:
        raise VisionError(f"模型输出不是合法 JSON：{exc.msg}") from exc
    if not isinstance(data, list):
        raise VisionError("模型输出不是 JSON 数组")
    return data


def _coerce_day_of_week(value):
    """'3' → 3，容忍模型把整数写成字符串。"""
    if isinstance(value, str) and value.isdigit():
        return int(value)
    return value


def _pad_time(value):
    """'8:00' → '08:00'，容忍模型漏写前导零。"""
    if isinstance(value, str) and re.fullmatch(r"\d{1,2}:\d{2}", value):
        hh, mm = value.split(":")
        return f"{int(hh):02d}:{mm}"
    return value


def _coerce_weeks(value):
    """weeks 容忍 int / 数组 / '1-16' / '1,3,5' 字符串；无法解析返回 None（全周）。"""
    if value is None:
        return None
    if isinstance(value, int):
        return [value]
    if isinstance(value, str):
        weeks: list[int] = []
        for part in re.split(r"[,，、\s]+", value.strip()):
            if not part:
                continue
            match = re.fullmatch(r"(\d+)-(\d+)", part)
            if match:
                weeks.extend(range(int(match.group(1)), int(match.group(2)) + 1))
            elif part.isdigit():
                weeks.append(int(part))
            else:
                return None
        return weeks or None
    if isinstance(value, list) and all(isinstance(v, int) for v in value):
        return value
    return None


async def _call_vision(image_bytes: bytes, mime: str) -> str:
    """单次 chat/completions 调用，返回 message.content 文本。"""
    url = config.LLM_BASE_URL.rstrip("/") + "/chat/completions"
    payload = {
        "model": config.LLM_VISION_MODEL,
        "messages": build_messages(image_bytes, mime),
        "temperature": 0,
        "max_tokens": 4096,
    }
    headers = {"Authorization": f"Bearer {config.LLM_API_KEY}"}
    try:
        async with httpx.AsyncClient(timeout=_VISION_TIMEOUT) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
    except httpx.TimeoutException as exc:
        raise VisionTimeout("视觉模型响应超时") from exc
    except httpx.HTTPStatusError as exc:
        # 只透出状态码，不透出响应正文（可能冗长且含未知内容）
        raise VisionError(f"上游返回 HTTP {exc.response.status_code}") from exc
    except (httpx.HTTPError, ValueError) as exc:
        raise VisionError(f"请求视觉模型失败：{exc}") from exc
    content = data["choices"][0]["message"]["content"]
    if not isinstance(content, str):
        raise VisionError("模型返回结构异常")
    return content


async def parse_schedule_image(image_bytes: bytes, mime: str) -> dict:
    """识别课表图片，返回 {"courses": [dict], "skipped": int}（不落库）。

    未配置模型抛 VisionNotConfigured；每个字段经宽容转换后用 CourseIn 校验，
    无效条目跳过并计数。"""
    if not is_configured():
        raise VisionNotConfigured()
    text = await _call_vision(image_bytes, mime if mime.startswith("image/") else "image/jpeg")
    courses: list[dict] = []
    skipped = 0
    for raw in extract_json_array(text):
        if not isinstance(raw, dict):
            skipped += 1
            continue
        item = {
            "name": raw.get("name"),
            "day_of_week": _coerce_day_of_week(raw.get("day_of_week")),
            "start_time": _pad_time(raw.get("start_time")),
            "end_time": _pad_time(raw.get("end_time")),
            "location": raw.get("location", ""),
            "weeks": _coerce_weeks(raw.get("weeks")),
        }
        try:
            courses.append(CourseIn.model_validate(item).model_dump())
        except ValidationError:
            skipped += 1
    return {"courses": courses, "skipped": skipped}
