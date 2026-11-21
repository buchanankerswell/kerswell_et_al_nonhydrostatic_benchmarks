from dataclasses import dataclass

import numpy as np


@dataclass
class PhaseTransition:
    """
    Container for extracted ASPECT phase transition parameters.

    Attributes:
        y (float):            Vertical coordinate in the model domain (m).
        depth (float):        Depth relative to the model surface     (m).
        temperature (float):  Temperature at the transition           (K).
        clapeyron (float):    Clapeyron slope (dP/dT)                 (Pa/K).
        density_jump (float): Change in density across the transition (kg/m^3).
    """

    y: float
    depth: float
    temperature: float
    clapeyron: float
    density_jump: float


def nominal_410_for_uid(model_id: str, nominal_box: float, nominal_sink400: float) -> float:
    """Runtime-adiabat 410 nominal (m) for a UID: box uses the block-free adiabat; all sink runs carry Block400."""
    if model_id.startswith("NH_Box_"):
        return nominal_box
    return nominal_sink400


def read_dG_profile(filepath: str) -> tuple[list[str], np.ndarray]:
    """
    Read a TSV profile file, skipping comment lines.

    Args:
        filepath: Path to the TSV file.

    Returns:
        tuple containing a list of headers and a numpy array of data.
    """
    # Initialize as None to identify the first non-comment line
    headers: list[str] | None = None
    data: list[list[float]] = []

    with open(filepath) as f:
        for line in f:
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue

            cols = stripped.split("\t")
            if headers is None:
                headers = cols
            else:
                try:
                    data.append([float(v) for v in cols])
                except ValueError:
                    continue

    # Logic check to satisfy the type checker and ensure file integrity
    if headers is None or not data:
        raise ValueError(f" XX Error: No valid header or data rows found in {filepath}")

    return headers, np.array(data)


def load_depth_datum(path: str) -> dict[str, np.ndarray]:
    """Canonical model-depth to true-depth table (m), per suite.

    True depth maps ambient pressure through the BurnMan isentrope, so the
    phase transition lands near 410 km instead of at model-domain depth.
    """
    rows = []
    with open(path) as f:
        for line in f:
            s = line.strip()
            if not s or s.startswith("#"):
                continue
            rows.append([float(v) for v in s.split()])
    data = np.array(rows)
    cols = ["model_depth_m", "box", "sink"]
    assert data.shape[1] == 3, f"depth datum must have 3 columns, got {data.shape[1]}"
    return {k: data[:, i] for i, k in enumerate(cols)}


def model_to_true_km(model_depth_km, datum: dict[str, np.ndarray], suite: str):
    """True depth (km) for model depths (km) via the datum table."""
    return np.interp(np.asarray(model_depth_km, dtype=float) * 1e3, datum["model_depth_m"], datum[suite]) / 1e3


def true_to_model_km(true_depth_km, datum: dict[str, np.ndarray], suite: str):
    """Model depth (km) for true depths (km); inverse of model_to_true_km."""
    return np.interp(np.asarray(true_depth_km, dtype=float) * 1e3, datum[suite], datum["model_depth_m"]) / 1e3


def find_surface_depth_offset(headers: list[str], data: np.ndarray, surface_pressure: float) -> float:
    """
    Finds the depth at which the profile matches the model's surface pressure.
    """
    col = {h: i for i, h in enumerate(headers)}
    pressures = data[:, col["pressure"]]
    depths = data[:, col["depth"]]

    if surface_pressure <= pressures[0]:
        return float(depths[0])

    idx = int(np.searchsorted(pressures, surface_pressure)) - 1
    idx = max(0, min(idx, len(pressures) - 2))

    # Linear interpolation
    t = (surface_pressure - pressures[idx]) / (pressures[idx + 1] - pressures[idx])
    return float(depths[idx] + t * (depths[idx + 1] - depths[idx]))


def find_transition(headers: list[str], data: np.ndarray, model_height: float, surface_depth_offset: float) -> PhaseTransition:
    """
    Locates the zero crossing of delta_molar_gibbs to define the phase boundary.

    Returns:
        PhaseTransition: Dataclass containing calculated parameters.
    """
    col = {h: i for i, h in enumerate(headers)}

    profile_depth = data[:, col["depth"]]
    temperature = data[:, col["temperature"]]
    delta_gibbs = data[:, col["delta_molar_gibbs"]]
    delta_entropy = data[:, col["delta_molar_entropy"]]
    delta_volume = data[:, col["delta_molar_volume"]]
    delta_density = data[:, col["delta_density"]]

    for i in range(len(delta_gibbs) - 1):
        # Look for zero crossing where Gibbs energy switches sign
        if delta_gibbs[i] > 0 and delta_gibbs[i + 1] <= 0:
            t = delta_gibbs[i] / (delta_gibbs[i] - delta_gibbs[i + 1])

            def interp(arr):
                return arr[i] + t * (arr[i + 1] - arr[i])

            trans_depth_profile = interp(profile_depth)
            trans_T = interp(temperature)
            trans_dS = interp(delta_entropy)
            trans_dV = interp(delta_volume)
            trans_drho = interp(delta_density)

            if abs(trans_dV) < 1e-20:
                raise ValueError(" XX Error: delta_molar_volume is zero at transition.")

            clapeyron = trans_dS / trans_dV
            model_depth = trans_depth_profile - surface_depth_offset
            model_y = model_height - model_depth

            return PhaseTransition(y=model_y, depth=model_depth, temperature=trans_T, clapeyron=clapeyron, density_jump=trans_drho)

    raise ValueError(" XX Error: no zero crossing found in delta_molar_gibbs")
