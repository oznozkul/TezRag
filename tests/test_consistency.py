import numpy as np
import pytest

from src.consistency import fleiss_kappa


def test_fleiss_kappa():
    same = np.array([[1, 1, 1], [0, 0, 0], [1, 1, 1], [0, 0, 0]])
    assert fleiss_kappa(same) == pytest.approx(1.0)
    noisy = np.array([[1, 0, 1], [0, 1, 0], [1, 0, 0], [0, 1, 1]])
    assert fleiss_kappa(noisy) < 0
    # textbook value: 2 categories, 3 raters
    m = np.array([[1, 1, 1], [1, 1, 0], [0, 0, 0], [1, 0, 0], [1, 1, 1]])
    p_i = np.array([1.0, 1 / 3, 1.0, 1 / 3, 1.0])
    pj1 = m.sum() / m.size
    pe = pj1 ** 2 + (1 - pj1) ** 2
    assert fleiss_kappa(m) == pytest.approx((p_i.mean() - pe) / (1 - pe))
