from app.services.analyzer import analyze_text


def test_positive_with_degree_and_exclaim():
    out = analyze_text("非常好，物流很快，包装也很用心！")
    assert out.polarity == "positive"
    assert out.confidence >= 0.3
    words = {h["word"] for h in out.hit_words}
    assert "好" in words and "快" in words


def test_negative_review():
    out = analyze_text("质量太差了，客服态度恶劣，再也不买了")
    assert out.polarity == "negative"
    assert out.raw_score < 0


def test_neutral_plain_text():
    out = analyze_text("商品于2026年10月1日收到，订单编号12345")
    assert out.polarity == "neutral"


def test_url_is_ignored():
    out = analyze_text("看看这个 https://example.com/item/123456")
    assert out.polarity == "neutral"
    assert out.hit_words == []


def test_negation_flips_polarity():
    out = analyze_text("客服并不热情")
    assert out.polarity == "negative"
    assert any(h["word"] == "热情" and h["contribution"] < 0 for h in out.hit_words)


def test_builtin_negated_positive_word():
    out = analyze_text("质量很不错，值得推荐")
    assert out.polarity == "positive"


def test_window_not_polluted_by_previous_word():
    # 上一个词「不好用」里的「不」不能翻转后续的「退货」
    out = analyze_text("这东西不好用，退货了")
    assert out.polarity == "negative"
    assert all(h["contribution"] < 0 for h in out.hit_words)


def test_double_negation():
    # 不是 + 不好吃 → 双重否定回到正面
    out = analyze_text("味道不是不好吃")
    assert out.polarity == "positive"
    # 没有 + 不满意 → 正面
    out = analyze_text("售后没有不满意")
    assert out.polarity == "positive"


def test_confidence_in_range():
    for text in ["很好很好很好", "一般般", "毫无亮点"]:
        out = analyze_text(text)
        assert 0 <= out.confidence <= 1
