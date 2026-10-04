import struct

import numpy as np

from optical_mvm.zbf import plane_reference_factor, read_zbf, write_zbf


def sample_field():
    yy, xx = np.mgrid[:4, :8]
    return (xx + 10 * yy).astype(float) + 1j * (3 * xx - 2 * yy)


def assert_beam_round_trip(path, *, text):
    expected = sample_field()
    write_zbf(path, expected, dx_mm=0.125, dy_mm=0.25, wavelength_mm=0.0006328, text=text)
    beam = read_zbf(path)
    assert beam.nx == 8
    assert beam.ny == 4
    assert beam.dx_mm == 0.125
    assert beam.dy_mm == 0.25
    assert beam.wavelength_mm == 0.0006328
    np.testing.assert_array_equal(beam.ex, expected)
    np.testing.assert_array_equal(beam.x_mm, (np.arange(8) - 4) * 0.125)
    np.testing.assert_array_equal(beam.y_mm, (np.arange(4) - 2) * 0.25)
    # x advances fastest; deliberately asymmetric values expose transpose/flip errors.
    assert beam.ex[0, 1] == expected[0, 1]
    assert beam.ex[1, 0] == expected[1, 0]
    assert beam.ex[0, 1] != beam.ex[1, 0]


def test_binary_zbf_round_trip(tmp_path):
    path = tmp_path / "known.zbf"
    assert_beam_round_trip(path, text=False)
    payload = np.frombuffer(path.read_bytes(), dtype="<f8", offset=struct.calcsize("<9i20d"))
    expected = sample_field()
    serialized = np.empty((expected.size, 2), dtype=np.float64)
    serialized[:, 0] = expected.real.ravel(order="C")
    serialized[:, 1] = expected.imag.ravel(order="C")
    np.testing.assert_array_equal(payload, serialized.ravel())


def test_text_zbf_round_trip(tmp_path):
    assert_beam_round_trip(tmp_path / "known_text.zbf", text=True)


def test_pop_pilot_sphere_to_plane_phase(tmp_path):
    path = tmp_path / "piloted.zbf"
    write_zbf(path, sample_field(), dx_mm=0.125, dy_mm=0.25, wavelength_mm=0.0006328)
    payload = bytearray(path.read_bytes())
    struct.pack_into("<6d", payload, 9 * 4 + 2 * 8, -100.0, 20.0, 0.1, 0.0, 20.0, 0.1)
    path.write_bytes(payload)
    beam = read_zbf(path)
    assert beam.pilot_zx_mm == -100.0
    assert beam.pilot_rayleigh_x_mm == 20.0
    x = np.array([0.0, 0.1])
    expected = np.exp(-1j * np.pi * x**2 / (beam.wavelength_mm * beam.pilot_zx_mm))
    np.testing.assert_allclose(plane_reference_factor(beam, x), expected)
