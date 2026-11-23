from dataclasses import dataclass

import numpy as np
from config import MeshConfig


@dataclass
class MeshPostProcessor:
    """
    Measures phase transition structure from geodynamic simulation meshes.

    Provides methods to locate the best-representative vertical profile for a phase transition, extract depth profiles, and compute scalar maxima
    within the transition window.
    """

    config: MeshConfig
    verbosity: int = 0

    def calculate_max_in_region(
        self, depths: np.ndarray, values: np.ndarray, rxn_depth: float, displacement: float, width: float, width_threshold: float = 15e3
    ) -> float:
        """
        Return the maximum absolute value within the depth window around the transition.

        Args:
            depths:        Depth array (m), sorted ascending.
            values:        Field value array aligned with depths.
            rxn_depth:     Nominal reaction depth (m).
            displacement:  Measured transition displacement from rxn_depth (m).
            width:         Measured transition width (m).

        Returns:
            Maximum absolute value within the window, or nan if the window contains no points or inputs are empty.
        """
        if depths.size == 0 or values.size == 0:
            return np.nan

        lower_factor, upper_factor = self._bound_factors(width, width_threshold)
        lower = max(np.nanmin(depths), rxn_depth + displacement - width * lower_factor)
        upper = min(np.nanmax(depths), rxn_depth + displacement + width * upper_factor)

        mask = (depths >= lower) & (depths <= upper)

        if not np.any(mask):
            center = rxn_depth + displacement
            nearest_idx = np.argmin(np.abs(depths - center))
            return float(np.abs(values[nearest_idx]))

        return float(np.nanmax(np.abs(values[mask]))) if np.any(mask) else np.nan

    def transition_depth_bounds(
        self, rxn_depth: float, displacement: float, width: float, width_threshold: float = 15e3, for_visualizing: bool = False
    ) -> tuple[float, float]:
        """
        Return (lower, upper) mesh-relative depth bounds for the transition window.

        Uses the same _bound_factors as calculate_max_in_region so that annotation brackets in plots are geometrically identical to the max-value
        integration window.

        Args:
            rxn_depth:    Nominal reaction depth (m).
            displacement: Measured transition displacement from rxn_depth (m).
            width:        Measured transition width (m).

        Returns:
            (lower, upper) depths in mesh-relative coordinates (m).
        """
        if not for_visualizing:
            lower_factor, upper_factor = self._bound_factors(width, width_threshold)
            lower = rxn_depth + displacement - width * lower_factor
            upper = rxn_depth + displacement + width * upper_factor
        else:
            lower = rxn_depth + displacement - width
            upper = rxn_depth + displacement

        return lower, upper

    def _bound_factors(self, width: float, width_threshold: float = 15e3) -> tuple[float, float]:
        """
        Return (lower_factor, upper_factor) for the transition depth window.

        Narrow transitions (width <= threshold) use a wider lower margin to capture the full phase change. Broad transitions use a tighter window.
        """
        return (2.5, 1.5) if width <= width_threshold else (2.0, 1.0)

    def _evaluate_transition_structure(
        self,
        depths: np.ndarray,
        values: np.ndarray,
        rxn_depth: float,
        search_window: float = 100e3,
    ) -> tuple[float, float, float]:
        """
        Measure the displacement and width of a phase transition from a depth profile.

        The transition runs from the first sample above 0.1 to the first
        sample above 0.9 in phase fraction. Small dips inside that span are
        smoothed, and crossings are found by straight-line interpolation.
        Each crossing anchors to rxn_depth: when several crossings exist,
        the one whose midpoint sits closest to rxn_depth wins, so stray
        crossings far from the known transition depth cannot hijack the
        measurement.

        When both crossings are found, the result is checked before use:
            - depth_90 must be greater than depth_10 (crossings in order).
            - the midpoint of the transition must lie within max_displacement_limit of rxn_depth.

        Transition structure is then computed as:
            displacement = depth(X=0.9) - rxn_depth
            width        = depth(X=0.9) - depth(X=0.1)

        If only one crossing is found, width falls back to the local depth
        spacing at that crossing and trans_depth is set to the single
        valid crossing depth.

        Args:
            depths:        Depth array (m), sorted ascending.
            values:        Phase fraction array aligned with depths, expected to be broadly 0 -> 1.
            rxn_depth:     Nominal reaction depth (m), used both to anchor crossing selection and to compute displacement.
            search_window: Half-width (m) of the depth window around rxn_depth within which the inferred transition must lie. Default 80 km.

        Returns:
            (trans_depth, displacement, width) in meters, or (nan, nan, nan) if the profile is too corrupt, no valid crossings are found,
            or the inferred transition location fails the proximity check.
        """

        if len(depths) < 2:
            return np.nan, np.nan, np.nan

        dz_all = np.diff(depths)
        if dz_all.size == 0:
            return np.nan, np.nan, np.nan
        dz_min = float(np.nanmin(dz_all))

        values = self._fill_gaps(np.asarray(values, dtype=float))
        clean = np.nan_to_num(values, nan=-np.inf)

        # The transition completes at the first sample above nine tenths. Everything below that
        # belongs to the next transition, which overprints the profile (the 520 truncates the
        # wadsleyite layer of a cold slab) and must stay out of the repair.
        above_10 = np.where(clean >= 0.1)[0]
        above_90 = np.where(clean >= 0.9)[0]
        if above_10.size == 0 or above_90.size == 0:
            return np.nan, np.nan, np.nan
        i10 = int(above_10[0])
        i90 = int(above_90[0])
        if i90 <= i10:
            return np.nan, np.nan, np.nan

        # The search spans the depth window around rxn_depth, but stops at the completion of the
        # transition, and reaches back to the onset in case the transition sits above the window.
        search_lo = int(np.searchsorted(depths, rxn_depth - search_window))
        lo = min(search_lo, max(0, i10 - 1))
        hi = i90

        # Monotonicity repair via isotonic regression (PAVA), confined to the transition.
        repaired_values = values.copy()
        repaired_values[lo : hi + 1] = self._repair_monotonic(values[lo : hi + 1], depths[lo : hi + 1], rxn_depth, search_window, bounds=(0, hi - lo))

        bracket_depths = depths[lo : hi + 1]
        bracket_values = repaired_values[lo : hi + 1]

        # Crossing detection
        def find_crossing(target: float) -> int:
            """Return bracket index of the crossing closest to rxn_depth."""
            if bracket_depths.size < 2:
                return -1
            signs = np.sign(bracket_values - target)
            signs[signs == 0] = 1
            local_crossings = np.where(np.diff(signs) != 0)[0]
            if not local_crossings.size:
                return -1
            crossing_depths = 0.5 * (bracket_depths[local_crossings] + bracket_depths[local_crossings + 1])
            return int(local_crossings[np.argmin(np.abs(crossing_depths - rxn_depth))])

        def interp_depth(target: float, idx: int) -> float:
            if idx < 0 or idx >= len(bracket_values) - 1:
                return np.nan
            x0, x1 = bracket_values[idx], bracket_values[idx + 1]
            z0, z1 = bracket_depths[idx], bracket_depths[idx + 1]
            if x1 == x0:
                return float((z0 + z1) / 2.0)
            return float(z0 + (target - x0) / (x1 - x0) * (z1 - z0))

        idx_10 = find_crossing(0.1)
        idx_90 = find_crossing(0.9)

        depth_10 = interp_depth(0.1, idx_10) if idx_10 != -1 else np.nan
        depth_90 = interp_depth(0.9, idx_90) if idx_90 != -1 else np.nan

        # Validate that both crossings belong to the same transition
        if not np.isnan(depth_10) and not np.isnan(depth_90):
            if depth_90 <= depth_10:
                return np.nan, np.nan, np.nan
            midpoint = 0.5 * (depth_10 + depth_90)
            if abs(midpoint - rxn_depth) > search_window:
                return np.nan, np.nan, np.nan
            width = abs(depth_90 - depth_10)
            trans_depth = depth_90
        else:
            # Fallback: only one crossing found
            valid_idx = idx_10 if not np.isnan(depth_10) else idx_90
            valid_depth = depth_10 if not np.isnan(depth_10) else depth_90

            if valid_idx == -1:
                return np.nan, np.nan, np.nan

            dz_local = depths[lo + valid_idx + 1] - depths[lo + valid_idx] if lo + valid_idx < len(depths) - 1 else dz_min
            width = float(abs(dz_local)) if dz_local > 0 else dz_min
            trans_depth = valid_depth

        displacement = trans_depth - rxn_depth
        return trans_depth, displacement, width

    @staticmethod
    def _fill_gaps(values: np.ndarray) -> np.ndarray:
        """
        Replace missing samples by carrying the nearest valid value.

        Slices without mesh nodes leave gaps in the depth profile; carrying the previous value
        keeps the profile monotone through them instead of breaking the crossing search.
        """
        filled = values.copy()
        valid = np.isfinite(filled)
        if not valid.any():
            return filled
        indices = np.arange(filled.size)
        filled[~valid] = np.interp(indices[~valid], indices[valid], filled[valid])
        return filled

    def _repair_monotonic(
        self,
        values: np.ndarray,
        depths: np.ndarray,
        rxn_depth: float,
        search_window: float = 100e3,
        bounds: tuple[int, int] | None = None,
    ) -> np.ndarray:
        """
        Smooth out dips in a phase fraction profile near a known transition depth.

        Only points within search_window of rxn_depth are touched. Dips are
        pooled with their neighbors and replaced by the pool mean, so a
        rising phase fraction passes through unchanged and only local dips
        are flattened. Points outside the window are ignored, keeping mesh
        noise elsewhere in the depth column out of the repair.

        Args:
            values:        Phase fraction array (expected to be broadly 0 -> 1).
            depths:        Depth array (m), sorted ascending, aligned with values.
            rxn_depth:     Nominal reaction depth (m) used to center the search window.
            search_window: Half-width (m) of the depth window around rxn_depth. Default 100 km.
            bounds:        Optional (lo, hi) index range to repair, overriding the search window.

        Returns:
            Array with monotonicity enforced within the search window.
        """
        repaired = values.astype(float).copy()

        if bounds is None:
            window_mask = np.where((depths >= rxn_depth - search_window) & (depths <= rxn_depth + search_window))[0]
            if window_mask.size == 0:
                return repaired
            lo, hi = int(window_mask[0]), int(window_mask[-1])
        else:
            lo, hi = int(bounds[0]), int(bounds[1])

        n_local = hi - lo + 1

        # Both lists use local indices (0..n_local-1) throughout
        block_start = list(range(n_local))
        block_end = list(range(n_local))

        def full(local: int) -> int:
            return lo + local

        i = 0
        while i < n_local - 1:
            if repaired[full(i)] > repaired[full(i + 1)]:
                start = block_start[i]  # local index
                end = block_end[i + 1]  # local index

                block_mean = float(np.mean(repaired[full(start) : full(end) + 1]))
                repaired[full(start) : full(end) + 1] = block_mean

                for k in range(start, end + 1):  # all local
                    block_start[k] = start
                    block_end[k] = end

                i = max(0, start - 1)
            else:
                i += 1

        return repaired
