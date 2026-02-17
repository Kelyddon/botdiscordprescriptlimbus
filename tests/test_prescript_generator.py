import utils.prescript_generator as pg


def test_generate_non_empty():
    rng = pg.make_daily_rng("u_test")
    script = pg.generate_prescript(rng)
    assert isinstance(script, str)
    assert script.strip() != ""


def test_deterministic_per_day(monkeypatch):
    # fix the day so RNG seed is stable
    monkeypatch.setattr(pg, 'iso_day_local', lambda: '2026-02-17')
    rng1 = pg.make_daily_rng('user123')
    rng2 = pg.make_daily_rng('user123')
    assert pg.generate_prescript(rng1) == pg.generate_prescript(rng2)


def test_normalize_whitespace():
    assert pg.normalize_punctuation('  hello   world  ') == 'hello world'


def test_fix_indefinite_articles():
    out = pg.fix_indefinite_articles('I found a apple and a hourglass')
    assert 'an apple' in out
    # 'a hourglass' should become 'an hourglass' because of silent h handling
    assert 'an hourglass' in out
