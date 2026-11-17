# Set the default goal before includes
.DEFAULT_GOAL := help

# Include definitions
include $(realpath $(dir $(lastword $(MAKEFILE_LIST)))/../project.mk)
include local.mk

ALL_RUNS := $(PRMS_BOX:.prm=.run) $(PRMS_SINK:.prm=.run)

CORE_BOX  := $(PRMS_GLOBALS_BOX) $(PRMS_SOLVER_BOX) $(PRMS_GEOMETRY_BOX) $(PRMS_BOUNDARY_BOX) $(PRMS_COMPOSITION_BOX) $(PRMS_INITIAL_BOX) $(PRMS_PHYSICS_BOX) $(PRMS_MATERIAL_BOX) $(PRMS_POSTPROCESS_BOX)
CORE_SINK := $(PRMS_GLOBALS_SINK) $(PRMS_SOLVER_SINK) $(PRMS_GEOMETRY_SINK) $(PRMS_BOUNDARY_SINK) $(PRMS_COMPOSITION_SINK) $(PRMS_INITIAL_SINK) $(PRMS_PHYSICS_SINK) $(PRMS_MATERIAL_SINK) $(PRMS_POSTPROCESS_SINK)

CLEAN      := $(ASPECT_PLUGIN) $(ASPECT_CONFIGS)
DEEP_CLEAN := $(ASPECT_RESULTS) $(ASPECT_DATA)

.PHONY: all all-models models-box-suite models-sink-suite configs configs-box-suite configs-sink-suite clean deep-clean help
.PRECIOUS: $(ASPECT_CONFIGS)

all: all-models
all-models: $(ALL_RUNS)
models-box-suite: $(ASPECT_EXE) $(DEALII_ENABLE) $(ASPECT_PLUGIN) $(PRMS_BOX:.prm=.run)
models-sink-suite: $(ASPECT_EXE) $(DEALII_ENABLE) $(ASPECT_PLUGIN) $(PRMS_SINK:.prm=.run)
configs: configs-box-suite configs-sink-suite
configs-box-suite: $(PRMS_BOX)
configs-sink-suite: $(PRMS_SINK)

$(PRMS_BOX:.prm=.run): $(ASPECT_PLUGIN)
$(PRMS_SINK:.prm=.run): $(ASPECT_PLUGIN)

$(PRMS_BOX): $(CORE_BOX)
$(PRMS_SINK): $(CORE_SINK)

$(ASPECT_CONFIGS):
	@mkdir -p $@

$(PRMS_GLOBALS_BOX) $(PRMS_GLOBALS_SINK): | $(ASPECT_CONFIGS)

%.run: %.prm
	@$(MAKE) --no-print-directory -C $(BASH) run-aspect PRM=$<

$(ASPECT_PLUGIN): $(ASPECT_EXE) $(DEALII_ENABLE)
	@if [ "$(OS_SYSTEM)" = "rocky" ]; then \
	  module load $(GCC) $(OPENMPI) $(OPENBLAS) $(CMAKE); \
	  cd $(SIMULATION)/plugins; \
	  cmake . -D CMAKE_EXPORT_COMPILE_COMMANDS=ON -D Aspect_DIR=$(dir $(ASPECT_EXE)) -D CMAKE_CXX_COMPILER=mpicxx -W no-dev; \
	  make; \
	else \
	  cd $(SIMULATION)/plugins; \
	  cmake . -D CMAKE_EXPORT_COMPILE_COMMANDS=ON -D Aspect_DIR=$(dir $(ASPECT_EXE)) -W no-dev 2>&1 | sed 's/^/ /'; \
	  make 2>&1 | sed 's/^/ -- /'; \
	fi

clean:
	@$(call SAFE_RM_LIST,$(CLEAN))
	@find $(PROJECT_ROOT)/simulation -type l -path '*/plugins/aspect*' | while read -r item; do \
	  if [[ "$$item" == $(PROJECT_ROOT)* ]]; then \
	    . "$(BASH)/utils/log.sh"; log_delete "$$item"; \
	    rm "$$item"; \
	  fi; \
	done

deep-clean:
	@$(call SAFE_RM_LIST,$(DEEP_CLEAN))

help:
	$(call LOG_INFO,Available targets:)
	$(call LOG_DETAIL,all-models          Run all NH benchmark models (box + sink))
	$(call LOG_DETAIL,models-box-suite    Run NH box 1-reaction benchmarks)
	$(call LOG_DETAIL,models-sink-suite   Run NH sinking-block benchmarks)
	$(call LOG_DETAIL,configs             Generate configs only (box + sink))
	$(call LOG_DETAIL,configs-box-suite   Generate box configs only)
	$(call LOG_DETAIL,configs-sink-suite  Generate sink configs only)
	$(call LOG_DETAIL,clean               Remove generated files (safe))
	$(call LOG_DETAIL,deep-clean          Remove results and data (use with caution!))
