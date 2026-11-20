# Set the default goal before includes
.DEFAULT_GOAL := help

# Include definitions
include $(realpath $(dir $(lastword $(MAKEFILE_LIST)))/../project.mk)
include $(SIMULATION)/local.mk

PROFILES          := $(foreach g,$(MG_NUM),$(SIMULATION)/data/olivine-wadsleyite-profile-Mg$(g).tsv)
MODELS_BOX_SUITE  := $(notdir $(RESULTS_BOX_SUITE))
MODELS_SINK_SUITE := $(notdir $(RESULTS_SINK_SUITE))

CLEAN := $(PYTHON)/**/__pycache__ \
	 $(PYTHON)/simulation/**/__pycache__ \
	 $(PYTHON)/setup/**/__pycache__ \
	 $(FIGS)/adiabat \
	 $(FIGS_SETUP) \
	 $(FIGS_BOX_SUITE) \
	 $(FIGS_SINK_SUITE) \
	 $(FIGS)/benchmarks \
	 $(DATA_MESH_BOX_SUITE) \
	 $(DATA_MESH_SINK_SUITE) \
	 $(POSTPROCESSED_CSV) \
	 $(SIMULATION)/results/pressure-history-summary.csv

.PHONY: all visualize sync-barkla postprocess timeseries pressure-history diagnostics scaling setup adiabat meshes meshes-box-suite meshes-sink-suite clean help

all: visualize
visualize: meshes setup

setup:
	@PYTHONPATH=$(PYTHON) $(CONDA_PYTHON) -u $(PYTHON)/setup/domains.py --suite box --width-m $(MODEL_WIDTH_BOX) --height-m $(MODEL_HEIGHT_BOX) \
	  --transition-y-m $(TRANSITION_Y_OL_WD) --trace-x-m $(TRACE_X_BOX) --nominal-m $(NOMINAL_410_BOX) --probes "$(POINTS_BOX)" --out $(FIGS_SETUP)/box-domain.png
	@PYTHONPATH=$(PYTHON) $(CONDA_PYTHON) -u $(PYTHON)/setup/domains.py --suite sink --width-m $(MODEL_WIDTH_SINK) --height-m $(MODEL_HEIGHT_SINK) \
	  --transition-y-m $(TRANSITION_Y_OL_WD) --trace-x-m $(TRACE_X_SINK) --nominal-m $(NOMINAL_410_SINK400) --probes "$(POINTS_SINK)" --out $(FIGS_SETUP)/sink-domain.png
	$(call LOG_ARTIFACT,$(FIGS_SETUP))

sync-barkla:
	@$(MAKE) --no-print-directory -C $(BASH) sync-barkla

postprocess: meshes-box-suite meshes-sink-suite $(POSTPROCESSED_CSV)

.PHONY: $(POSTPROCESSED_CSV)
$(POSTPROCESSED_CSV):
	@mkdir -p $(dir $@)
	@PYTHONPATH=$(PYTHON) $(CONDA_PYTHON) -u $(PYTHON)/simulation/mesh/export-postprocessed.py \
	  --data-dir $(SIMULATION)/results \
	  --out-csv $@ \
	  --profile-ol-wd $(SIMULATION)/data/olivine-wadsleyite-profile-Mg$(MG_NUM).tsv \
	  --model-height $(MODEL_HEIGHT_BOX) \
	  --surface-pressure $(SURFACE_PRESSURE) \
	  --depth-corr-ol-wd=$(DEPTH_CORRECTION_OL_WD) \
	  --nominal-410-box=$(NOMINAL_410_BOX) \
	  --nominal-410-sink400=$(NOMINAL_410_SINK400) \
	  --force
	$(call LOG_ARTIFACT,$@)

timeseries:
	@for run in $(UIDS_BOX_SUITE) $(UIDS_SINK_SUITE); do \
	  PYTHONPATH=$(PYTHON) $(CONDA_PYTHON) -u $(PYTHON)/benchmarks/extract_timeseries.py $(SIMULATION)/results/$$run; \
	done

pressure-history: timeseries
	@PYTHONPATH=$(PYTHON) $(CONDA_PYTHON) -u $(PYTHON)/benchmarks/summarize_pressure_history.py \
	  --runs $(UIDS_BOX_SUITE) $(UIDS_SINK_SUITE) \
	  --plot-box $(PLOT_BOX_RUNS) \
	  --plot-sink $(PLOT_SINK_RUNS) \
	  --out-csv $(SIMULATION)/results/pressure-history-summary.csv \
	  --fig-dir $(FIGS)/benchmarks
	@PYTHONPATH=$(PYTHON) $(CONDA_PYTHON) -u $(PYTHON)/benchmarks/plot_depth_profiles.py \
	  --runs $(PLOT_BOX_RUNS) --suite-tag box --profile $(SIMULATION)/data/olivine-wadsleyite-profile-Mg$(MG_NUM).tsv \
	  --model-height $(MODEL_HEIGHT_BOX) --surface-pressure $(SURFACE_PRESSURE) \
	  --nominal-km $(shell echo $(NOMINAL_410_BOX) | awk '{print $$1/1000}') --out $(FIGS)/benchmarks/depth-profiles-box.png
	@PYTHONPATH=$(PYTHON) $(CONDA_PYTHON) -u $(PYTHON)/benchmarks/plot_depth_profiles.py \
	  --runs $(PLOT_SINK_RUNS) --suite-tag sink --profile $(SIMULATION)/data/olivine-wadsleyite-profile-Mg$(MG_NUM).tsv \
	  --model-height $(MODEL_HEIGHT_SINK) --surface-pressure $(SURFACE_PRESSURE) \
	  --nominal-km $(shell echo $(NOMINAL_410_SINK400) | awk '{print $$1/1000}') --out $(FIGS)/benchmarks/depth-profiles-sink.png
	$(call LOG_ARTIFACT,$(FIGS)/benchmarks)

diagnostics: postprocess
	@PYTHONPATH=$(PYTHON) $(CONDA_PYTHON) -u $(PYTHON)/benchmarks/plot_bulk_damping_check.py --fig-dir $(FIGS)/benchmarks
	$(call LOG_ARTIFACT,$(FIGS)/benchmarks)

scaling: pressure-history postprocess
	@PYTHONPATH=$(PYTHON) $(CONDA_PYTHON) -u $(PYTHON)/benchmarks/plot_mesh_step_sensitivity.py \
	  --summary $(SIMULATION)/results/pressure-history-summary.csv \
	  --postprocessed $(POSTPROCESSED_CSV) \
	  --out-dir $(FIGS)/benchmarks \
	  --z-mid $(Z_MID) --cfl-box $(CFL_BOX) --cfl-sink $(CFL_SINK)
	$(call LOG_ARTIFACT,$(FIGS)/benchmarks)

meshes: meshes-box-suite meshes-sink-suite

# Shared mesh recipe: $(1)=suite tag, $(2)=models, $(3)=visualize ids,
# $(4)=fig dir, $(5)=410 nominal [m], $(6)=trace x [m], $(7)=model height [m].
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
	  --suite-tag $(1) \
	  --in-dirs $(DIRS) \
	  --visualize-ids $(VIS) \
	  --depth-corr-ol-wd=$(DEPTH_CORRECTION_OL_WD) \
	  --nominal-410=$(5) \
	  --trace-x=$(6) \
	  --mode=$(POSTPROCESS_MODE) \
	  --save-csv=$(SAVE_CSV) \
	  --force-reprocess=$(FORCE_REPROCESS) \
	  --verbosity=$(POSTPROCESS_VERBOSITY) \
	  --chunk-size=$(CHUNK_SIZE)
endef

meshes-box-suite:
	$(call MESH_SUITE,$(TAG_BOX_SUITE),$(MODELS_BOX_SUITE),$(VIS_MODELS_BOX_SUITE),$(FIGS_SIM_BOX_SUITE),$(NOMINAL_410_BOX),$(TRACE_X_BOX),$(MODEL_HEIGHT_BOX))

meshes-sink-suite:
	$(call MESH_SUITE,$(TAG_SINK_SUITE),$(MODELS_SINK_SUITE),$(VIS_MODELS_SINK_SUITE),$(FIGS_SIM_SINK_SUITE),$(NOMINAL_410_SINK400),$(TRACE_X_SINK),$(MODEL_HEIGHT_SINK))

adiabat: $(PROFILES)

$(PROFILES): $(SIMULATION)/data/olivine-wadsleyite-profile-Mg%.tsv:
	@for model in $(PERPLEX_MODELS); do \
	  cd $(PERPLEX)/$$model && PYTHONPATH=$(PYTHON) $(CONDA_PYTHON) -u $(PYTHON)/adiabat/main.py $$model $* $(SIMULATION)/data $(FIGS)/adiabat; \
	done

clean:
	@$(call SAFE_RM_LIST,$(CLEAN))

help:
	$(call LOG_INFO,Available targets:)
	$(call LOG_DETAIL,visualize          Visualize all results (box + sink meshes))
	$(call LOG_DETAIL,sync-barkla        Fetch simulation results from Barkla2 (delegates to bash))
	$(call LOG_DETAIL,adiabat            Build PerpleX phase profiles + adiabat figures)
	$(call LOG_DETAIL,meshes             Visualize ASPECT models (box + sink))
	$(call LOG_DETAIL,meshes-box-suite   Visualize NH box benchmarks)
	$(call LOG_DETAIL,meshes-sink-suite  Visualize NH sinking-block benchmarks)
	$(call LOG_DETAIL,postprocess        Export postprocessed table (thermal-kinetic split at 410))
	$(call LOG_DETAIL,timeseries         Extract per-run pressure/boundary/stats histories from solutions)
	$(call LOG_DETAIL,pressure-history  Summarize range: vtu extrema + flow/point/depth plots)
	$(call LOG_DETAIL,diagnostics        Supplement: bulk-damping resolution check (needs postprocess))
	$(call LOG_DETAIL,scaling            Mesh + step sensitivity: range vs refinement and step size)
	$(call LOG_DETAIL,setup              Draw setup domain sketches (initial + boundary conditions))
	$(call LOG_DETAIL,clean              Remove generated files (safe))
