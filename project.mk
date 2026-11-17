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

BARKLA2_ROOT       := /users/kersweb/scratch/kerswell_et_al_nonhydrostatic_benchmarks
BARKLA2_SIMULATION := $(BARKLA2_ROOT)/simulation

# --------------------------------------------------
# Suites and outputs (can edit)
# --------------------------------------------------
ASPECT_RESULTS    := $(SIMULATION)/results
POSTPROCESS_MODE  := full
POSTPROCESS_VERBOSITY := 0
SAVE_CSV          := true
FORCE_REPROCESS   := false
FORCE_REWRITE     := true
RESULTS_BOX_SUITE  = $(addprefix $(ASPECT_RESULTS)/,$(UIDS_BOX_SUITE))
RESULTS_SINK_SUITE = $(addprefix $(ASPECT_RESULTS)/,$(UIDS_SINK_SUITE))
# Plot sets (paper matrix + laptop check) selected from the registered UIDs.
PLOT_BOX_RUNS    = $(filter %_Res5_CFL7e-01_End1e7,$(UIDS_BOX_SUITE))
PLOT_SINK_RUNS   = $(filter %_Res6_CFL5e-01_End5e6,$(UIDS_SINK_SUITE))
PLOT_LAPTOP_RUNS = $(filter %_End2e6,$(UIDS_SINK_SUITE))
# All Barkla NH runs write 21 outputs (0-20). Sync init + crossing + peak + last.
TIMESTEPS_SYNC   := 000 002 004 006 008 012 016 019 020
FORCE_SYNC       := 0
FORCE_COMPOSE    := 0
FORCE_DOWNLOAD   := 0
ZENODO_DATASET_DOI := TODO-no-dataset-yet
ZENODO_FILES       := TODO-no-files-yet
# -1 = last output per model (output counts vary: full 21, laptop 9, test 5).
TIMESTEPS_MESH_BOX_SUITE  := -1
TIMESTEPS_MESH_SINK_SUITE := -1
CHUNK_SIZE := 32

TAG_BOX_SUITE  := box
TAG_SINK_SUITE := sink
FIGS_BOX_SUITE     := $(FIGS)/box_suite
FIGS_SINK_SUITE    := $(FIGS)/sink_suite
FIGS_SIM_BOX_SUITE  := $(FIGS_BOX_SUITE)/simulation
FIGS_SIM_SINK_SUITE := $(FIGS_SINK_SUITE)/simulation

FIGS_SIMULATION := $(FIGS)/simulation
FIGS_STRUCTURE  := $(FIGS)/structure
FIGS_SEISMIC    := $(FIGS)/seismic
FIGS_SETUP      := $(FIGS)/setup
FIGS_KUBO       := $(FIGS)/kubo
# All generated outputs live under results (ASPECT runs + mesh/postprocess
# products); data holds required versioned inputs only.
POSTPROCESSED_CSV := $(ASPECT_RESULTS)/postprocessed.csv
POSTPROCESSED_MD   := $(ASPECT_RESULTS)/postprocessed.md

PERPLEX_MODELS  := $(shell find $(PERPLEX) -type f -name '*.dat' -exec basename {} .dat \;)
# Versioned thermodynamic inputs (tracked) live alongside generated outputs in
# SIMULATION/data; deep-clean and .gitignore spare exactly these files.
VERSIONED_DATA := olivine-wadsleyite-profile-Mg100.tsv wadsleyite-ringwoodite-profile-Mg100.tsv ringwoodite-postspinel-profile-Mg100.tsv
MESH_CSV_BOX_SUITE  := $(ASPECT_RESULTS)/structure-summary-box.csv
MESH_CSV_SINK_SUITE := $(ASPECT_RESULTS)/structure-summary-sink.csv
SEISMIC_BOX_SUITE   := $(ASPECT_RESULTS)/seismic_profiles_box
SEISMIC_SINK_SUITE  := $(ASPECT_RESULTS)/seismic_profiles_sink

DATA_MESH_BOX_SUITE  := $(addprefix $(ASPECT_RESULTS)/,structure-summary-box.csv structure-cache-box.pkl seismic-profile-cache-box.pkl seismic_profiles_box)
DATA_MESH_SINK_SUITE := $(addprefix $(ASPECT_RESULTS)/,structure-summary-sink.csv structure-cache-sink.pkl seismic-profile-cache-sink.pkl seismic_profiles_sink)

# NH reference UIDs (paper matrix). NH_{Box,Sink}_Dynp{0|1}_Damp{..}[_Block{b}]
# _Z{z}_Res{r}_CFL{c}_End{e}. Dynp0+DampNone = no-feedback equilibrium ground
# truth; Dynp1+DampNone = undamped spurious-wave demonstrator. Kinds: none,
# Bimpl (implicit bulk zeta), Bexpl (explicit bulk zeta), Rel (relaxation
# time s), Cap (pressure cap Pa). Must match simulation/local.mk.
ID_B1 := NH_Box_Dynp1_DampNone_Z4.44e-04_Res5_CFL7e-01_End1e7
ID_B2 := NH_Box_Dynp0_DampNone_Z4.44e-04_Res5_CFL7e-01_End1e7
ID_B3 := NH_Box_Dynp1_DampBimpl1e21_Z4.44e-04_Res5_CFL7e-01_End1e7
ID_B4 := NH_Box_Dynp1_DampBexpl1e20_Z4.44e-04_Res5_CFL7e-01_End1e7
ID_B5 := NH_Box_Dynp1_DampRel3.156e12_Z4.44e-04_Res5_CFL7e-01_End1e7
ID_B6 := NH_Box_Dynp1_DampCap1e7_Z4.44e-04_Res5_CFL7e-01_End1e7

ID_S1 := NH_Sink_Dynp1_DampNone_Block400_Z4.44e-04_Res6_CFL5e-01_End5e6
ID_S2 := NH_Sink_Dynp0_DampNone_Block400_Z4.44e-04_Res6_CFL5e-01_End5e6
ID_S3 := NH_Sink_Dynp1_DampBimpl1e19_Block400_Z4.44e-04_Res6_CFL5e-01_End5e6
ID_S4 := NH_Sink_Dynp1_DampBimpl1e20_Block400_Z4.44e-04_Res6_CFL5e-01_End5e6
ID_S5 := NH_Sink_Dynp1_DampBexpl1e19_Block400_Z4.44e-04_Res6_CFL5e-01_End5e6
ID_S6 := NH_Sink_Dynp1_DampRel3.156e10_Block400_Z4.44e-04_Res6_CFL5e-01_End5e6
ID_S7 := NH_Sink_Dynp1_DampRel3.156e11_Block400_Z4.44e-04_Res6_CFL5e-01_End5e6
ID_S8 := NH_Sink_Dynp1_DampCap2e8_Block400_Z4.44e-04_Res6_CFL5e-01_End5e6

# Local-only smoke/config tests, not paper results. Must match local.mk.
ID_STEST    := NH_Sink_Dynp1_DampNone_Block400_Z4.44e-04_Res4_CFL5e-01_End1e6
ID_SNOBLOCK := NH_Sink_Dynp1_DampNone_Block0_Z4.44e-04_Res4_CFL5e-01_End1e6

# Visualization scope (can edit)
VIS_ALL            := false
VIS_ALL_BOX_SUITE  := $(VIS_ALL)
VIS_ALL_SINK_SUITE := $(VIS_ALL)

VIS_ON := true yes 1

VIS_IDS_BOX_SUITE  := $(ID_B1) $(ID_B2) $(ID_B3) $(ID_B4) $(ID_B5) $(ID_B6)
VIS_IDS_SINK_SUITE := $(ID_S1) $(ID_S2) $(ID_S3) $(ID_S4) $(ID_S5) $(ID_S6) $(ID_S7) $(ID_S8) $(ID_STEST) $(ID_SNOBLOCK)

VIS_MODELS_BOX_SUITE  = $(if $(filter $(VIS_ON),$(VIS_ALL_BOX_SUITE)),$(notdir $(RESULTS_BOX_SUITE)),$(VIS_IDS_BOX_SUITE))
VIS_MODELS_SINK_SUITE = $(if $(filter $(VIS_ON),$(VIS_ALL_SINK_SUITE)),$(notdir $(RESULTS_SINK_SUITE)),$(VIS_IDS_SINK_SUITE))

# --------------------------------------------------
# Model parameters (can edit)
# --------------------------------------------------
SURFACE_TEMPERATURE := 1706
SURFACE_PRESSURE    := 2e+09
SOLVER_TOLERANCE    := 1e-04
MAX_SOLVER_ITER     := 100
MAX_SOLVER_TSTEP    := 25e+03
CHECKPOINT_TIME     := 300
MG_NUM              := 100

# Output cadence per benchmark (end time rides in the UID; end/viz = 21 outputs).
VIZ_OUT_BOX_SUITE  := 5e+05
VIZ_OUT_SINK_SUITE := 2.5e+05

# Kinetic prefactors (ReactionChain N=1, SI 1/s/K). Matrix runs Z_KIN.
# The later Z sweep spans the 660 ol pair and the pre-scaled 410 ol pair
# (410-repo sweep ends 3.0e0/7.0e7 divided by 3.154e7 s/yr: that plugin
# divides its rate by time_scale, ours does not). 520 values still needed.
Z_660_SLUGGISH_OL := 4.44e-04
Z_660_NOMINAL_OL  := 1.4e+04
Z_410_SLUGGISH_OL := 9.51e-08
Z_410_NOMINAL_OL  := 2.22e+00
Z_KIN := $(Z_660_SLUGGISH_OL)
H_KIN := 274e+03
V_KIN := 3.3e-06

ETA_REF   := 1e+21
ETA_MIN   := 1e+19
ETA_MAX   := 1e+24
ETA_GIBBS := 1e+03

DEPTH_CORRECTION_OL_WD := 5e+03
DEPTH_CORRECTION_WD_RI := 5e+03
DEPTH_CORRECTION_RI_PS := 15e+03

# Init-step model-Y at the profile equilibrium (359.2 km depth); loaded front
# measures ~375 km and mesh/R display adds +5 km (364.2 km band).
TRANSITION_Y_OL_WD := 6.408e+05

MODEL_WIDTH_BOX  := 300e+03
MODEL_HEIGHT_BOX := 1000e+03
MESH_X_BOX       := 1
MESH_Y_BOX       := 4

MODEL_WIDTH_SINK  := 1000e+03
MODEL_HEIGHT_SINK := 1000e+03
MESH_X_SINK       := 2
MESH_Y_SINK       := 2
BLOCK_EXCESS      := 400.0

# --------------------------------------------------
# Environment (no edits)
# --------------------------------------------------
CONDA_ENV    := kerswell-et-al-nonhydrostatic-benchmarks
CONDA_PYTHON := $(shell conda run -n $(CONDA_ENV) which python 2>/dev/null || echo python3)

# --------------------------------------------------
# Macros (no edits)
# --------------------------------------------------
# NH_Box_Dynp{d}_Damp{kind+val}_Z{z}_Res{r}_CFL{c}_End{e}; sink inserts
# _Block{b} after the damping token. DampNone has no value suffix.
define MAKE_UID_BOX
  NH_Box_Dynp$(1)_Damp$(if $(filter none,$(2)),None,$(2)$(3))_Z$(4)_Res$(5)_CFL$(6)_End$(7)
endef

define MAKE_UID_SINK
  NH_Sink_Dynp$(1)_Damp$(if $(filter none,$(2)),None,$(2)$(3))_Block$(4)_Z$(5)_Res$(6)_CFL$(7)_End$(8)
endef

define REGISTER_NH_BOX
  $(eval _uid := $(strip $(call MAKE_UID_BOX,$(2),$(3),$(4),$(5),$(6),$(7),$(8))))
  $(1)                       += $(_uid)
  PARAM_suite_$(_uid)    := box
  PARAM_dynp_$(_uid)     := $(2)
  PARAM_dampkind_$(_uid) := $(3)
  PARAM_dampval_$(_uid)  := $(4)
  PARAM_z_$(_uid)        := $(5)
  PARAM_res_$(_uid)      := $(6)
  PARAM_cfl_$(_uid)      := $(7)
  PARAM_end_$(_uid)      := $(8)
endef

define REGISTER_NH_SINK
  $(eval _uid := $(strip $(call MAKE_UID_SINK,$(2),$(3),$(4),$(5),$(6),$(7),$(8),$(9))))
  $(1)                       += $(_uid)
  PARAM_suite_$(_uid)    := sink
  PARAM_dynp_$(_uid)     := $(2)
  PARAM_dampkind_$(_uid) := $(3)
  PARAM_dampval_$(_uid)  := $(4)
  PARAM_block_$(_uid)    := $(5)
  PARAM_z_$(_uid)        := $(6)
  PARAM_res_$(_uid)      := $(7)
  PARAM_cfl_$(_uid)      := $(8)
  PARAM_end_$(_uid)      := $(9)
endef

define GENERATE_NH_PRM
	$(call LOG_ARTIFACT,$(3))
	@mkdir -p $(dir $(3))
	@$(CONDA_PYTHON) $(PYTHON)/simulation/params/generator.py $(1) $(3) \
	  "end-time=$(PARAM_end_$(2))" \
	  "surface-temperature=$(SURFACE_TEMPERATURE)" \
	  "surface-pressure=$(SURFACE_PRESSURE)" \
	  "solver-tolerance=$(SOLVER_TOLERANCE)" \
	  "max-solver-iter=$(MAX_SOLVER_ITER)" \
	  "max-solver-tstep=$(MAX_SOLVER_TSTEP)" \
	  "cfl=$(PARAM_cfl_$(2))" \
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
	  "block-expr=$(if $(filter sink,$(PARAM_suite_$(2))),$(if $(filter 0,$(PARAM_block_$(2))),0,(x>4.25e+05 && x<5.75e+05 && y>7.25e+05 && y<8.75e+05) ? 1 : 0),0)" \
	  "mg-num=$(MG_NUM)" \
	  "transition-ol-wd=$(TRANSITION_Y_OL_WD)" \
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
