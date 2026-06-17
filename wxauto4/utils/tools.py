from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
import math
import os
import re
import shutil
import subprocess
import tempfile
import time

from PIL import Image, ImageEnhance, ImageOps

from wxauto4.param import WxParam
from wxauto4.uia import uiautomation as uia

from .win32 import GetAllWindows

def get_file_dir(dir_path=None):
    if dir_path is None:
        dir_path = Path('.').absolute()
    elif isinstance(dir_path, str):
        dir_path = Path(dir_path)
    dir_path.mkdir(parents=True, exist_ok=True)
    return dir_path

def find_window_from_root(classname=None, name=None, pid:int=None, uiaclsname:str=None, timeout=1):
    t0 = time.time()
    while True:
        wins = find_all_windows_from_root(classname, name, pid, uiaclsname)
        if len(wins) > 0:
            return wins[0]
        if time.time() - t0 > timeout:
            return None

def find_all_windows_from_root(classname:str=None, name:str=None, pid:int=None, uiaclsname:str=None):
    windows = GetAllWindows()
    targets = []
    for window in windows:
        if (
            (all((classname, name)) and classname == window[1] and name == window[2])
            or (all((classname, not name)) and classname == window[1])
            or (all((not classname, name)) and name == window[2])
        ):
            targets.append(uia.ControlFromHandle(window[0]))
    if pid:
        targets = [w for w in targets if w.ProcessId == pid]
    if uiaclsname:
        targets = [w for w in targets if w.ClassName == uiaclsname]
    return targets

def now_time(fmt='%Y%m%d%H%M%S%f'):
    return datetime.now().strftime(fmt)
        
def parse_wechat_time(time_str):
    """
    时间格式转换函数

    Args:
        time_str: 输入的时间字符串

    Returns:
        转换后的时间字符串
    """
    time_str = time_str.replace('星期天', '星期日')
    match = re.match(r'^(\d{2})-(\d{2}) (\d{2}):(\d{2}):(\d{2})$', time_str)
    if match:
        month, day, hour, minute, second = match.groups()
        current_year = datetime.now().year
        return datetime(current_year, int(month), int(day), int(hour), int(minute), int(second)).strftime('%Y-%m-%d %H:%M:%S')
    
    match = re.match(r'^(\d{1,2}):(\d{1,2})$', time_str)
    if match:
        hour, minute = match.groups()
        return datetime.now().strftime('%Y-%m-%d') + f' {hour}:{minute}:00'

    match = re.match(r'^昨天 (\d{1,2}):(\d{1,2})$', time_str)
    if match:
        hour, minute = match.groups()
        yesterday = datetime.now() - timedelta(days=1)
        return yesterday.strftime('%Y-%m-%d') + f' {hour}:{minute}:00'

    match = re.match(r'^星期([一二三四五六日]) (\d{1,2}):(\d{1,2})$', time_str)
    if match:
        weekday, hour, minute = match.groups()
        weekday_num = ['一', '二', '三', '四', '五', '六', '日'].index(weekday)
        today_weekday = datetime.now().weekday()
        delta_days = (today_weekday - weekday_num) % 7
        target_day = datetime.now() - timedelta(days=delta_days)
        return target_day.strftime('%Y-%m-%d') + f' {hour}:{minute}:00'

    match = re.match(r'^(\d{4})年(\d{1,2})月(\d{1,2})日 (\d{1,2}):(\d{1,2})$', time_str)
    if match:
        year, month, day, hour, minute = match.groups()
        return datetime(*[int(i) for i in [year, month, day, hour, minute]]).strftime('%Y-%m-%d %H:%M:%S')
    
    match = re.match(r'^(\d{2})-(\d{2}) (上午|下午) (\d{1,2}):(\d{2})$', time_str)
    if match:
        month, day, period, hour, minute = match.groups()
        current_year = datetime.now().year
        hour = int(hour)
        if period == '下午' and hour != 12:
            hour += 12
        elif period == '上午' and hour == 12:
            hour = 0
        return datetime(current_year, int(month), int(day), hour, int(minute)).strftime('%Y-%m-%d %H:%M:%S')
    
    return time_str


def is_valid_image(file_path):
    path = Path(file_path)
    
    if not path.exists() or not path.is_file():
        return False

    try:
        with Image.open(path) as img:
            img.verify()  # 只验证图像，不会完全解码
        return True
    except Exception as e:
        return False

def delete_update_files():
    home = Path.home()
    update_dir = home / 'AppData' / 'Roaming' / 'Tencent' / 'xwechat' / 'update'
    if update_dir.exists():
        for file in update_dir.iterdir():
            shutil.rmtree(file) if file.is_dir() else file.unlink()


# ============================================================================================================================================
#                                                           消息解析方法
# ============================================================================================================================================

def detect_message_direction(
    image_path: str,
    avatar_height_ratio: float = 0.8,
    tolerance: int = 0,
) -> tuple[str, float]:
    """通过截图判断消息气泡的方向。

    Args:
        image_path: 消息截图路径。
        avatar_height_ratio: 头像在截图中占据的高度比例。
        tolerance: 像素颜色比较的容忍度。

    Returns:
        Tuple[str, float]: ``("left", distance)`` 或 ``("right", distance)``，
        ``distance`` 表示从对应方向开始出现气泡的列索引，便于后续定位。
    """

    img = Image.open(image_path)
    if img.mode != 'RGB':
        img = img.convert('RGB')
    w, h = img.size

    # 仅取中间 band 区域
    band_h = int(h * avatar_height_ratio)
    y0 = (h - band_h) // 2
    y1 = y0 + band_h

    pixels = img.load()  # 获取像素访问对象

    def is_uniform_column(x: int) -> bool:
        base = pixels[x, y0]  # 以 band 顶部像素作为参考
        for y in range(y0, y1):
            r, g, b = pixels[x, y]
            if (abs(r - base[0]) > tolerance or
                abs(g - base[1]) > tolerance or
                abs(b - base[2]) > tolerance):
                return False
        return True

    # 从左边扫描
    left_idx = math.inf
    for x in range(w):
        if not is_uniform_column(x):
            left_idx = x
            break

    # 从右边扫描
    right_idx = math.inf
    for offset, x in enumerate(range(w - 1, -1, -1)):
        if not is_uniform_column(x):
            right_idx = offset  # 距右边界的列数
            break

    # print(f"left_idx: {left_idx}, right_idx: {right_idx}")
    if left_idx == math.inf and right_idx == math.inf:
        # 都没找到变化列，兜底
        return 'right', math.inf
    if left_idx <= right_idx:
        return 'left', float(left_idx)
    return 'right', float(right_idx)

def calculate_pixel_variance(region):
    """
    计算图像区域的像素变化程度
    
    Args:
        region: PIL Image对象
    
    Returns:
        float: 像素变化程度的度量值
    """
    if region.size[0] == 0 or region.size[1] == 0:
        return 0
    
    # 获取所有像素值
    pixels = list(region.getdata())
    
    if not pixels:
        return 0
    
    # 分别计算R、G、B通道的方差
    r_values = [p[0] for p in pixels]
    g_values = [p[1] for p in pixels]
    b_values = [p[2] for p in pixels]
    
    r_variance = calculate_variance(r_values)
    g_variance = calculate_variance(g_values)
    b_variance = calculate_variance(b_values)
    
    return r_variance + g_variance + b_variance

def calculate_variance(values):
    """
    计算数值列表的方差
    
    Args:
        values: 数值列表
    
    Returns:
        float: 方差值
    """
    if not values:
        return 0
    
    # 计算平均值
    mean = sum(values) / len(values)
    
    # 计算方差
    variance = sum((x - mean) ** 2 for x in values) / len(values)
    
    return variance

def calculate_color_diversity(region):
    """
    计算区域颜色多样性（备用方法）
    
    Args:
        region: PIL Image对象
    
    Returns:
        float: 颜色多样性得分
    """
    pixels = list(region.getdata())
    
    if not pixels:
        return 0
    
    # 统计不同颜色的数量
    color_set = set(pixels)
    unique_colors = len(color_set)
    
    # 计算颜色多样性比例
    diversity_ratio = unique_colors / len(pixels)
    
    return diversity_ratio

def detect_message_direction_enhanced(
    image_path: str,
    avatar_width_ratio: float = 0.15,
    avatar_height_ratio: float = 0.8,
) -> tuple[str, float]:
    """
    增强版检测，结合方差和颜色多样性
    
    Args:
        image_path: 消息图片路径
        avatar_width_ratio: 头像区域宽度比例
        avatar_height_ratio: 头像区域高度比例
    
    Returns:
        str: 'left' 或 'right'
    """
    
    img = Image.open(image_path).convert('RGB')
    width, height = img.size
    
    avatar_width = int(width * avatar_width_ratio)
    avatar_height = int(height * avatar_height_ratio)
    avatar_start_y = (height - avatar_height) // 2
    avatar_end_y = avatar_start_y + avatar_height
    
    # 截取左右头像区域
    left_box = (0, avatar_start_y, avatar_width, avatar_end_y)
    right_box = (width - avatar_width, avatar_start_y, width, avatar_end_y)
    
    left_region = img.crop(left_box)
    right_region = img.crop(right_box)
    
    # 计算方差和颜色多样性
    left_variance = calculate_pixel_variance(left_region)
    right_variance = calculate_pixel_variance(right_region)
    
    left_diversity = calculate_color_diversity(left_region)
    right_diversity = calculate_color_diversity(right_region)
    
    # 综合评分（方差权重0.7，多样性权重0.3）
    left_score = left_variance * 0.7 + left_diversity * 1000 * 0.3
    right_score = right_variance * 0.7 + right_diversity * 1000 * 0.3
    
    if left_score > right_score:
        return 'left', float(left_score)
    return 'right', float(right_score)

def batch_detect_messages(image_paths, method='basic', **kwargs):
    """
    批量检测多条消息的方向
    
    Args:
        image_paths: 图片路径列表
        method: 检测方法 ('basic' 或 'enhanced')
        **kwargs: 传递给检测函数的额外参数
    
    Returns:
        list: 检测结果列表
    """
    results = []
    
    detect_func = detect_message_direction if method == 'basic' else detect_message_direction_enhanced

    for path in image_paths:
        try:
            result = detect_func(path, **kwargs)
            if isinstance(result, tuple):
                direction, distance = result
            else:
                direction, distance = result, None
            sender = '对方' if direction == 'left' else '自己'
            results.append({
                'path': path,
                'direction': direction,
                'sender': sender,
                'distance': distance,
            })
        except Exception as e:
            results.append({
                'path': path,
                'direction': 'unknown',
                'sender': '未知',
                'error': str(e)
            })
    
    return results


# ============================================================================================================================================
#                                                           发送者解析方法
# ============================================================================

# 时间戳/系统提示等不应被识别为发送者昵称
_SENDER_EXCLUDE_PATTERNS = (
    re.compile(r'^\s*$'),
    # 时间
    re.compile(r'^\d{1,2}:\d{2}(:\d{2})?$'),
    re.compile(r'^\d{2}-\d{2}\s'),
    re.compile(r'^昨天\s'),
    re.compile(r'^前天\s'),
    re.compile(r'^星期[一二三四五六日]'),
    re.compile(r'^周[一二三四五六日]'),
    re.compile(r'^\d{4}年'),
    re.compile(r'^[上下]午\s?\d'),
    # 系统提示
    re.compile(r'^以下是新消息'),
    re.compile(r'^以上是打招呼的内容'),
    re.compile(r'^查看更多'),
    re.compile(r'^\s*查看\s*\d+\s*条'),
    re.compile(r'^\s*\d+\s*条新消息'),
    re.compile(r'^\d+$'),
    re.compile(r'^收到红包'),
    re.compile(r'^收到转账'),
    re.compile(r'^撤回了一条消息'),
    re.compile(r'^你撤回了一条消息'),
)

_WINDOWS_OCR_SCRIPT = r"""& {
$ErrorActionPreference='Stop'
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()
$path = $env:WXAUTO4_OCR_IMAGE
if (-not $path) { exit 3 }
Add-Type -AssemblyName System.Runtime.WindowsRuntime
$null = [Windows.Storage.StorageFile, Windows.Storage, ContentType = WindowsRuntime]
$null = [Windows.Storage.Streams.IRandomAccessStreamWithContentType, Windows.Storage.Streams, ContentType = WindowsRuntime]
$null = [Windows.Graphics.Imaging.BitmapDecoder, Windows.Graphics.Imaging, ContentType = WindowsRuntime]
$null = [Windows.Graphics.Imaging.SoftwareBitmap, Windows.Graphics.Imaging, ContentType = WindowsRuntime]
$null = [Windows.Media.Ocr.OcrEngine, Windows.Media.Ocr, ContentType = WindowsRuntime]
$null = [Windows.Globalization.Language, Windows.Globalization, ContentType = WindowsRuntime]
$asTaskGeneric = ([System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object {
    $_.Name -eq 'AsTask' -and $_.GetParameters().Count -eq 1 -and $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1'
})[0]
function Await($op, [Type]$type) {
    $asTask = $asTaskGeneric.MakeGenericMethod($type)
    $task = $asTask.Invoke($null, @($op))
    $task.Wait()
    $task.Result
}
$engine = [Windows.Media.Ocr.OcrEngine]::TryCreateFromLanguage([Windows.Globalization.Language]::new('zh-Hans'))
if ($null -eq $engine) { exit 2 }
$file = Await ([Windows.Storage.StorageFile]::GetFileFromPathAsync($path)) ([Windows.Storage.StorageFile])
$stream = Await ($file.OpenReadAsync()) ([Windows.Storage.Streams.IRandomAccessStreamWithContentType])
$decoder = Await ([Windows.Graphics.Imaging.BitmapDecoder]::CreateAsync($stream)) ([Windows.Graphics.Imaging.BitmapDecoder])
$bitmap = Await ($decoder.GetSoftwareBitmapAsync()) ([Windows.Graphics.Imaging.SoftwareBitmap])
$result = Await ($engine.RecognizeAsync($bitmap)) ([Windows.Media.Ocr.OcrResult])
$result.Text
}
"""

def _is_sender_excluded(name: str, content: str = None) -> bool:
    """判断文本是否应被排除在发送者候选之外"""
    if not name or not name.strip():
        return True
    name = name.strip()
    # 仅精确匹配消息内容本身（昵称不会等于完整消息文本）
    if content and name == content:
        return True
    for pat in _SENDER_EXCLUDE_PATTERNS:
        if pat.match(name):
            return True
    return False


def _clean_sender_ocr_text(text: str) -> str:
    if not text:
        return ''
    text = re.sub(r'\s+', '', text)
    text = re.sub(r'[^\w\u4e00-\u9fff·.\-（）()]+', '', text)
    return text.strip('._-·')


def _windows_ocr_text(image_path: Path) -> str:
    try:
        env = os.environ.copy()
        env['WXAUTO4_OCR_IMAGE'] = str(image_path)
        result = subprocess.run(
            [
                'powershell',
                '-NoProfile',
                '-ExecutionPolicy',
                'Bypass',
                '-Command',
                _WINDOWS_OCR_SCRIPT,
            ],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='ignore',
            timeout=WxParam.SENDER_OCR_TIMEOUT,
            creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0),
            env=env,
        )
    except Exception:
        return ''
    if result.returncode != 0:
        return ''
    return result.stdout.strip()


def _ocr_sender_from_control(control, content: str = None) -> str:
    if not WxParam.ENABLE_SENDER_OCR:
        return ''

    try:
        screenshot = Path(control.ScreenShot())
    except Exception:
        return ''

    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            image = Image.open(screenshot).convert('RGB')
            width, height = image.size
            if width < 80 or height < 20:
                return ''

            # 群聊昵称位于消息截图左上角,正文/图片从更低位置开始。
            # 裁剪区域基于 WxParam.DEFAULT_MESSAGE_XBIAS/YBIAS(头像偏移参数)
            # 计算,允许用户调整微信显示缩放后通过 WxParam 同步修正。
            # 默认 XBIAS=51 / YBIAS=30 下,与原硬编码 (55, 0, 260, 42) 完全等价。
            xbias = WxParam.DEFAULT_MESSAGE_XBIAS
            ybias = WxParam.DEFAULT_MESSAGE_YBIAS
            x_start = xbias + 4
            x_end = min(xbias + 209, width)
            y_end = min(ybias + 12, height)
            crop = image.crop((x_start, 0, x_end, y_end))
            crop = crop.resize(
                (crop.width * 4, crop.height * 4),
                Image.Resampling.LANCZOS,
            )
            gray = ImageEnhance.Contrast(ImageOps.grayscale(crop)).enhance(2.5)

            variants = [gray, gray.point(lambda pixel: 0 if pixel < 210 else 255)]
            for index, variant in enumerate(variants):
                image_path = Path(temp_dir) / f'sender_ocr_{index}.png'
                variant.save(image_path)
                sender = _clean_sender_ocr_text(_windows_ocr_text(image_path))
                if sender and not _is_sender_excluded(sender, content):
                    return sender
    except Exception:
        return ''
    finally:
        try:
            screenshot.unlink(missing_ok=True)
        except Exception:
            pass

    return ''


def extract_sender_from_control(
        control,
        content: str = None,
        max_depth: int = 8
    ):
    """从消息控件的子树中递归查找发送者昵称。

    用于群聊场景：好友消息项的子树中通常包含一个独立的昵称 TextControl，
    通过排除消息内容、时间戳、系统提示来定位。

    Args:
        control: 消息控件（通常是 ListItemControl）。
        content: 已知的消息内容，用于排除消息文本自身。
        max_depth: 递归最大深度。

    Returns:
        Optional[str]: 发送者昵称，找不到返回 None。
    """
    if control is None:
        return None

    candidates = []

    def walk(ctrl, depth):
        if depth > max_depth:
            return
        try:
            children = ctrl.GetChildren()
        except Exception:
            return
        for child in children:
            try:
                ctype = child.ControlTypeName
            except Exception:
                continue
            if ctype == 'TextControl':
                try:
                    cname = child.Name or ''
                except Exception:
                    cname = ''
                if not _is_sender_excluded(cname, content):
                    candidates.append(cname.strip())
            else:
                walk(child, depth + 1)

    walk(control, 0)

    # 第一个非排除文本即为发送者昵称（昵称通常是最靠近顶部的文本节点）
    if candidates:
        return candidates[0]
    return _ocr_sender_from_control(control, content) or None


# ============================================================================================================================================
#                                                           消息解析方法End
# ============================================================================
