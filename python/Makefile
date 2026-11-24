# Set the default goal before includes
.DEFAULT_GOAL := help

# Include definitions
include $(realpath $(dir $(lastword $(MAKEFILE_LIST)))/../project.mk)
include $(SIMULATION)/local.mk

PROFILES          := $(foreach g,$(MG_NUM),$(SIMULATION)/data/olivine-wadsleyite-profile-Mg$(g).tsv)
PYR_TABLE         := $(SIMULATION)/data/PYR-material-table.tab
PYR_ADIABAT       := $(SIMULATION)/data/PYR-adiabatic-profile.tsv
MODELS_SINK_SUITE := $(notdir $(RESULTS_SINK_SUITE))

CLEAN := $(PYTHON)/**/__pycache__ \
	 $(PYTHON)/simulation/**/__pycache__ \
	 $(PYTHON)/setup/**/__pycache__ \
	 $(FIGS)/adiabat \
	 $(FIGS_SETUP) \
	 $(FIGS_SINK_SUITE) \
	 $(FIGS)/benchmarks \
	 $(DATA_MESH_SINK_SUITE) \
	 $(POSTPROCESSED_CSV) \
	 $(SIMULATION)/results/lateral-pressure.csv \
	 $(SIMULATION)/results/pressure-history-summary.csv

.PHONY: all visualize postprocess sync-barkla extract-timeseries timeseries pressure-history-summary pressure-history lateral-oscillation lateral mesh-step-sensitivity scaling depth-window-figures depth-window setup-sketch setup benchmarks adiabat meshes meshes-sink-suite clean help

all: visualize
visualize: adiabat meshes-sink-suite $(POSTPROCESSED_CSV) extract-timeseries setup-sketch benchmarks
postprocess: visualize
benchmarks: pressure-history-summary lateral-oscillation mesh-step-sensitivity depth-window-figures

setup-sketch:
	@PYTHONPATH=$(PYTHON) $(CONDA_PYTHON) -u $(PYTHON)/setup/domains.py --suite sink --width-m $(MODEL_WIDTH_SINK) --height-m $(MODEL_HEIGHT_SINK) \
	  --transition-y-m $(TRANSITION_Y_OL_WD) --trace-x-m $(TRACE_X_SINK) --nominal-m $(NOMINAL_410_SINK400) --probes "$(POINTS_SINK)" --out $(FIGS_SETUP)/sink-domain.png --dpi $(FIG_DPI)

setup: setup-sketch

sync-barkla:
	@$(MAKE) --no-print-directory -C $(BASH) sync-barkla

.PHONY: $(POSTPROCESSED_CSV)
$(POSTPROCESSED_CSV):
	@mkdir -p $(dir $@)
	@PYTHONPATH=$(PYTHON) $(CONDA_PYTHON) -u $(PYTHON)/simulation/mesh/export-postprocessed.py \
	  --data-dir $(SIMULATION)/results \
	  --out-csv $@ \
	  --profile-ol-wd $(SIMULATION)/data/olivine-wadsleyite-profile-Mg$(MG_NUM).tsv \
	  --model-height $(MODEL_HEIGHT_SINK) \
	  --surface-pressure $(SURFACE_PRESSURE) \
	  --depth-corr-ol-wd=$(DEPTH_CORRECTION_OL_WD) \
	  --nominal-410-sink400=$(NOMINAL_410_SINK400) \
	  --gravity=$(GRAVITY) \
	  --ref-density=$(REF_DENSITY) \
	  --force
	$(call LOG_ARTIFACT,$@)

extract-timeseries:
	@for run in $(UIDS_SINK_SUITE); do \
	  PYTHONPATH=$(PYTHON) $(CONDA_PYTHON) -u $(PYTHON)/benchmarks/extract_timeseries.py $(SIMULATION)/results/$$run \
	    --block-top-m=$(BLOCK_Y_TOP) --block-bottom-m=$(BLOCK_Y_BOT) --gravity=$(GRAVITY); \
	done

timeseries: extract-timeseries

pressure-history-summary: extract-timeseries
	@PYTHONPATH=$(PYTHON) $(CONDA_PYTHON) -u $(PYTHON)/benchmarks/summarize_pressure_history.py \
	  --runs $(UIDS_SINK_SUITE) \
	  --plot-sink $(PLOT_SINK_RUNS) \
	  --out-csv $(SIMULATION)/results/pressure-history-summary.csv \
	  --fig-dir $(FIGS)/benchmarks \
	  --dpi $(FIG_DPI)
	@PYTHONPATH=$(PYTHON) $(CONDA_PYTHON) -u $(PYTHON)/benchmarks/plot_depth_profiles.py \
	  --runs $(PLOT_SINK_RUNS) --suite-tag sink --profile $(SIMULATION)/data/olivine-wadsleyite-profile-Mg$(MG_NUM).tsv \
	  --model-height $(MODEL_HEIGHT_SINK) --surface-pressure $(SURFACE_PRESSURE) \
	  --depth-corr-ol-wd=$(DEPTH_CORRECTION_OL_WD) \
	  --nominal-m=$(NOMINAL_410_SINK400) --out $(FIGS)/benchmarks/depth-profiles-sink.png --dpi $(FIG_DPI)
	@PYTHONPATH=$(PYTHON) $(CONDA_PYTHON) -u $(PYTHON)/benchmarks/plot_lateral_profiles.py \
	  --runs $(PLOT_SINK_RUNS) --suite-tag sink --step 00007 --nominal-m=$(NOMINAL_410_SINK400) \
	  --block-top-m=$(BLOCK_Y_TOP) --block-bottom-m=$(BLOCK_Y_BOT) --gravity=$(GRAVITY) \
	  --out $(FIGS)/benchmarks/lateral-profiles-sink.png --dpi $(FIG_DPI)

pressure-history: pressure-history-summary

lateral-oscillation:
	@PYTHONPATH=$(PYTHON) $(CONDA_PYTHON) -u $(PYTHON)/benchmarks/extract_lateral_pressure.py \
	  --models $(UIDS_SINK_SUITE) --nominal-m=$(NOMINAL_410_SINK400) \
	  --block-top-m=$(BLOCK_Y_TOP) --block-bottom-m=$(BLOCK_Y_BOT) --gravity=$(GRAVITY) \
	  --out-csv $(SIMULATION)/results/lateral-pressure.csv --fig-dir $(FIGS)/benchmarks --dpi $(FIG_DPI)

lateral: lateral-oscillation

mesh-step-sensitivity: pressure-history-summary $(POSTPROCESSED_CSV)
	@PYTHONPATH=$(PYTHON) $(CONDA_PYTHON) -u $(PYTHON)/benchmarks/plot_mesh_step_sensitivity.py \
	  --summary $(SIMULATION)/results/pressure-history-summary.csv \
	  --postprocessed $(POSTPROCESSED_CSV) \
	  --out-dir $(FIGS)/benchmarks \
	  --z-mid $(Z_MID) --cfl-sink $(CFL_SINK) --dpi $(FIG_DPI)

meshes: meshes-sink-suite

# Depth-window composition figures (one per run per field set: set0 is
# pressure/density/vertical-flow, set1 is drive/rate/fraction). Steps and
# nominals match the existing figures. Outputs carry the full run UID.
# Runs without synced solutions are skipped, so this works before and
# after sync-barkla (steps from project.mk DEPTH_WINDOW_STEPS).

scaling: mesh-step-sensitivity

depth-window-figures:
	@PYTHONPATH=$(PYTHON) $(CONDA_PYTHON) -u $(PYTHON)/benchmarks/compute_window_clims.py \
	  --models $(UIDS_SINK_SUITE) --out $(SIMULATION)/results/depth-window-clims.json \
	  --nominal-sink-m=$(NOMINAL_410_SINK400) \
	  --block-top-m=$(BLOCK_Y_TOP) --block-bottom-m=$(BLOCK_Y_BOT) --gravity=$(GRAVITY)
	@for model in $(UIDS_SINK_SUITE); do \
	  nom=$(NOMINAL_410_SINK400); \
	  ok=1; for st in $(DEPTH_WINDOW_STEPS); do \
	    [ -f $(SIMULATION)/results/$$model/solution/solution-$$st.pvtu ] || ok=0; \
	  done; \
	  if [ $$ok -eq 0 ]; then echo "skip $$model (solutions missing)"; continue; fi; \
	  for s in set0 set1; do \
	    PYTHONPATH=$(PYTHON) $(CONDA_PYTHON) -u $(PYTHON)/benchmarks/plot_depth_window.py \
	      --model $$model --steps $(DEPTH_WINDOW_STEPS) --nominal-410-m $$nom \
	      --block-top-m=$(BLOCK_Y_TOP) --block-bottom-m=$(BLOCK_Y_BOT) --gravity=$(GRAVITY) \
	      --clims-json $(SIMULATION)/results/depth-window-clims.json \
	      --out $(FIGS)/benchmarks/depth-window-$$model-$$s.png --set $$s --dpi $(FIG_DPI); \
	  done; \
	done

depth-window: depth-window-figures

# Shared mesh recipe: $(1)=suite tag, $(2)=models, $(3)=visualize ids,
# $(4)=fig dir, $(5)=410 nominal (m), $(6)=trace x (m), $(7)=model height (m).
define MESH_SUITE
	@$(eval MODELS := $(2))
	@$(eval DIRS := $(addprefix $(SIMULATION)/results/, $(MODELS)))
	@$(eval VIS := $(3))
	@PYTHONPATH=$(PYTHON) $(CONDA_PYTHON) -u $(PYTHON)/simulation/mesh/main.py \
	  $(SIMULATION)/data/olivine-wadsleyite-profile-Mg$(MG_NUM).tsv \
	  $(7) \
	  $(SURFACE_PRESSURE) \
	  $(4) \
	  $(SIMULATION)/results \
	  --model-ids $(MODELS) \
	  --timesteps $(TIMESTEPS) \
	  --plot-timesteps $(MESH_TIMESTEPS) \
	  --suite-tag $(1) \
	  --in-dirs $(DIRS) \
	  --visualize-ids $(VIS) \
	  --depth-corr-ol-wd=$(DEPTH_CORRECTION_OL_WD) \
	  --nominal-410=$(5) \
	  --trace-x=$(6) \
	  --x-step-limit-m=$(TRACE_X_STEP_LIMIT) \
	  --block-top-m=$(BLOCK_Y_TOP) \
	  --block-bottom-m=$(BLOCK_Y_BOT) \
	  --gravity=$(GRAVITY) \
	  --mode=$(POSTPROCESS_MODE) \
	  --save-csv=$(SAVE_CSV) \
	  --force-reprocess=$(FORCE_REPROCESS) \
	  --verbosity=$(POSTPROCESS_VERBOSITY) \
	  --chunk-size=$(CHUNK_SIZE) \
	  --dpi=$(FIG_DPI)
endef

meshes-sink-suite:
	$(call MESH_SUITE,$(TAG_SINK_SUITE),$(MODELS_SINK_SUITE),$(VIS_MODELS_SINK_SUITE),$(FIGS_SIM_SINK_SUITE),$(NOMINAL_410_SINK400),$(TRACE_X_SINK),$(MODEL_HEIGHT_SINK))

adiabat: $(PROFILES) $(PYR_TABLE) $(PYR_ADIABAT)

# BurnMan builds both PYR tables in one run from the PerpleX project
# output. Run inside perplex/PYR where werami and PYR.dat live.
$(PYR_ADIABAT):
	@cd $(PERPLEX)/PYR && PYTHONPATH=$(PYTHON) $(CONDA_PYTHON) -u $(PYTHON)/adiabat/main.py PYR $(MG_NUM) $(SIMULATION)/data $(FIGS)/adiabat \
	  --potential-temperature $(ADIABAT_POTENTIAL_TEMP) --out-table-resolution $(ADIABAT_TABLE_RES) \
	  --out-profile-resolution $(ADIABAT_PROFILE_RES) --planet-radius $(PLANET_RADIUS) --surface-gravity $(GRAVITY) --dpi $(FIG_DPI)

$(PYR_TABLE): $(PYR_ADIABAT)
	@test -f $@

$(PROFILES): $(SIMULATION)/data/olivine-wadsleyite-profile-Mg%.tsv:
	@for model in $(PERPLEX_MODELS); do \
	  cd $(PERPLEX)/$$model && PYTHONPATH=$(PYTHON) $(CONDA_PYTHON) -u $(PYTHON)/adiabat/main.py $$model $* $(SIMULATION)/data $(FIGS)/adiabat \
	    --potential-temperature $(ADIABAT_POTENTIAL_TEMP) --out-table-resolution $(ADIABAT_TABLE_RES) \
	    --out-profile-resolution $(ADIABAT_PROFILE_RES) --planet-radius $(PLANET_RADIUS) --surface-gravity $(GRAVITY) --dpi $(FIG_DPI); \
	done

clean:
	@$(call SAFE_RM_LIST,$(CLEAN))

help:
	$(call LOG_INFO,Available targets:)
	$(call LOG_DETAIL,visualize        Derive data products and render all figures (meshes, setup, benchmarks))
	$(call LOG_DETAIL,postprocess      Alias for visualize (kept for compatibility))
	$(call LOG_DETAIL,benchmarks       Run all benchmark diagnostics (pressure-history, lateral, scaling, depth-window))
	$(call LOG_DETAIL,sync-barkla        Fetch simulation results from Barkla2 (delegates to bash))
	$(call LOG_DETAIL,adiabat            Build PerpleX phase profiles + adiabat figures)
	$(call LOG_DETAIL,meshes             Visualize ASPECT models (sink, full mode))
	$(call LOG_DETAIL,meshes-sink-suite   Visualize NH sinking-block benchmarks)
	$(call LOG_DETAIL,extract-timeseries Extract per-run pressure/boundary/stats histories from solutions)
	$(call LOG_DETAIL,timeseries       Alias for extract-timeseries)
	$(call LOG_DETAIL,pressure-history-summary Summarize range: vtu extrema + flow/point/depth plots)
	$(call LOG_DETAIL,pressure-history Alias for pressure-history-summary)
	$(call LOG_DETAIL,lateral-oscillation Lateral oscillation diagnostic (transient steps, sink))
	$(call LOG_DETAIL,lateral          Alias for lateral-oscillation)
	$(call LOG_DETAIL,mesh-step-sensitivity Mesh + step sensitivity: range vs refinement and step size)
	$(call LOG_DETAIL,scaling          Alias for mesh-step-sensitivity)
	$(call LOG_DETAIL,depth-window-figures Draw depth-window compositions for all runs with solutions)
	$(call LOG_DETAIL,depth-window     Alias for depth-window-figures)
	$(call LOG_DETAIL,setup-sketch     Draw setup domain sketches (initial + boundary conditions))
	$(call LOG_DETAIL,setup            Alias for setup-sketch)
	$(call LOG_DETAIL,clean              Remove generated files (safe))
