import numpy as np

from optical_mvm.theory import focal_plane_positions


def test_expected_fourier_plane_positions():
    positions = focal_plane_positions(4, 0.250, 0.0006328, 100.0)
    np.testing.assert_allclose(positions, [-0.09492, -0.03164, 0.03164, 0.09492], atol=1e-14, rtol=0)
