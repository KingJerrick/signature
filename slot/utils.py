def int_to_roman(num: int) -> str:
    """"""
    val = [
        1000, 900, 500, 400,
        100, 90, 50, 40,
        10, 9, 5, 4,
        1
    ]
    syms = [
        "M", "CM", "D", "CD",
        "C", "XC", "L", "XL",
        "X", "IX", "V", "IV",
        "I"
    ]
    roman = ""
    i = 0
    while num > 0:
        for _ in range(num // val[i]):
            roman += syms[i]
            num -= val[i]
        i += 1
    return roman

def int_to_letters(num: int) -> str:
    """1 -> a, 26 -> z, 27 -> aa"""
    result = ""
    while num > 0:
        num -= 1  # Excel 列号是从 1 开始的，所以先减 1
        result = chr(num % 26 + ord('a')) + result
        num //= 26
    return result


def hsv_to_rgb(h, s, v):
    """
    HSV(0-360, 0-255, 0-255) → RGB(0-255, 0-255, 0-255)
    """
    h = h % 360  # 360° = 0°
    s /= 255.0
    v /= 255.0

    c = v * s
    x = c * (1 - abs((h / 60) % 2 - 1))
    m = v - c

    if 0 <= h < 60:
        r_, g_, b_ = c, x, 0
    elif 60 <= h < 120:
        r_, g_, b_ = x, c, 0
    elif 120 <= h < 180:
        r_, g_, b_ = 0, c, x
    elif 180 <= h < 240:
        r_, g_, b_ = 0, x, c
    elif 240 <= h < 300:
        r_, g_, b_ = x, 0, c
    else:
        r_, g_, b_ = c, 0, x

    r = int(round((r_ + m) * 255))
    g = int(round((g_ + m) * 255))
    b = int(round((b_ + m) * 255))

    return r, g, b


def rgb_to_hsv(r, g, b):
    """
    RGB(0-255, 0-255, 0-255) → HSV(0-360, 0-255, 0-255)
    """
    r_ = r / 255.0
    g_ = g / 255.0
    b_ = b / 255.0

    max_c = max(r_, g_, b_)
    min_c = min(r_, g_, b_)
    delta = max_c - min_c

    # Hue
    if delta == 0:
        h = 0
    elif max_c == r_:
        h = 60 * (((g_ - b_) / delta) % 6)
    elif max_c == g_:
        h = 60 * (((b_ - r_) / delta) + 2)
    else:
        h = 60 * (((r_ - g_) / delta) + 4)

    # Saturation
    s = 0 if max_c == 0 else delta / max_c

    # Value
    v = max_c

    return int(round(h)), int(round(s * 255)), int(round(v * 255))

