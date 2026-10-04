# Sequential prescription: 4×4 Fourier matrix

The starter file `optical_matrix_4x4.zmx` encodes this Sequential prescription using the text syntax of installed OpticStudio sample files. It was opened and saved in OpticStudio Student 2026 R1. The four surfaces and 200 mm axial layout were checked in the GUI; the saved file retains the wavelength, pupil, and focal-length values below.

## System settings

| Setting | Value |
|---|---|
| Mode | Sequential |
| Lens units | mm |
| Wavelength 1 | 0.6328 µm |
| Field 1 | X = 0°, Y = 0° |
| Entrance pupil diameter | 10 mm |

## Lens Data Editor

| Surface | Comment | Type | Thickness after surface | Semi-diameter | Parameter 1 |
|---:|---|---|---:|---:|---|
| 0 | OBJECT | Standard object | 0 mm | — | — |
| 1 | INPUT FIELD | Standard / dummy | 100.000 mm | 2.0 mm | — |
| 2 | FOURIER LENS | Paraxial | 100.000 mm | 5.0 mm | 100.000 mm focal length |
| 3 | OUTPUT / DFT PLANE | Image | — | 2.0 mm | — |

Set surface 2 as the aperture stop. Use a flat Standard surface for the input plane. On the Paraxial surface, set Parameter 1 to the stated focal length. Confirm the image surface lies one focal length after the lens.

The axial layout is:

```text
Input plane  --100 mm-->  ideal f=100 mm lens  --100 mm-->  Fourier/output plane
```

Input-beam sample positions occupy ±0.375 mm; the input plane's 2 mm semi-diameter clears the complete beam array. The lens's 5 mm semi-diameter is the 10 mm pupil stop.

## OpticStudio review checklist

1. Open `optical_matrix_4x4.zmx` and confirm Units are Millimeters.
2. In System Explorer, confirm aperture type is Entrance Pupil Diameter and value is 10 mm.
3. Confirm the on-axis field and the active wavelength at 0.6328 µm.
4. Confirm surface 2 is Paraxial, its focal-length parameter is 100 mm, and it is the aperture stop.
5. Verify total track from input to lens and lens to image is 100 mm each, then save from OpticStudio.
6. Run POP using `POP_SETTINGS.md`.

## Prescription table file

`prescription.csv` restates surface number, comment, type, thickness, semi-diameter, and focal length for reference. It is not a Zemax import format.
