# --------------------------------------------------
# Paths (no edits)
# --------------------------------------------------
PROJECT_ROOT := $(realpath $(dir $(lastword $(MAKEFILE_LIST)))/.)
export PROJECT_ROOT

ASPECT     := $(PROJECT_ROOT)/aspect
DEALII     := $(PROJECT_ROOT)/dealii
BASH       := $(PROJECT_ROOT)/bash
DRAFT      := $(PROJECT_ROOT)/draft
PYTHON     := $(PROJECT_ROOT)/python
R          := $(PROJECT_ROOT)/R
SIMULATION := $(PROJECT_ROOT)/simulation
FIGS       := $(PROJECT_ROOT)/figs
PERPLEX    := $(PROJECT_ROOT)/perplex

BARKLA2_SIMULATION := /users/kersweb/scratch/kerswell_et_al_nonhydrostatic_benchmarks/simulation

# --------------------------------------------------
# Suites and outputs (can edit)
# --------------------------------------------------
ASPECT_RESULTS        := $(SIMULATION)/results
POSTPROCESS_MODE      := full
POSTPROCESS_VERBOSITY := 0
SAVE_CSV              := true
FORCE_REPROCESS       := false
FORCE_REWRITE         := true
# Recursive (=): expands after local.mk registers UIDS_* below.
RESULTS_SINK_SUITE = $(addprefix $(ASPECT_RESULTS)/,$(UIDS_SINK_SUITE))
# Plot list (main Z_MID runs) selected from the registered UIDs.
PLOT_SINK_RUNS   = $(filter %_Z$(Z_MID)_Res6,$(UIDS_SINK_SUITE))
# One step list for sync + mesh: all 21 run outputs so time-history
# figures draw full-resolution curves.
TIMESTEPS := 000 001 002 003 004 005 006 007 008 009 010 011 012 013 014 015 016 017 018 019 020
# Mesh render steps (subset of TIMESTEPS). Postprocessing always covers all
# synced outputs; only the mesh plots are selective. Test with e.g.
# make postprocess MESH_TIMESTEPS="004 006 008". Manuscript runs use all.
MESH_TIMESTEPS ?= $(TIMESTEPS)
FORCE_DOWNLOAD := 0
ZENODO_DATASET_DOI := TODO-no-dataset-yet
ZENODO_FILES       := TODO-no-files-yet
# Models per worker process. PyVista/VTK leaks memory per rendered mesh
# on macOS, so keep this small enough that one chunk fits in RAM.
CHUNK_SIZE := 6

TAG_SINK_SUITE  := sink
FIGS_SINK_SUITE     := $(FIGS)/sink_suite
FIGS_SIM_SINK_SUITE := $(FIGS_SINK_SUITE)/simulation

FIGS_SIMULATION := $(FIGS)/simulation
FIGS_STRUCTURE  := $(FIGS)/structure
FIGS_SEISMIC    := $(FIGS)/seismic
FIGS_SETUP      := $(FIGS)/setup
# All generated outputs live under results (ASPECT runs + mesh/postprocess
# products); data holds required versioned inputs only.
POSTPROCESSED_CSV := $(ASPECT_RESULTS)/postprocessed.csv
POSTPROCESSED_MD   := $(ASPECT_RESULTS)/postprocessed.md

PERPLEX_MODELS  := $(shell find $(PERPLEX) -type f -name '*.dat' -exec basename {} .dat \;)
# Versioned thermodynamic inputs (tracked) live alongside generated outputs in
# SIMULATION/data; deep-clean and .gitignore spare exactly these files.
VERSIONED_DATA := olivine-wadsleyite-profile-Mg100.tsv wadsleyite-ringwoodite-profile-Mg100.tsv ringwoodite-postspinel-profile-Mg100.tsv depth-datum.tsv
MESH_CSV_SINK_SUITE  := $(ASPECT_RESULTS)/structure-summary-sink.csv
SEISMIC_SINK_SUITE  := $(ASPECT_RESULTS)/seismic_profiles_sink

DATA_MESH_SINK_SUITE := $(addprefix $(ASPECT_RESULTS)/,structure-summary-sink.csv structure-cache-sink.pkl seismic-profile-cache-sink.pkl seismic_profiles_sink)

ID_S1 := NH_Sink_DynpOn_DampNone_Block400_Z4.44e-04_Res6
ID_S2 := NH_Sink_DynpOff_DampNone_Block400_Z4.44e-04_Res6
ID_S3 := NH_Sink_DynpOn_DampBimpl1e19_Block400_Z4.44e-04_Res6
ID_S4 := NH_Sink_DynpOn_DampBimpl1e20_Block400_Z4.44e-04_Res6
ID_S5 := NH_Sink_DynpOn_DampBexpl1e19_Block400_Z4.44e-04_Res6
ID_S6 := NH_Sink_DynpOn_DampRel3.156e10_Block400_Z4.44e-04_Res6
ID_S7 := NH_Sink_DynpOn_DampRel3.156e11_Block400_Z4.44e-04_Res6
ID_S8 := NH_Sink_DynpOn_DampCap2e8_Block400_Z4.44e-04_Res6

# Sink timestep scaling: undamped Res6 at double CFL (0.5 is ID_S1).
# The halved-CFL twin (CFL0.25) is dropped: it blows up deterministically
# in the initial transient (t ~ 1e5 yr, velocity 0.09 -> 22 m/yr, then
# ASPECT aborts on negative density*c_P), while CFL0.5 and CFL1.0 run clean.
ID_SCFL10 := NH_Sink_DynpOn_DampNone_Block400_Z4.44e-04_Res6_CFL1.0

# Batch A: relaxed-pressure taus in the resolvable window plus CFL0.25
# rescue twins (damped only; the undamped CFL0.25 blowup is the stability
# test these must survive). ARKODE floor: the p_rel transient (~7x tau)
# must span several reaction substeps of hmin = 1e-6 x dt (~6.5 yr), so
# tau lives in years-scale [10 yr, 100 kyr]; sub-year taus stall the
# reaction solve at step 1 (mxstep). S6/S7 already cover 1/10 kyr.
ID_S9  := NH_Sink_DynpOn_DampRel3.156e8_Block400_Z4.44e-04_Res6
ID_S10 := NH_Sink_DynpOn_DampRel3.156e9_Block400_Z4.44e-04_Res6
ID_S11 := NH_Sink_DynpOn_DampRel3.156e12_Block400_Z4.44e-04_Res6
ID_S12 := NH_Sink_DynpOn_DampCap2e8_Block400_Z4.44e-04_Res6_CFL0.25
ID_S13 := NH_Sink_DynpOn_DampBimpl1e19_Block400_Z4.44e-04_Res6_CFL0.25
ID_S14 := NH_Sink_DynpOn_DampRel3.156e11_Block400_Z4.44e-04_Res6_CFL0.25

# Batch B: bulk and cap sensitivity at Res6, suite CFL.
ID_S15 := NH_Sink_DynpOn_DampBimpl1e18_Block400_Z4.44e-04_Res6
ID_S16 := NH_Sink_DynpOn_DampBexpl1e20_Block400_Z4.44e-04_Res6
ID_S17 := NH_Sink_DynpOn_DampCap1e8_Block400_Z4.44e-04_Res6
ID_S18 := NH_Sink_DynpOn_DampCap4e8_Block400_Z4.44e-04_Res6

# Batch C: mesh scaling. Res7 puts ~2 cells across the ~3.5 km front
# (0.9 dx at Res6); Res5 is the coarse anchor. The Res7 relaxed run uses
# the proven 10 kyr tau; swap it for the A winner before submitting C.
ID_S19 := NH_Sink_DynpOn_DampNone_Block400_Z4.44e-04_Res7
ID_S20 := NH_Sink_DynpOn_DampCap2e8_Block400_Z4.44e-04_Res7
ID_S21 := NH_Sink_DynpOn_DampRel3.156e11_Block400_Z4.44e-04_Res7
ID_S22 := NH_Sink_DynpOn_DampBimpl1e19_Block400_Z4.44e-04_Res7
ID_S23 := NH_Sink_DynpOn_DampNone_Block400_Z4.44e-04_Res5
ID_S24 := NH_Sink_DynpOn_DampCap2e8_Block400_Z4.44e-04_Res5

# Visualization scope (can edit)
VIS_ALL            := false
VIS_ALL_SINK_SUITE := $(VIS_ALL)

# Figure resolution (dots per inch). Draft/test value 100 keeps file
# sizes small; set 330 for final manuscript figures.
FIG_DPI := 100

VIS_ON := true yes 1

VIS_IDS_SINK_SUITE := $(ID_S1) $(ID_S2) $(ID_S3) $(ID_S4) $(ID_S5) $(ID_S6) $(ID_S7) $(ID_S8) $(ID_SCFL10) \
  $(ID_S9) $(ID_S10) $(ID_S11) $(ID_S12) $(ID_S13) $(ID_S14) \
  $(ID_S15) $(ID_S16) $(ID_S17) $(ID_S18) \
  $(ID_S19) $(ID_S20) $(ID_S21) $(ID_S22) $(ID_S23) $(ID_S24)

# Recursive (=): expands after local.mk registers UIDS_*/Z_MID above.
VIS_MODELS_SINK_SUITE = $(if $(filter $(VIS_ON),$(VIS_ALL_SINK_SUITE)),$(notdir $(RESULTS_SINK_SUITE)),$(VIS_IDS_SINK_SUITE))

# --------------------------------------------------
# Runtime constants (can edit). Units: temperatures (K), pressures (Pa),
# lengths (m), kinetic rates (1/s/K), enthalpies (J/mol), volumes (m^3/mol),
# viscosities (Pa s), densities (kg/m^3); CFL numbers, iteration counts,
# Mg#, and mesh counts are dimensionless. Model-time inputs (end time,
# output cadence, solver caps) are in years: ASPECT converts them to seconds
# internally (`Use years instead of seconds`). Relaxation times stay SI
# seconds (plugin-side, no conversion). Figure scripts rescale to geologic
# units at plot time (see config.py).
# --------------------------------------------------
SURFACE_TEMPERATURE := 1706
SURFACE_PRESSURE    := 2e09
SOLVER_TOLERANCE    := 1e-04
MAX_SOLVER_ITER     := 100
MAX_SOLVER_TSTEP    := 25e03
CHECKPOINT_TIME     := 300
MG_NUM              := 100

# Output cadence (yr, model time; 21 run outputs each: end / viz-out = 20).
VIZ_OUT_SINK_SUITE := 2.5e05

# End time (yr, model time; UIDs carry no End token). Long enough to
# cover pressure-rise onset, saturation, and block bottoming.
END_SINK := 5e06

# Fixed solver settings (outside the parameter sweep, so absent from UIDs).
# CFL 0.5 proved low-sensitivity (sink timing-only).
# Gravity everywhere (m/s^2): matches the PerpleX profile construction, the
# postprocessing thermal split, and the ASPECT default.
CFL_SINK := 0.5
GRAVITY  := 9.81

# Ambient hydrostatic reference (can edit). The 1D adiabatic profile is
# integrated down a column through the initial block, adding ~589 MPa of
# block weight into P_ref; the plugin subtracts that static load when
# AMBIENT_REF is true so kinetics see ambient mantle.
# Geometry (m) must match {block-expr} below.
AMBIENT_REF := true
BLOCK_Y_TOP := 875e03
BLOCK_Y_BOT := 725e03

# Kinetic prefactor (ReactionChain N=1, SI 1/s/K). Only Z_MID runs in the
# minimal set; Z_LO/Z_HI stay defined for later resolution-rate studies.
Z_660_SLUGGISH_OL := 4.44e-04
Z_660_NOMINAL_OL  := 1.4e+04
Z_410_SLUGGISH_OL := 9.51e-08
Z_KIN := $(Z_660_SLUGGISH_OL)
H_KIN := 274e03
V_KIN := 3.3e-06

# Kinetic-rate anchors: sluggish (410-like), intermediate (current Z_KIN),
# quasi-equilibrium (660-nominal, near-instantaneous).
Z_LO  := $(Z_410_SLUGGISH_OL)
Z_MID := $(Z_KIN)
Z_HI  := $(Z_660_NOMINAL_OL)

ETA_REF   := 1e21
ETA_MIN   := 1e19
ETA_MAX   := 1e24
ETA_GIBBS := 1e03

# Depth correction (m).
DEPTH_CORRECTION_OL_WD := 5e03

# Reference density (kg/m^3) for the postprocessed thermal split of the
# measured 410 displacement into thermal offset and kinetic contribution.
REF_DENSITY := 4100.0

# Init-step model-Y (m) at the profile equilibrium. The runtime adiabat puts the
# same equilibrium pressure deeper, so all runs relax from the init step
# within ~0.1 Ma; final states are unaffected.
TRANSITION_Y_OL_WD := 6.408e05

# Model depth (m) where ASPECT pressure equals the profile equilibrium
# (14.324 GPa). Re-derived under g = 9.81 as dG = 0 on the Barkla2
# no-feedback twin (static across all 21 outputs): S2 at 379957 m.
NOMINAL_410_SINK400 := 379957
# Profile-reference 410 in true depth (profile dG = 0 at 422554 m).
PROFILE_REF_410_M := 422600

# Fixed vertical line the suite is sampled along (m): sink block
# center. The suite is isothermal, so there is no hotspot to follow.
TRACE_X_SINK := 500e03

# Probe points (x, y in metres of model height; y = 1e6 - depth). Baked
# into finished runs; do not move.
POINTS_SINK := 5.0e05, 6.358e05; 5.0e05, 8.00e05

MODEL_WIDTH_SINK  := 1000e03
MODEL_HEIGHT_SINK := 1000e03
MESH_X_SINK       := 2
MESH_Y_SINK       := 2
# Model extents are (m); mesh counts are cells per direction.

# Depth-window figure steps (output numbers, subset of TIMESTEPS).
DEPTH_WINDOW_STEPS := 00000 00002 00006 00012

# Representative-trace guard (m): max x jump between depth slices before
# the trace re-anchors to the strongest anomaly.
TRACE_X_STEP_LIMIT := 150e03

# Adiabat generation (BurnMan isentrope + PerpleX tables backing VERSIONED_DATA).
# Potential temperature (K), resolutions (counts), planet radius (m).
ADIABAT_POTENTIAL_TEMP := 1573.0
ADIABAT_TABLE_RES      := 128
ADIABAT_PROFILE_RES    := 501
PLANET_RADIUS          := 6370e03

# --------------------------------------------------
# Environment (no edits)
# --------------------------------------------------
CONDA_ENV    := kerswell-et-al-nonhydrostatic-benchmarks
CONDA_PYTHON := $(shell conda run -n $(CONDA_ENV) which python 2>/dev/null || echo python3)

# --------------------------------------------------
# Macros (no edits)
# --------------------------------------------------
# UIDs name the benchmark and what varies. Box:
# NH_Box_Dynp{d}_Damp{kind+val}_Z{z}_Res{r}[_CFL{c}]. Sink inserts _Block{b}
# after damping. DampNone has no value. The _CFL part is only present when
# the run uses a timestep different from the suite default. End times and
# default steps are suite constants, so they stay out of UIDs.
define MAKE_UID_BOX
  NH_Box_Dynp$(if $(filter 1,$(1)),On,Off)_Damp$(if $(filter none,$(2)),None,$(2)$(3))_Z$(4)_Res$(5)$(if $(6),_CFL$(6))
endef

define MAKE_UID_SINK
  NH_Sink_Dynp$(if $(filter 1,$(1)),On,Off)_Damp$(if $(filter none,$(2)),None,$(2)$(3))_Block$(4)_Z$(5)_Res$(6)$(if $(7),_CFL$(7))
endef

define REGISTER_NH_BOX
  $(eval _uid := $(strip $(call MAKE_UID_BOX,$(2),$(3),$(4),$(5),$(6),$(7))))
  $(1)                       += $(_uid)
  PARAM_suite_$(_uid)    := box
  PARAM_dynp_$(_uid)     := $(2)
  PARAM_dampkind_$(_uid) := $(3)
  PARAM_dampval_$(_uid)  := $(4)
  PARAM_z_$(_uid)        := $(5)
  PARAM_res_$(_uid)      := $(6)
  PARAM_cfl_$(_uid)      := $(if $(7),$(7),$(CFL_BOX))
  PARAM_points_$(_uid)   := $(POINTS_BOX)
endef

define REGISTER_NH_SINK
  $(eval _uid := $(strip $(call MAKE_UID_SINK,$(2),$(3),$(4),$(5),$(6),$(7),$(8))))
  $(1)                       += $(_uid)
  PARAM_suite_$(_uid)    := sink
  PARAM_dynp_$(_uid)     := $(2)
  PARAM_dampkind_$(_uid) := $(3)
  PARAM_dampval_$(_uid)  := $(4)
  PARAM_block_$(_uid)    := $(5)
  PARAM_z_$(_uid)        := $(6)
  PARAM_res_$(_uid)      := $(7)
  PARAM_cfl_$(_uid)      := $(if $(8),$(8),$(CFL_SINK))
  PARAM_points_$(_uid)   := $(POINTS_SINK)
endef

define GENERATE_NH_PRM
	$(call LOG_ARTIFACT,$(3))
	@mkdir -p $(dir $(3))
	@$(CONDA_PYTHON) $(PYTHON)/simulation/params/generator.py $(1) $(3) \
	  "end-time=$(if $(filter box,$(PARAM_suite_$(2))),$(END_BOX),$(END_SINK))" \
	  "surface-temperature=$(SURFACE_TEMPERATURE)" \
	  "surface-pressure=$(SURFACE_PRESSURE)" \
	  "solver-tolerance=$(SOLVER_TOLERANCE)" \
	  "max-solver-iter=$(MAX_SOLVER_ITER)" \
	  "max-solver-tstep=$(MAX_SOLVER_TSTEP)" \
	  "cfl=$(PARAM_cfl_$(2))" \
	  "gravity=$(GRAVITY)" \
	  "viz-out-time=$(if $(filter box,$(PARAM_suite_$(2))),$(VIZ_OUT_BOX_SUITE),$(VIZ_OUT_SINK_SUITE))" \
	  "checkpoint-time=$(CHECKPOINT_TIME)" \
	  "model-width=$(if $(filter box,$(PARAM_suite_$(2))),$(MODEL_WIDTH_BOX),$(MODEL_WIDTH_SINK))" \
	  "model-height=$(if $(filter box,$(PARAM_suite_$(2))),$(MODEL_HEIGHT_BOX),$(MODEL_HEIGHT_SINK))" \
	  "mesh-x=$(if $(filter box,$(PARAM_suite_$(2))),$(MESH_X_BOX),$(MESH_X_SINK))" \
	  "mesh-y=$(if $(filter box,$(PARAM_suite_$(2))),$(MESH_Y_BOX),$(MESH_Y_SINK))" \
	  "mesh-refine-global=$(PARAM_res_$(2))" \
	  "dynp-density=$(if $(filter 1,$(PARAM_dynp_$(2))),true,false)" \
	  "dynp-gibbs=$(if $(filter 1,$(PARAM_dynp_$(2))),true,false)" \
	  "bulk-enable=$(if $(filter Bimpl,$(PARAM_dampkind_$(2))),true,false)" \
	  "bulk-zeta=$(if $(filter Bimpl,$(PARAM_dampkind_$(2))),$(PARAM_dampval_$(2)),0.0)" \
	  "addrhs-enable=$(if $(filter Bexpl,$(PARAM_dampkind_$(2))),true,false)" \
	  "z-kin=$(PARAM_z_$(2))" \
	  "h-kin=$(H_KIN)" \
	  "v-kin=$(V_KIN)" \
	  "eta-ref=$(ETA_REF)" \
	  "eta-min=$(ETA_MIN)" \
	  "eta-max=$(ETA_MAX)" \
	  "eta-gibbs=$(ETA_GIBBS)" \
	  "relax-time=$(if $(filter Rel,$(PARAM_dampkind_$(2))),$(PARAM_dampval_$(2)),0.0)" \
	  "explicit-zeta=$(if $(filter Bexpl,$(PARAM_dampkind_$(2))),$(PARAM_dampval_$(2)),0.0)" \
	  "max-cap=$(if $(filter Cap,$(PARAM_dampkind_$(2))),$(PARAM_dampval_$(2)),0.0)" \
	  "block-excess=$(if $(filter sink,$(PARAM_suite_$(2))),$(PARAM_block_$(2)).0,0.0)" \
  "ambient-reference=$(AMBIENT_REF)" \
  "block-top-y=$(BLOCK_Y_TOP)" \
  "block-bottom-y=$(BLOCK_Y_BOT)" \
	  "block-expr=$(if $(filter sink,$(PARAM_suite_$(2))),$(if $(filter 0,$(PARAM_block_$(2))),0,(x>4.25e05 && x<5.75e05 && y>7.25e05 && y<8.75e05) ? 1 : 0),0)" \
	  "mg-num=$(MG_NUM)" \
	  "transition-ol-wd=$(TRANSITION_Y_OL_WD)" \
	  "point-values=$(PARAM_points_$(2))" \
	  "output-dir=$(ASPECT_RESULTS)/$(2)" \
	  "config-dir=$(ASPECT_CONFIGS)" \
	  "aspect-plugin=$(SIMULATION)/plugins/build/libnh-kinetics.release.so" \
	  "benchmark-data-dir=$(SIMULATION)/data/" \
	  "uid=$(2)"
endef

# --------------------------------------------------
# Environment checks (no edits)
# --------------------------------------------------
ifeq ($(shell command -v conda 2>/dev/null),)
  $(error !! ERROR: 'conda' not found in PATH)
endif

ifeq ($(shell conda info --envs | grep -q "$(CONDA_ENV)" && echo "exists"),)
  $(warning !! WARNING: Conda environment '$(CONDA_ENV)' not found)
  $(warning !!          Run 'make environments' to set up the workspace)
endif

ifeq ($(shell command -v Rscript 2>/dev/null),)
  $(error !! ERROR: 'Rscript' not found in PATH. This project requires R)
endif

# --------------------------------------------------
# ASPECT and deal.II (only needed for `make models`)
# --------------------------------------------------
UNAME_SHELL := $(shell uname)
OS_SYSTEM   := $(shell [ -f /etc/os-release ] && . /etc/os-release && echo $$ID || echo unknown)

ASPECT_EXE    := $(ASPECT)/aspect-release
DEALII_ENABLE := $(DEALII)/configuration/enable.sh

define CHECK_SIM_DEPS
  $(error !! ERROR: simulation dependencies not found (missing $(1)). Link your installs at the project root as 'aspect/aspect-release' and 'dealii/configuration/enable.sh'. To install from source, see https://github.com/dealii/candi (deal.II >= v9.7.0) and https://github.com/geodynamics/aspect (ASPECT >= 3.1.0))
endef

$(ASPECT_EXE) $(DEALII_ENABLE):
	$(call CHECK_SIM_DEPS,$@)

ifeq ($(UNAME_SHELL), Darwin)
  RUN_ASPECT := $(BASH)/simulation/run-aspect-macos.sh
  NTASKS     := 8
else ifeq ($(OS_SYSTEM), rocky)
  GCC      := gcc/14.2.0
  OPENMPI  := openmpi/5.0.8-gcc14.2.0
  OPENBLAS := openblas/0.3.29/gcc-14.2.0
  CMAKE    := cmake/3.30.5-gcc14.2.0

  RUN_ASPECT    := $(BASH)/simulation/run-aspect-barkla2.sh
  NTASKS        := 128
  NTASKSPERNODE := 168
  TIME          := 2-12:00:00
  MAIL_ADDRESS  := b.kerswell@liverpool.ac.uk
  MAIL_TYPE     := ALL
else
  $(error Unsupported OS: Only macOS and Rocky Linux are supported!)
endif

# --------------------------------------------------
# Logging (no edits)
# --------------------------------------------------
LOG_SH       := $(BASH)/utils/log.sh
LOG_INFO     = @bash -c 'source $(LOG_SH); log_info "$(1)"'
LOG_DETAIL   = @bash -c 'source $(LOG_SH); log_detail "$(1)"'
LOG_ARTIFACT = @bash -c 'source $(LOG_SH); log_artifact "$(1)"'

# --------------------------------------------------
# Safe removal (no edits)
# --------------------------------------------------
define SAFE_RM
	if [ -e "$(1)" ]; then \
	  ABS_PATH=$$(realpath "$(1)"); \
	  if [[ "$$ABS_PATH" == $(PROJECT_ROOT)* ]]; then \
	    log_delete "$$ABS_PATH"; \
	    rm -rf "$$ABS_PATH"; \
	  fi; \
	fi
endef

define SAFE_RM_LIST
	. "$(BASH)/utils/log.sh"; for item in $(1); do $(call SAFE_RM,$$item); done
endef
