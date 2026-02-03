from utils.text_manager import charger_prescripts

def test_charger_prescripts():
	prescripts = charger_prescripts("data/prescript.json", "fr")
	assert isinstance(prescripts, list)
	assert len(prescripts) > 0
