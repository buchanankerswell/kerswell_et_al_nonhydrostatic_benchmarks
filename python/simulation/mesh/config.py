from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
import re

import matplotlib

# Single source of truth for all per-field display configuration
# Columns: file_id, cmap, clim, label, fmt, scaling, edges, transition_contours, trace
# Color limits are suite-wide fixed values (display units) so mesh plots are
# directly comparable across benchmark variants and timesteps. Symmetric
# diverging bounds cover the measured mesh-wide extrema over all complete
# runs and steps 0-20: P-hat [-1917, +697] MPa, density [-0.53, +0.61] g/cm^3,
# vertical velocity [-36, +17] cm/yr, dG [-39, +30] kJ/mol, rate +/-890 1/Ma
# (signed-log display: log10(1+890) ~= 2.95). xi overshoot beyond [0, 1] clips.
# fmt: off
_FIELD_DEFAULTS: dict[str, tuple] = {
    "T":                         ("temperature-full",         "magma",    "auto",      "$T$ (K)",                   "%.0f", 1,        False, False, False),
    "nonadiabatic_temperature":  ("temperature-nonadiabatic", "seismic",  (-1e3, 1e3), "$\\hat{T}$ (K)",            "%.0f", 1,        True,  False, False),
    "p":                         ("pressure-full",            "Oranges",  "auto",      "$P$ (GPa)",                 "%.0f", 1e-9,     False, False, False),
    "nonadiabatic_pressure":     ("pressure-nonadiabatic",    "PuOr_r",   (-2000, 2000), "$\\hat{P}$ (MPa)",          "%.0f", 1e-6,     False, False, False),
    "density":                   ("density-full",             "Purples",  "auto",      "$\\rho$ (g/cm$^3$)",        "%.1f", 1e-3,     False, False, False),
    "nonadiabatic_density":      ("density-nonadiabatic",     "BrBG",     (-0.7, 0.7), "$\\hat{\\rho}$ (g/cm$^3$)", "%.1f", 1e-3,     True,  False, False),
    "dG_driving_0":              ("dg-driving-ol-wd",         "PuOr_r",   (-40, 40),   "$dG$ (kJ/mol)",             "%.1f", 1e-3,     False, False, True),
    "seismic_Vp":                ("vp",                       "copper_r", "auto",      "$V_p$ (km/s)",              "%.1f", 1e-3,     False, False, False),
    "seismic_Vs":                ("vs",                       "copper_r", "auto",      "$V_s$ (km/s)",              "%.1f", 1e-3,     False, False, False),
    "velocity":                  ("velocity-cart",            "PiYG",     "auto",      "$\\vec{u}$ (cm/yr)",        "%.1f", 1e2,      False, False, False),
    "velocity_vertical":         ("velocity-vertical",        "PiYG",     (-40, 40),   "$\\vec{u}_y$ (cm/yr)",      "%.1f", 1e2,      True,  False, False),
    "viscosity":                 ("viscosity",                "bone_r",   (19, 24),    "Log $\\eta$ (Pa s)",        "%.0f", 1,        True,  True,  True),
    "xi_ol_wd":                  ("xi-ol-wd",                 "GnBu",     (0.0, 1.0),  "$\\xi$",                   "%.1f", 1,        False, True,  True),
    "reaction_rate_C0":          ("reaction-rate-ol-wd",      "RdGy_r",   (-3.0, 3.0), "Log $\\dot{X}$ (1/Ma)",     "%.2f", 3.154e13, True,  True,  True),
}
# fmt: on


@dataclass
class MeshConfig:
    """Display settings for mesh plots: colormaps, limits, labels, scaling.

    Per-field maps fill in from _FIELD_DEFAULTS unless overridden at
    construction time. plot_rcParams applies to matplotlib on init.
    """

    # Phase contour color for the measured-transition overlays
    transition_contour_color: str = "black"

    # Per-field display maps (populated from _FIELD_DEFAULTS if empty)
    file_map: dict[str, str] = field(default_factory=dict)
    cmap_map: dict[str, str] = field(default_factory=dict)
    clim_map: dict[str, tuple[float, float] | str] = field(default_factory=dict)
    label_map: dict[str, str] = field(default_factory=dict)
    format_map: dict[str, str] = field(default_factory=dict)
    scaling_map: dict[str, float] = field(default_factory=dict)
    edges_map: dict[str, bool] = field(default_factory=dict)
    transition_contours_map: dict[str, bool] = field(default_factory=dict)
    trace_map: dict[str, bool] = field(default_factory=dict)

    # Colormap / colorbar settings
    n_colors: int = 11
    cbar_vertical: bool = False
    cbar_title_font_size: int = 115
    cbar_label_font_size: int = 115
    cbar_width: float = 0.6
    cbar_height: float = 0.13
    cbar_n_labels: int = 3
    cbar_position: list[float] = field(default_factory=lambda: [0.20, 0.12])

    # Output / render settings
    default_fig_dir: Path = Path("figs")
    plotter_window_size: list[int] = field(default_factory=lambda: [1920, 1920])
    screenshot_dpi: tuple[int, int] = field(
        default_factory=lambda: (100, 100)
    )  # passed to PIL Image.save (metadata only; pixels come from the window size)

    # Camera settings (framing tuned for the narrow/square bench domains)
    camera_y_shift_factor: float = -0.225
    camera_zoom_factor: float = 2.925

    # Scale bar settings
    scale_bar_enabled: bool = True
    scale_bar_color: str = "black"
    scale_bar_thickness: float = 30
    scale_bar_length_fraction: float = 0.25
    scale_bar_position: tuple = (0.05, 0.08)
    scale_bar_label_font_size: int = 115
    scale_bar_label_shift_factor: float = 0.01

    # Trace and arrow indicators
    trace_line_color: str = "white"
    v_arrow_color: str = "white"
    v_arrow_alpha: float = 1.0
    v_arrow_length: float = 60e3
    v_arrow_tip_length: float = 0.35
    v_arrow_tip_radius: float = 0.22
    v_arrow_shaft_radius: float = 0.08

    # Matplotlib rcParams applied globally on init
    plot_rcParams: dict[str, Any] = field(
        default_factory=lambda: {
            "figure.dpi": 300,
            "savefig.bbox": "tight",
            "axes.facecolor": "0.9",
            "legend.frameon": False,
            "legend.facecolor": "0.9",
            "legend.loc": "upper left",
            "legend.fontsize": "small",
            "figure.autolayout": True,
            "font.size": 14,
        }
    )

    def __post_init__(self) -> None:
        """Populate per-field maps from _FIELD_DEFAULTS and apply rcParams."""
        if not self.file_map:
            self.file_map = {f: v[0] for f, v in _FIELD_DEFAULTS.items()}
        if not self.cmap_map:
            self.cmap_map = {f: v[1] for f, v in _FIELD_DEFAULTS.items()}
        if not self.clim_map:
            self.clim_map = {f: v[2] for f, v in _FIELD_DEFAULTS.items()}
        if not self.label_map:
            self.label_map = {f: v[3] for f, v in _FIELD_DEFAULTS.items()}
        if not self.format_map:
            self.format_map = {f: v[4] for f, v in _FIELD_DEFAULTS.items()}
        if not self.scaling_map:
            self.scaling_map = {f: v[5] for f, v in _FIELD_DEFAULTS.items()}
        if not self.edges_map:
            self.edges_map = {f: v[6] for f, v in _FIELD_DEFAULTS.items()}
        if not self.transition_contours_map:
            self.transition_contours_map = {f: v[7] for f, v in _FIELD_DEFAULTS.items()}
        if not self.trace_map:
            self.trace_map = {f: v[8] for f, v in _FIELD_DEFAULTS.items()}

        if self.plot_rcParams:
            matplotlib.rcParams.update(self.plot_rcParams)


# Single source of truth for benchmark figure style (colors, labels).
# Default resolution matches project.mk FIG_DPI (draft 100, manuscript 330).
BENCH_FACECOLOR = "0.92"
BENCH_DPI = 100

# Print sizing (inches) for A4/Letter with 1-inch margins: wide row
# figures span the full 6.5-inch text width; tall stacked figures fit a
# single journal column. Manuscript needs no rescaling at either DPI.
BENCH_WIDE_W = 6.5
BENCH_TALL_W = 3.5

# Seconds per mega-annum: file reaction rates are 1/s, figures use 1/Ma.
S_PER_MA = 3.154e13


def apply_bench_style(dpi: int = BENCH_DPI):
    """Match R theme_bench: grey92 panels, no grid, tick marks off, given dpi.

    Font sizes follow ggplot2 theme proportions on a 14 pt base: axis
    titles 14 (rel 1.0), tick labels and legend text 11.2 (rel 0.8),
    legend titles 14, figure titles 16.8 (rel 1.2).
    """
    import matplotlib as mpl

    mpl.rcParams.update(
        {
            "font.size": 14,
            "axes.labelsize": 14,
            "axes.titlesize": 16.8,
            "figure.titlesize": 16.8,
            "xtick.labelsize": 11.2,
            "ytick.labelsize": 11.2,
            "legend.fontsize": 11.2,
            "legend.title_fontsize": 14,
            "figure.dpi": dpi,
            "savefig.dpi": dpi,
            "savefig.bbox": "tight",
            "axes.facecolor": BENCH_FACECOLOR,
            "figure.facecolor": "white",
            "axes.grid": False,
            "xtick.direction": "out",
            "ytick.direction": "out",
            "legend.frameon": False,
        }
    )


# Standard benchmark colors, mirroring R damp_pal in R/utils/seismic.R:
# one color per damping kind+value, shared by every benchmark plot.
# None-family variants (CFL twins, no-feedback controls) get their own
# shades so every run in a panel is unique.
DAMP_COLORS = {
    "None": "#000000",
    "None_CFL1.0": "#737373",
    "None_Off": "#08306B",
    "None_Res5": "#969696",
    "None_Res7": "#525252",
    "Bimpl1e19": "#EF3B2C",
    "Bimpl1e19_CFL0.25": "#FB6A4A",
    "Bimpl1e19_Res7": "#FC9272",
    "Bimpl1e18": "#E41A1C",
    "Bimpl1e20": "#A50F15",
    "Bexpl1e19": "#74ADD1",
    "Bexpl1e20": "#377EB8",
    "Rel3.156e8": "#C7E9C0",
    "Rel3.156e9": "#A1D99B",
    "Rel3.156e11_CFL0.25": "#ADDD8E",
    "Rel3.156e11_Res7": "#4DAF4A",
    "Rel3.156e12": "#00441B",
    "Rel3.156e10": "#A6D96A",
    "Rel3.156e11": "#1B7837",
    "Cap1e8": "#984EA3",
    "Cap2e8": "#C51B7D",
    "Cap2e8_CFL0.25": "#F768A1",
    "Cap2e8_Res5": "#F1B6DA",
    "Cap2e8_Res7": "#8C0B4B",
    "Cap4e8": "#762A83",
}

DAMP_RE = re.compile(r"_Damp([A-Za-z]+)([\d.e+-]*)")
UID_DAMP_RE = re.compile(r"_Damp[A-Za-z]+[\d.e+-]*")


def damp_key(run):
    """Damping kind+value token from a UID (None, Bimpl1e21, ...).

    Extended with _CFL<value> for timestep variants, _Off for the
    no-feedback controls, and _Res<level> for off-default resolutions, so
    every benchmark run maps to a unique color.
    """
    m = DAMP_RE.search(run)
    key = (m.group(1) + m.group(2)) if m else "None"
    mc = re.search(r"_CFL([\d.]+)", run)
    if mc:
        key += f"_CFL{mc.group(1)}"
    if "_DynpOff_" in run:
        key += "_Off"
    mr = re.search(r"_Res(\d+)", run)
    if mr and mr.group(1) != "6":
        key += f"_Res{mr.group(1)}"
    return key


def bench_color(run):
    """Standard line color for a run: one color per damping kind+value."""
    return DAMP_COLORS.get(damp_key(run), "#333333")


def bench_label(run):
    """Standard legend label for a run: damping + res + CFL/no-feedback tags."""
    key = damp_key(run)
    # The variant suffixes already surface as explicit tags below; the
    # color key stays the full variant so every run maps to a unique color.
    shown = re.sub(r"_CFL[\d.]+", "", key).replace("_Off", "")
    shown = re.sub(r"_Res\d+", "", shown)
    parts = [shown or key]
    mr = re.search(r"_Res(\d+)", run)
    if mr:
        parts.append(f"Res{mr.group(1)}")
    mc = re.search(r"_CFL([\d.]+)", run)
    if mc:
        parts.append(f"CFL{mc.group(1)}")
    if "_DynpOff_" in run:
        parts.append("(no feedback)")
    return " ".join(parts)
