"""Reasons to open a listing, never claims of value or a buying recommendation."""
import re
from .schemas import InterestResult

# One contribution per category avoids repetition inflating scores.
RULES = (
    ('CRT', 60, r'\bCRT\b|阴极射线|显像管|监视器|特丽珑'),
    ('VFD', 60, r'\bVFD\b|真空荧光|客显'),
    ('TFEL_EL', 65, r'\b(?:TFEL|EL)\b|电致发光|薄膜电致|LJ64HB34'),
    ('PLASMA', 55, r'\bPLASMA\b|等离子(?:显示|屏)'),
    ('INDUSTRIAL_DISPLAY', 45, r'工业显示|工控屏|工业屏|工控显示|触摸屏模块'),
    ('TERMINAL', 50, r'老式终端|老终端|字符终端|串口终端|\bterminal\b'),
    ('INSTRUMENT', 45, r'示波器|频谱仪|信号发生器|计数器|逻辑分析仪|仪器仪表|高斯计|\boscilloscope\b'),
    ('LAB_MEDICAL', 40, r'医疗.{0,6}(?:电子|设备|仪器)|实验室|实验仪器'),
    ('OLD_COMPUTER', 45, r'老计算机|老电脑|古董电脑|老工业设备|古董电子|\b(?:Commodore|Amiga)\b'),
    ('MODULE', 35, r'拆机模块|不明.{0,5}(?:电子|模块)|嵌入式|开发板|奇怪.{0,5}(?:输入|输出)|电子模块'),
)
SIGNALS = (
    ('SALVAGE', 10, r'拆机|设备淘汰|按废品'),
    ('WAREHOUSE', 8, r'库存|清仓|仓库翻出'),
    ('UNKNOWN_TEST', 8, r'不会测试|不知道是什么|不懂|未测试'),
    ('OLD_INDUSTRIAL', 8, r'老设备|工业设备|仪器'),
)


def score_interest(text: str, model_count: int = 0) -> InterestResult:
    flags, score = [], 0
    for name, weight, pattern in RULES:
        if re.search(pattern, text, re.I):
            flags.append(name)
            score += weight
    has_technology = bool(flags)
    for name, weight, pattern in SIGNALS:
        if re.search(pattern, text, re.I):
            flags.append(name)
            score += weight if has_technology else min(weight, 3)
    if model_count and has_technology:
        flags.append('MODEL_CANDIDATE')
        score += 5
    return InterestResult(min(100, score), flags,
                          '命中兴趣线索：' + ', '.join(flags) if flags else '未命中电子猎手兴趣规则。')
