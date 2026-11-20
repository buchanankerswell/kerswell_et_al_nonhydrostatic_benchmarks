from dataclasses import dataclass
from typing import Callable, ClassVar

import numpy as np
import pyvista as pv
from utils.logging import log_warn


# Ambient-reference block-load correction (must match BLOCK_Y_TOP/BLOCK_Y_BOT
# and GRAVITY in project.mk). The 1D adiabatic reference includes the initial
# block weight, so ambient-referenced driving pressure adds the static load
# back below the block column. Box runs have no block field and are unaffected.
AMBIENT_BLOCK_TOP_Y = 875e3
AMBIENT_BLOCK_BOT_Y = 725e3
AMBIENT_GRAVITY = 9.81


@dataclass
class MeshPreProcessor:
    verbosity: int = 0

    # Derived field recipes: field_name -> (required_source_fields, compute_fn)
    _DERIVED_FIELDS: ClassVar[dict[str, tuple[tuple[str, ...], Callable]]] = {
        "nonadiabatic_density": (
            ("density", "adiabatic_density"),
            lambda m: m["density"] - m["adiabatic_density"],
        ),
        "nonadiabatic_temperature": (
            ("T", "adiabatic_temperature"),
            lambda m: m["T"] - m["adiabatic_temperature"],
        ),
        "nonadiabatic_pressure": (
            ("p", "adiabatic_pressure"),
            lambda m: m["p"] - m["adiabatic_pressure"],
        ),
        "velocity_vertical": (
            ("velocity",),
            lambda m: m["velocity"][:, 1],
        ),
    }

    def prepare_mesh(self, mesh: pv.UnstructuredGrid, field: str, model_id: str = "") -> None:
        """Derive computed fields from raw mesh data where required source fields are present."""
        if field not in self._DERIVED_FIELDS:
            return

        required, compute = self._DERIVED_FIELDS[field]
        if all(r in mesh.point_data for r in required):
            mesh[field] = compute(mesh)
        elif self.verbosity >= 1:
            missing = [r for r in required if r not in mesh.point_data]
            log_warn(f"cannot derive '{field}', missing source fields: {missing}")
            return

        if field in ("nonadiabatic_pressure", "nonadiabatic_density") and "block" in mesh.point_data:
            self._apply_ambient_correction(mesh, field, model_id)

    def _apply_ambient_correction(self, mesh: pv.UnstructuredGrid, field: str, model_id: str) -> None:
        """Add the static block load back so sink tiles show ambient-referenced driver."""
        import re

        m = re.search(r"Block(\d+)", model_id)
        excess = float(m.group(1)) if m else 0.0
        if not excess:
            return
        y = np.asarray(mesh.points[:, 1])
        if field == "nonadiabatic_pressure":
            overlap = np.where(
                y < AMBIENT_BLOCK_BOT_Y,
                AMBIENT_BLOCK_TOP_Y - AMBIENT_BLOCK_BOT_Y,
                np.where(y < AMBIENT_BLOCK_TOP_Y, y - AMBIENT_BLOCK_BOT_Y, 0.0),
            )
            mesh[field] = np.asarray(mesh[field]) + excess * AMBIENT_GRAVITY * overlap
        else:
            in_block = (y >= AMBIENT_BLOCK_BOT_Y) & (y <= AMBIENT_BLOCK_TOP_Y)
            mesh[field] = np.asarray(mesh[field]) + excess * in_block

    def check_mesh(self, mesh: pv.UnstructuredGrid, field: str) -> bool:
        """Return True if field is present in mesh point data after preparation."""
        return field in mesh.point_data

    def get_mesh_time_myr(self, mesh: pv.UnstructuredGrid, model_id: str, tstep: int) -> float:
        """Extract simulation time in Myr from mesh field data."""
        if "TIME" in mesh.field_data:
            return float(mesh.field_data["TIME"][0]) / 1e6  # seconds → Myr
        if self.verbosity >= 1:
            log_warn(f"'TIME' not found in field_data for model {model_id}, timestep {tstep}.")
        return 0.0
