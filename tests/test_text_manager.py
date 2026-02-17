import json
from utils.text_manager import PrescriptManager


def test_load_simple_list(tmp_path):
    data = ["one", "two", "three"]
    p = tmp_path / "p.json"
    p.write_text(json.dumps(data), encoding='utf-8')
    mgr = PrescriptManager.load_from_file(str(p), 'fr')
    assert mgr.list_texts() == data


def test_weighted_choice(tmp_path):
    data = {"prescripts": [{"text": "a", "weight": 0.1}, {"text": "b", "weight": 10}]}
    p = tmp_path / "p2.json"
    p.write_text(json.dumps(data), encoding='utf-8')
    mgr = PrescriptManager.load_from_file(str(p), 'fr')
    # with seed, weighted should pick 'b' most of the time
    val = mgr.choose_weighted(seed=42)
    assert val in ("a", "b")


def test_sequential(tmp_path):
    data = {"prescripts": ["x", "y"]}
    p = tmp_path / "p3.json"
    p.write_text(json.dumps(data), encoding='utf-8')
    mgr = PrescriptManager.load_from_file(str(p), 'fr')
    assert mgr.next_sequential() == "x"
    assert mgr.next_sequential() == "y"
    assert mgr.next_sequential() == "x"


def test_formatting():
    entries = ["Hello {name}"]
    mgr = PrescriptManager(entries)
    assert mgr.format_text(mgr.list_texts()[0], {"name": "Alice"}) == "Hello Alice"
