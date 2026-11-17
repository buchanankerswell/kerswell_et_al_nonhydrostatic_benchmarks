# Set the default goal before includes
.DEFAULT_GOAL := help

# Include definitions
include $(realpath $(dir $(lastword $(MAKEFILE_LIST)))/../project.mk)
include $(SIMULATION)/local.mk

PROFILES        := $(foreach g,$(MG_NUM),$(SIMULATION)/data/olivine-wadsleyite-profile-Mg$(g).tsv)
MODELS_BOX_SUITE  := $(notdir $(RESULTS_BOX_SUITE))
MODELS_SINK_SUITE := $(notdir $(RESULTS_SINK_SUITE))

CLEAN := $(PYTHON)/**/__pycache__ \
	 $(PYTHON)/simulation/**/__pycache__ \
	 $(FIGS)/adiabat \
	 $(FIGS_BOX_SUITE) \
	 $(FIGS_SINK_SUITE) \
	 $(FIGS_SIMULATION) \
	 $(DATA_MESH_BOX_SUITE) \
	 $(DATA_MESH_SINK_SUITE) \
	 $(POSTPROCESSED_CSV)

.PHONY: all visualize sync-barkla postprocess timeseries pressure-waves adiabat meshes meshes-box-suite meshes-sink-suite clean help

all: visualize
visualize: meshes

sync-barkla:
	@$(MAKE) --no-print-directory -C $(BASH) sync-barkla

postprocess: meshes-box-suite meshes-sink-suite $(POSTPROCESSED_CSV)

.PHONY: $(POSTPROCESSED_CSV)
$(POSTPROCESSED_CSV):
	@mkdir -p $(dir $@)
	@PYTHONPATH=$(PYTHON) $(CONDA_PYTHON) -u $(PYTHON)/simulation/mesh/export-postprocessed.py \
	  --data-dir $(SIMULATION)/data \
	  --out-csv $@ \
	  --profile-ol-wd $(BENCH_DATA)/olivine-wadsleyite-profile-Mg$(MG_NUM).tsv \
	  --profile-wd-ri $(BENCH_DATA)/wadsleyite-ringwoodite-profile-Mg$(MG_NUM).tsv \
	  --profile-ri-ps $(BENCH_DATA)/ringwoodite-postspinel-profile-Mg$(MG_NUM).tsv \
	  --model-height $(MODEL_HEIGHT_BOX) \
	  --surface-pressure $(SURFACE_PRESSURE) \
	  --depth-corr-ol-wd=$(DEPTH_CORRECTION_OL_WD) \
	  --depth-corr-wd-ri=$(DEPTH_CORRECTION_WD_RI) \
	  --depth-corr-ri-ps=$(DEPTH_CORRECTION_RI_PS) \
	  --force
	$(call LOG_ARTIFACT,$@)

timeseries:
	@for run in $(UIDS_BOX_SUITE) $(UIDS_SINK_SUITE); do \
	  PYTHONPATH=$(PYTHON) $(CONDA_PYTHON) -u $(PYTHON)/benchmarks/extract_timeseries.py $(SIMULATION)/results/$$run; \
	done

pressure-waves: timeseries
	@PYTHONPATH=$(PYTHON) $(CONDA_PYTHON) -u $(PYTHON)/benchmarks/quantify_pressure_waves.py \
	  --runs $(UIDS_BOX_SUITE) $(UIDS_SINK_SUITE) \
	  --plot-box $(PLOT_BOX_RUNS) \
	  --plot-sink $(PLOT_SINK_RUNS) \
	  --plot-laptop $(PLOT_LAPTOP_RUNS) \
	  --out-csv $(SIMULATION)/data/pressure-wave-summary.csv \
	  --fig-dir $(FIGS)/benchmarks
	$(call LOG_ARTIFACT,$(FIGS)/benchmarks)

meshes: meshes-box-suite meshes-sink-suite

meshes-box-suite: SUITE := BOX_SUITE
meshes-sink-suite: SUITE := SINK_SUITE
meshes-box-suite meshes-sink-suite:
	@$(eval MODELS := $(MODELS_$(SUITE)))
	@$(eval DIRS := $(addprefix $(SIMULATION)/results/, $(MODELS)))
	@$(eval VIS := $(VIS_MODELS_$(SUITE)))
	@PYTHONPATH=$(PYTHON) $(CONDA_PYTHON) -u $(PYTHON)/simulation/mesh/main.py \
	  $(BENCH_DATA)/olivine-wadsleyite-profile-Mg$(MG_NUM).tsv \
	  $(BENCH_DATA)/wadsleyite-ringwoodite-profile-Mg$(MG_NUM).tsv \
	  $(BENCH_DATA)/ringwoodite-postspinel-profile-Mg$(MG_NUM).tsv \
	  $(MODEL_HEIGHT_BOX) \
	  $(SURFACE_PRESSURE) \
	  $(FIGS_SIM_$(SUITE)) \
	  $(SIMULATION)/data \
	  --model-ids $(MODELS) \
	  --timesteps $(TIMESTEPS_MESH_$(SUITE)) \
	  --suite-tag $(TAG_$(SUITE)) \
	  --in-dirs $(DIRS) \
	  --visualize-ids $(VIS) \
	  --depth-corr-ol-wd=$(DEPTH_CORRECTION_OL_WD) \
	  --depth-corr-wd-ri=$(DEPTH_CORRECTION_WD_RI) \
	  --depth-corr-ri-ps=$(DEPTH_CORRECTION_RI_PS) \
	  --mode=$(POSTPROCESS_MODE) \
	  --save-csv=$(SAVE_CSV) \
	  --force-reprocess=$(FORCE_REPROCESS) \
	  --verbosity=$(POSTPROCESS_VERBOSITY) \
	  --chunk-size=$(CHUNK_SIZE)

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
	$(call LOG_DETAIL,postprocess         Export postprocessed table (thermal-kinetic split at 410))
	$(call LOG_DETAIL,timeseries          Extract per-run pressure/front timeseries from solutions)
	$(call LOG_DETAIL,pressure-waves      Quantify wave magnitude across benchmarks (table + plots))
	$(call LOG_DETAIL,clean              Remove generated files (safe))
