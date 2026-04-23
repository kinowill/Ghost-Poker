from ghost_poker.perception.ocr import OCRLine
from ghost_poker.perception.table_state import _parse_actions


def test_parse_actions_uses_spatial_matching_for_hotkeys_and_amounts() -> None:
    lines = [
        OCRLine(text="All-In", score=0.99, left=105, top=7, width=44, height=19),
        OCRLine(text="F4", score=0.99, left=85, top=9, width=16, height=12),
        OCRLine(text="33%", score=0.97, left=21, top=53, width=28, height=17),
        OCRLine(text="100%", score=1.0, left=133, top=56, width=30, height=13),
        OCRLine(text="50%", score=0.91, left=79, top=57, width=24, height=11),
        OCRLine(text="Raise", score=1.0, left=70, top=77, width=43, height=14),
        OCRLine(text="F3", score=1.0, left=13, top=84, width=16, height=12),
        OCRLine(text="$40", score=1.0, left=74, top=92, width=34, height=18),
        OCRLine(text="Call", score=1.0, left=77, top=120, width=31, height=16),
        OCRLine(text="F2", score=0.97, left=13, top=128, width=16, height=12),
        OCRLine(text="$20", score=1.0, left=75, top=136, width=34, height=17),
        OCRLine(text="F1", score=0.89, left=13, top=172, width=16, height=12),
        OCRLine(text="Fold", score=1.0, left=73, top=172, width=37, height=16),
    ]

    state = _parse_actions(lines)

    assert state.all_in_hotkey == "F4"
    assert state.presets_percent == [33, 50, 100]
    assert [option.to_dict() for option in state.options] == [
        {"label": "Raise", "hotkey": "F3", "amount": 40},
        {"label": "Call", "hotkey": "F2", "amount": 20},
        {"label": "Fold", "hotkey": "F1", "amount": None},
    ]
