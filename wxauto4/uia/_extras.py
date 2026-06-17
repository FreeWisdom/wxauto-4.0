"""wxauto4 在 uiautomation 之上补充的辅助函数。

历史上这些函数被嵌在 ``wxauto4/uia/uiautomation.py`` 的 381KB 内嵌源码里。
替换为 PyPI 依赖后,把它们独立出来,逻辑不变。
"""

from __future__ import annotations

import time

__all__ = [
    "RollIntoView",
    "CheckElementPosition",
    "IsElementInWindow",
    "GetElementPositionDescription",
]


def RollIntoView(win, ele, equal=True, bias=0):
    """将目标元素滚动到主窗口内可见区域。

    参数:
        win: 主窗口元素 (uiautomation.Control 对象)
        ele: 目标元素 (uiautomation.Control 对象)
        equal: 保留参数,暂未使用
        bias: 偏移量,元素边缘需要超过这个量才算完全在窗口内(默认为 0)
    """

    win_rect = win.BoundingRectangle
    ele_rect = ele.BoundingRectangle

    win_top = win_rect.top + bias
    win_bottom = win_rect.bottom - bias
    win_height = win_bottom - win_top

    ele_top = ele_rect.top
    ele_bottom = ele_rect.bottom
    ele_height = ele_rect.height()
    ele_ycenter = ele_rect.ycenter()

    if ele_height > win_height:
        target_top = ele_ycenter
        target_bottom = ele_ycenter
    else:
        target_top = ele_top
        target_bottom = ele_bottom

    max_attempts = 100
    attempt = 0

    while attempt < max_attempts:
        current_ele_rect = ele.BoundingRectangle

        if ele_height > win_height:
            current_ycenter = current_ele_rect.ycenter()
            if win_top <= current_ycenter <= win_bottom:
                break
            if current_ycenter < win_top:
                win.WheelUp()
                time.sleep(0.1)
            elif current_ycenter > win_bottom:
                win.WheelDown()
                time.sleep(0.1)
        else:
            current_top = current_ele_rect.top
            current_bottom = current_ele_rect.bottom

            if win_top <= current_top and current_bottom <= win_bottom:
                break

            if current_top < win_top:
                win.WheelUp()
                time.sleep(0.1)
            elif current_bottom > win_bottom:
                win.WheelDown()
                time.sleep(0.1)
            else:
                break

        attempt += 1

    if attempt >= max_attempts:
        print(f"Warning: 滚动操作达到最大尝试次数({max_attempts}),可能元素无法完全滚动到视图内")


def CheckElementPosition(win, ele, bias=0):
    """判断目标元素相对于主窗口的位置关系。

    参数:
        win: 主窗口元素
        ele: 目标元素
        bias: 偏移量

    返回:
        dict: 各种位置关系判断结果
    """

    win_rect = win.BoundingRectangle
    ele_rect = ele.BoundingRectangle

    win_top = win_rect.top + bias
    win_bottom = win_rect.bottom - bias
    win_left = win_rect.left + bias
    win_right = win_rect.right - bias

    ele_top = ele_rect.top
    ele_bottom = ele_rect.bottom
    ele_left = ele_rect.left
    ele_right = ele_rect.right

    result = {
        'ele_top_above_win_top': ele_top < win_top,
        'ele_bottom_below_win_bottom': ele_bottom > win_bottom,
        'ele_completely_above_win': ele_bottom <= win_top,
        'ele_completely_below_win': ele_top >= win_bottom,
        'ele_vertically_inside_win': win_top <= ele_top and ele_bottom <= win_bottom,
        'win_vertically_inside_ele': ele_top <= win_top and win_bottom <= ele_bottom,

        'ele_left_before_win_left': ele_left < win_left,
        'ele_right_after_win_right': ele_right > win_right,
        'ele_completely_left_of_win': ele_right <= win_left,
        'ele_completely_right_of_win': ele_left >= win_right,
        'ele_horizontally_inside_win': win_left <= ele_left and ele_right <= win_right,
        'win_horizontally_inside_ele': ele_left <= win_left and win_right <= ele_right,

        'ele_completely_inside_win': False,
        'win_completely_inside_ele': False,
        'ele_and_win_overlap': False,
        'ele_and_win_separate': False,
    }

    result['ele_completely_inside_win'] = (
        result['ele_vertically_inside_win'] and result['ele_horizontally_inside_win']
    )
    result['win_completely_inside_ele'] = (
        result['win_vertically_inside_ele'] and result['win_horizontally_inside_ele']
    )

    vertical_overlap = not (result['ele_completely_above_win'] or result['ele_completely_below_win'])
    horizontal_overlap = not (result['ele_completely_left_of_win'] or result['ele_completely_right_of_win'])
    result['ele_and_win_overlap'] = vertical_overlap and horizontal_overlap
    result['ele_and_win_separate'] = not result['ele_and_win_overlap']

    return result


def IsElementInWindow(win, ele, bias=0):
    """判断元素是否在窗口内(仅垂直方向)。

    参数:
        win: 主窗口元素
        ele: 目标元素
        bias: 偏移量

    返回:
        bool: True 表示元素在窗口内
    """
    position_info = CheckElementPosition(win, ele, bias)
    return position_info['ele_vertically_inside_win']


def GetElementPositionDescription(win, ele, bias=0):
    """获取元素位置的文字描述。"""

    result = CheckElementPosition(win, ele, bias)

    if result['ele_completely_inside_win']:
        return "元素完全在窗口内部"
    elif result['win_completely_inside_ele']:
        return "窗口完全在元素内部"
    elif result['ele_completely_above_win']:
        return "元素完全在窗口上方"
    elif result['ele_completely_below_win']:
        return "元素完全在窗口下方"
    elif result['ele_completely_left_of_win']:
        return "元素完全在窗口左侧"
    elif result['ele_completely_right_of_win']:
        return "元素完全在窗口右侧"
    elif result['ele_and_win_overlap']:
        descriptions = []
        if result['ele_top_above_win_top']:
            descriptions.append("元素顶部高于窗口顶部")
        if result['ele_bottom_below_win_bottom']:
            descriptions.append("元素底部低于窗口底部")
        if result['ele_left_before_win_left']:
            descriptions.append("元素左边超出窗口左边")
        if result['ele_right_after_win_right']:
            descriptions.append("元素右边超出窗口右边")

        if descriptions:
            return "元素与窗口重叠," + ",".join(descriptions)
        else:
            return "元素与窗口重叠"
    else:
        return "元素与窗口完全分离"
