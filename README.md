# LOC-NIPI Droplet Analyser
Completed as of 01/05/23
An automated image analysis tool for studying **ice-nucleating particles (INPs)** in continuous-flow microfluidic devices, built with Python and OpenCV.

Developed as part of a Master of Physics research project at the **University of Leeds, School of Physics and Astronomy**, supervised by Dr S. A. Peyman. The tool analyses video footage from the **Lab-on-a-Chip Nucleation by Immersed Particle Instrument (LOC-NIPI)** used by [Tarn *et al.* (2020)](https://doi.org/10.1039/D0LC00251H).

📄 The full dissertation, including the literature review, methodology, and validation results, can be found in [`docs/UAzeem_LOCNIPI_Automated_Tracking_Dissertation.pdf`](docs/UAzeem_LOCNIPI_Automated_Tracking_Dissertation.pdf).

## What it does

Given a video of droplets flowing through a microfluidic channel over a cold plate, the program automatically extracts:

- **Droplet count** — total number of droplets passing through the channel
- **Frozen droplet count** — number of freezing events over the cold plate
- **Droplet diameter** (µm) — via the Circle Hough Transform
- **Droplet velocity** (µm/s) — via frame-by-frame centroid tracking

All metrics are displayed live in a Tkinter GUI and exported to a `data.csv` file, with final totals and averages in the last row.

### How it works (brief)

1. Frames are converted to greyscale and the background is removed with a MOG2 background subtractor, isolating moving droplets.
2. Morphological operations (elliptical kernel closing + median blur) clean the foreground mask.
3. Connected-component analysis (`cv2.connectedComponentsWithStats`) tracks and counts droplets in a region of interest before the cold plate.
4. The Circle Hough Transform (`cv2.HoughCircles`) measures droplet diameters.
5. Freezing events are detected in the cold-plate region by intensity thresholding — frozen droplets appear darker due to dendritic ice growth — with area-based filtering and a sanity check against the main droplet count to avoid double counting.

Validated against manually verified test footage: all droplet and freezing events were correctly identified, with measured diameters (90 ± 6 µm) and velocities (~10 mm/s) in agreement with reference values from Tarn *et al.*

## Requirements

- Python 3.7+
- OpenCV
- NumPy
- Tkinter (bundled with most Python installations)

```bash
pip install -r requirements.txt
```

Developed and tested on macOS 12.5.1 (M1) with Python 3.7.13 and OpenCV 4.1.0.

## Usage

```bash
python loc_nipi_analyser.py
```

**Input files needed:**

- An `.mp4` recording of droplets passing through the LOC-NIPI channel (AVI can be converted with VLC)
- A screen capture (`.png`/`.jpg`) of a frozen droplet, used to calibrate the freezing-detection threshold

**Steps:**

1. In the GUI, click **Browse Image File** and select the frozen droplet screenshot.
2. Click **Browse Video File** and select the recording.
3. **Channel width calibration:** click the upper and lower channel walls three times each, then press `q`. (The channel width is assumed to be 300 µm for the pixel-to-micron conversion.)
4. **Background sampling:** click a few points on the cold-plate region background, then press `q`.
5. **Frozen droplet sampling:** click a few points on the frozen droplet image, then press `q`.
6. Select two regions of interest: first the **cold plate region** (freezing detection), then the **leftmost third of the channel** (counting, velocity, and diameter measurement).
7. The analysis runs with a live display; results are written to `data.csv` as it goes.

**Assumptions/limitations:** the video should be captured at 177 fps (not decimated), with a 300 µm channel width, good contrast, and minimal condensation or artefacts. See Chapter 4 of the dissertation for details and future directions.

## Repository contents

```
├── loc_nipi_analyser.py    # Main analysis program (GUI + processing)
├── requirements.txt        # Python dependencies
├── docs/
│   └── UAzeem_Dissertation.pdf   # Full write-up: theory, methods, results
└── README.md
```

## Reference

M. D. Tarn *et al.*, "On-chip analysis of atmospheric ice-nucleating particles in continuous flow," *Lab on a Chip*, vol. 20, pp. 2889–2910, 2020.

## Author

U. Azeem (Shaami Azeem)— University of Leeds, School of Physics and Astronomy (2023)
