# Physical Optics Propagation settings

Run each input separately in the OpticStudio GUI. Input and output ZBF beams reside in the installation-specific `POP/BEAMFILES` folder. Pass the parent `POP` folder to `scripts/copy_to_zemax.py --pop-dir ...`; the helper checks for `BEAMFILES` and copies inputs there. On this machine the folder was `C:\Users\ethan\OneDrive\Documents\Zemax\POP\BEAMFILES`.

| POP control | Required setting |
|---|---|
| Analysis | Physical Optics Propagation |
| Start surface | 1 (INPUT FIELD) |
| End surface | 3 (OUTPUT / DFT PLANE) |
| Wavelength | 1 (632.8 nm) |
| Field | 1 |
| Initial beam | File |
| Input | One selected `.ZBF` beam |
| Beam power setting | Peak Irradiance = 1 W/mm² |
| Polarization | Off |
| Save Output Beam | On |
| Auto Apply | Off |
| Sampling | Use sampling encoded by input ZBF |

In the POP settings, use **General** for start/end surfaces, wavelength, field, and polarization; **Beam Definition** for `Beam Type: File`, the selected input ZBF, and Peak Irradiance = 1; and **Display** for `Save Output Beam To`. Turn **Auto Apply off before changing input beams**, so selecting a new input cannot overwrite the previous output file. Set the input file and matching output filename, then press **OK** for each run. The output name is entered without a path; OpticStudio writes the ZBF to `POP/BEAMFILES` and adds `.ZBF` if needed. See the [OpticStudio POP reference](https://ansyshelp.ansys.com/public/Views/Secured/Zemax/v25101/en/OpticStudio_User_Guide/OpticStudio_Help/topics/Physical_Optics_Propagation.html).

Use binary inputs produced by `python scripts/generate_inputs.py`. For each run, select one input and save the output with the exact corresponding name:

```text
basis_0.zbf -> basis_0_out.zbf
basis_1.zbf -> basis_1_out.zbf
basis_2.zbf -> basis_2_out.zbf
basis_3.zbf -> basis_3_out.zbf
demo.zbf    -> demo_out.zbf
```

Copy these five output beams into `data/output/`, using lowercase `.zbf` names if the host filesystem distinguishes case, then run `python scripts/analyze_results.py`. The measured run used `.venv\Scripts\python.exe` because dependencies were installed in that virtual environment.

If POP reports clipping or sampling warnings, record the message. Inspect input and output with `scripts/inspect_zbf.py`; increase ZBF sampling through `config/project.yaml` only after confirming the current run's coordinate and aperture setup. Basis outputs may have a different pixel size and pilot phase reference from the demo output; the analysis handles both and records the demo's global phase alignment in `results/metrics.json`.
