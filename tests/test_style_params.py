from utils.style import apply_prescript_style, chunk_text_for_edits, prepare_text_for_discord_edit


def test_spaced_param():
    s = "abc"
    out = apply_prescript_style(s, "spaced", space_char='x')
    # expect 'a x b x c'
    assert out == 'a' + 'x' + 'b' + 'x' + 'c'


def test_chunk_preserve_words():
    text = "Hello world"
    chunks = chunk_text_for_edits(text, chunk_size=7, prefer_word_boundary=True)
    # Should not split the word 'Hello' if possible
    assert ''.join(chunks) == text
    assert all(len(c) <= 7 for c in chunks)


def test_prepare_text_for_discord_edit():
    text = "Test rendering"
    chunks = prepare_text_for_discord_edit(text, variant='spaced', chunk_size=5)
    # joined should equal stylized text
    joined = ''.join(chunks)
    assert joined == apply_prescript_style(text, 'spaced')
    assert len(chunks) >= 1
