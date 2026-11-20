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
RESULTS_BOX_SUITE  = $(addprefix $(ASPECT_RESULTS)/,$(UIDS_BOX_SUITE))
RESULTS_SINK_SUITE = $(addprefix $(ASPECT_RESULTS)/,$(UIDS_SINK_SUITE))
# Plot lists (main Z_MID runs) selected from the registered UIDs.
PLOT_BOX_RUNS    = $(filter %_Z$(Z_MID)_Res5,$(UIDS_BOX_SUITE))
PLOT_SINK_RUNS   = $(filter %_Z$(Z_MID)_Res6,$(UIDS_SINK_SUITE))
# One step list for sync + mesh: all 21 run outputs so time-history
# figures draw full-resolution curves.
TIMESTEPS := 000 001 002 003 004 005 006 007 008 009 010 011 012 013 014 015 016 017 018 019 020
FORCE_DOWNLOAD := 0
ZENODO_DATASET_DOI := TODO-no-dataset-yet
ZENODO_FILES       := TODO-no-files-yet
CHUNK_SIZE := 32

TAG_BOX_SUITE   := box
TAG_SINK_SUITE  := sink
FIGS_BOX_SUITE      := $(FIGS)/box_suite
FIGS_SINK_SUITE     := $(FIGS)/sink_suite
FIGS_SIM_BOX_SUITE  := $(FIGS_BOX_SUITE)/simulation
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
MESH_CSV_BOX_SUITE  := $(ASPECT_RESULTS)/structure-summary-box.csv
MESH_CSV_SINK_SUITE := $(ASPECT_RESULTS)/structure-summary-sink.csv
SEISMIC_BOX_SUITE   := $(ASPECT_RESULTS)/seismic_profiles_box
SEISMIC_SINK_SUITE  := $(ASPECT_RESULTS)/seismic_profiles_sink

DATA_MESH_BOX_SUITE  := $(addprefix $(ASPECT_RESULTS)/,structure-summary-box.csv structure-cache-box.pkl seismic-profile-cache-box.pkl seismic_profiles_box)
DATA_MESH_SINK_SUITE := $(addprefix $(ASPECT_RESULTS)/,structure-summary-sink.csv structure-cache-sink.pkl seismic-profile-cache-sink.pkl seismic_profiles_sink)

# Box main runs: every damping type at Z_MID Res5. DynpOff+DampNone is the
# reference with no feedback; DynpOn+DampNone the run with no damping.
ID_B1 := NH_Box_DynpOn_DampNone_Z4.44e-04_Res5
ID_B2 := NH_Box_DynpOff_DampNone_Z4.44e-04_Res5
ID_B3 := NH_Box_DynpOn_DampBimpl1e21_Z4.44e-04_Res5
ID_B4 := NH_Box_DynpOn_DampBexpl1e20_Z4.44e-04_Res5
ID_B5 := NH_Box_DynpOn_DampRel3.156e12_Z4.44e-04_Res5
ID_B6 := NH_Box_DynpOn_DampCap1e7_Z4.44e-04_Res5

# Box timestep scaling: undamped Res5 at half and double CFL (0.7 is ID_B1).
ID_BCFL035 := NH_Box_DynpOn_DampNone_Z4.44e-04_Res5_CFL0.35
ID_BCFL14 := NH_Box_DynpOn_DampNone_Z4.44e-04_Res5_CFL1.4

ID_S1 := NH_Sink_DynpOn_DampNone_Block400_Z4.44e-04_Res6
ID_S2 := NH_Sink_DynpOff_DampNone_Block400_Z4.44e-04_Res6
ID_S3 := NH_Sink_DynpOn_DampBimpl1e19_Block400_Z4.44e-04_Res6
ID_S4 := NH_Sink_DynpOn_DampBimpl1e20_Block400_Z4.44e-04_Res6
ID_S5 := NH_Sink_DynpOn_DampBexpl1e19_Block400_Z4.44e-04_Res6
ID_S6 := NH_Sink_DynpOn_DampRel3.156e10_Block400_Z4.44e-04_Res6
ID_S7 := NH_Sink_DynpOn_DampRel3.156e11_Block400_Z4.44e-04_Res6
ID_S8 := NH_Sink_DynpOn_DampCap2e8_Block400_Z4.44e-04_Res6

# Sink timestep scaling: undamped Res6 at half and double CFL (0.5 is ID_S1).
ID_SCFL025 := NH_Sink_DynpOn_DampNone_Block400_Z4.44e-04_Res6_CFL0.25
ID_SCFL10 := NH_Sink_DynpOn_DampNone_Block400_Z4.44e-04_Res6_CFL1.0

# Visualization scope (can edit)
VIS_ALL            := false
VIS_ALL_BOX_SUITE  := $(VIS_ALL)
VIS_ALL_SINK_SUITE := $(VIS_ALL)

VIS_ON := true yes 1

VIS_IDS_BOX_SUITE  := $(ID_B1) $(ID_B2) $(ID_B3) $(ID_B4) $(ID_B5) $(ID_B6) $(ID_BCFL035) $(ID_BCFL14)
VIS_IDS_SINK_SUITE := $(ID_S1) $(ID_S2) $(ID_S3) $(ID_S4) $(ID_S5) $(ID_S6) $(ID_S7) $(ID_S8) $(ID_SCFL025) $(ID_SCFL10)

# Recursive (=): expands after local.mk registers UIDS_*/Z_MID above.
VIS_MODELS_BOX_SUITE  = $(if $(filter $(VIS_ON),$(VIS_ALL_BOX_SUITE)),$(notdir $(RESULTS_BOX_SUITE)),$(VIS_IDS_BOX_SUITE))
VIS_MODELS_SINK_SUITE = $(if $(filter $(VIS_ON),$(VIS_ALL_SINK_SUITE)),$(notdir $(RESULTS_SINK_SUITE)),$(VIS_IDS_SINK_SUITE))

# --------------------------------------------------
# Runtime constants (can edit)
# --------------------------------------------------
SURFACE_TEMPERATURE := 1706
SURFACE_PRESSURE    := 2e+09
SOLVER_TOLERANCE    := 1e-04
MAX_SOLVER_ITER     := 100
MAX_SOLVER_TSTEP    := 25e+03
CHECKPOINT_TIME     := 300
MG_NUM              := 100

# Output cadence (21 run outputs each: end / viz-out = 20).
VIZ_OUT_BOX_SUITE  := 5e+05
VIZ_OUT_SINK_SUITE := 2.5e+05

# End times per suite (s, model time; UIDs carry no End token). Long enough
# to cover pressure-rise onset, saturation, and (sink) block bottoming.
END_BOX  := 1e7
END_SINK := 5e6

# Fixed solver settings (outside the parameter sweep, so absent from UIDs).
# CFL 0.7 box / 0.5 sink proved low-sensitivity (box flat, sink timing-only).
# Gravity 9.81 everywhere: matches the PerpleX profile construction, the
# postprocessing thermal split (GRAV), and the ASPECT default.
CFL_BOX  := 7e-01
CFL_SINK := 5e-01
GRAVITY  := 9.81

# Ambient hydrostatic reference (can edit). The 1D adiabatic profile is
# integrated down a column through the initial block, adding ~589 MPa of
# block weight into P_ref; the plugin subtracts that static load when
# AMBIENT_REF is true so kinetics see ambient mantle. Box has no block, so
# the correction is a no-op there. Geometry must match {block-expr} below.
AMBIENT_REF := true
BLOCK_Y_TOP := 875e3
BLOCK_Y_BOT := 725e3

# Kinetic prefactor (ReactionChain N=1, SI 1/s/K). Only Z_MID runs in the
# minimal set; Z_LO/Z_HI stay defined for later resolution-rate studies.
Z_660_SLUGGISH_OL := 4.44e-04
Z_660_NOMINAL_OL  := 1.4e+04
Z_410_SLUGGISH_OL := 9.51e-08
Z_KIN := $(Z_660_SLUGGISH_OL)
H_KIN := 274e+03
V_KIN := 3.3e-06

# Kinetic-rate anchors: sluggish (410-like), intermediate (current Z_KIN),
# quasi-equilibrium (660-nominal, near-instantaneous).
Z_LO  := $(Z_410_SLUGGISH_OL)
Z_MID := $(Z_KIN)
Z_HI  := $(Z_660_NOMINAL_OL)

ETA_REF   := 1e+21
ETA_MIN   := 1e+19
ETA_MAX   := 1e+24
ETA_GIBBS := 1e+03

DEPTH_CORRECTION_OL_WD := 5e+03

# Init-step model-Y at the profile equilibrium. The runtime adiabat puts the
# same equilibrium pressure deeper, so all runs relax from the init step
# within ~0.1 Myr; final states are unaffected.
TRANSITION_Y_OL_WD := 6.408e+05

# Model depth (m) where ASPECT pressure equals the profile equilibrium
# (14.324 GPa). Re-derived under g = 9.81 as dG = 0 on the Barkla2
# no-feedback twins (static across all 21 outputs): B2 at 379943 m,
# S2 at 379957 m. Ambient reference removes the block load, so both
# suites share the same ~380 km adiabat; the 14 m split is mesh noise.
NOMINAL_410_BOX     := 379943
NOMINAL_410_SINK400 := 379957
# Profile-reference 410 in true depth (profile dG = 0 at 422554 m).
PROFILE_REF_410_M := 422600

# Fixed vertical lines each suite is sampled along (m): box center, sink
# block center. Both suites are isothermal, so there is no hotspot to follow.
TRACE_X_BOX  := 150000
TRACE_X_SINK := 500000

# Probe points (x, y in model m; y = 1e6 - depth). Baked into finished
# runs; do not move.
POINTS_BOX  := 1.5e+05, 6.358e+05; 1.5e+05, 4.358e+05
POINTS_SINK := 5.0e+05, 6.358e+05; 5.0e+05, 8.00e+05

MODEL_WIDTH_BOX  := 300e+03
MODEL_HEIGHT_BOX := 1000e+03
MESH_X_BOX       := 1
MESH_Y_BOX       := 4

MODEL_WIDTH_SINK  := 1000e+03
MODEL_HEIGHT_SINK := 1000e+03
MESH_X_SINK       := 2
MESH_Y_SINK       := 2

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
	  "block-expr=$(if $(filter sink,$(PARAM_suite_$(2))),$(if $(filter 0,$(PARAM_block_$(2))),0,(x>4.25e+05 && x<5.75e+05 && y>7.25e+05 && y<8.75e+05) ? 1 : 0),0)" \
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
