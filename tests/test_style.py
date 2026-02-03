from utils.style import parse_color
import discord


def test_parse_color_named():
    assert isinstance(parse_color('purple'), discord.Color)
    assert isinstance(parse_color('red'), discord.Color)
    assert isinstance(parse_color('blurple'), discord.Color)


def test_parse_color_hex():
    c = parse_color('#FF00FF')
    assert isinstance(c, discord.Color)
    c2 = parse_color('00FF00')
    assert isinstance(c2, discord.Color)


def test_parse_color_invalid():
    assert parse_color('notacolor') is None
    assert parse_color('') is None
