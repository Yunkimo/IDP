"""气泡折行逻辑测试（纯函数）+ 气泡基本行为测试。"""

from pet.bubble import wrap_text


def test_wrap_text_empty():
    assert wrap_text("", 100, len) == [""]


def test_wrap_text_wraps_long():
    # measure=len，即每字符宽 1 像素
    assert wrap_text("abcdef", 3, len) == ["abc", "def"]


def test_wrap_text_newline():
    assert wrap_text("ab\ncd", 10, len) == ["ab", "cd"]


def test_bubble_append(qapp):
    from pet.bubble import SpeechBubble

    b = SpeechBubble(timeout_ms=0)  # 0 = 不自动隐藏
    b.set_text("你好")
    assert b._text == "你好"
    b.append_chunk("呀")
    assert b._text == "你好呀"
