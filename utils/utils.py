
from colormap import rgb2hex, hex2rgb
from uuid import uuid3, NAMESPACE_URL
import re


def clear(data: dict) -> dict:
    return {key: data[key] for key in data if not data[key] is None}


def string_to_uuid(string: str) -> str:
    return uuid3(NAMESPACE_URL, string).hex


def remove_gpt_file_marker(text):
    pattern = r"【(.+):(.+)】"
    return re.sub(pattern, '', text)


def adjust_lightness(color, amount=0.7):
    rgb = hex2rgb(color)

    min_color = min(rgb)
    min_color_i = rgb.index(min_color)

    ligher = [*rgb]
    ligher[min_color_i] = round(ligher[min_color_i] + ligher[min_color_i] * amount) % 256

    return rgb2hex(*rgb)


def interpolate_color(color1, color2, t):
    r = int(color1[0] * (1 - t) + color2[0] * t)
    g = int(color1[1] * (1 - t) + color2[1] * t)
    b = int(color1[2] * (1 - t) + color2[2] * t)
    return [r, g, b]


def generate_gradient(start_color, end_color, num_steps):
    gradient = []

    for i in range(num_steps):
        t = i / (num_steps - 1)
        interpolated_color = interpolate_color(start_color, end_color, t)

        gradient.append(rgb2hex(*interpolated_color))

    return gradient
