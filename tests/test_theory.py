import numpy as np

from optical_mvm.theory import centered_dft_matrix


def test_centered_dft_is_unitary_for_both_signs():
    for sign in (-1, 1):
        matrix = centered_dft_matrix(4, sign)
        np.testing.assert_allclose(matrix.conj().T @ matrix, np.eye(4), atol=1e-12, rtol=0)


def test_demo_vector_expected_output():
    vector = np.array([1.0, 0.6, -0.4, 0.8], dtype=np.complex128)
    output = centered_dft_matrix(4, -1) @ vector
    expected = np.array([
        -0.7932232360236493 - 0.4236714230191345j,
        0.4368030423797096 - 0.2837296694336735j,
        0.4368030423797096 + 0.2837296694336735j,
        -0.7932232360236493 + 0.4236714230191345j,
    ])
    np.testing.assert_allclose(output, expected, atol=1e-12, rtol=0)
