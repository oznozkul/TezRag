import pandas as pd
import pytest

from src.annotation import review_labels


def write(tmp_path, rows):
    path = tmp_path / "review.csv"
    pd.DataFrame(rows, columns=["item_id", "check_first", "suggested_label", "verdict", "note"]).to_csv(
        path, sep=";", index=False, encoding="utf-8-sig")
    return path


def test_review_labels_accept_override_and_skip(tmp_path):
    path = write(tmp_path, [["A1", "0", "1", "ok", ""], ["A2", "1", "0", "1", "gold outdated"],
                            ["A3", "0", "1", "", ""], ["A4", "1", "?", "OK", ""], ["A5", "0", "0", "?", ""]])
    lab = review_labels(path).set_index("item_id")
    assert list(lab.index) == ["A1", "A2", "A4", "A5"]          # empty verdict = not reviewed
    assert lab.label.to_dict() == {"A1": "1", "A2": "1", "A4": "?", "A5": "?"}
    assert lab.changed.to_dict() == {"A1": False, "A2": True, "A4": False, "A5": True}


def test_review_labels_rejects_unknown_verdict(tmp_path):
    path = write(tmp_path, [["A1", "0", "1", "yes", ""]])
    with pytest.raises(ValueError):
        review_labels(path)
