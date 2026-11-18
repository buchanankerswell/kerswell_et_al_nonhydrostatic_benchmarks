# Set the default goal before includes
.DEFAULT_GOAL := help

# Include definitions
include $(realpath $(dir $(lastword $(MAKEFILE_LIST)))/../project.mk)
include $(SIMULATION)/local.mk

.PHONY: sync-barkla run-aspect download clean help

download:
	@$(BASH)/simulation/download-zenodo.sh "$(ZENODO_DATASET_DOI)" "$(PROJECT_ROOT)" "$(ZENODO_FILES)" "$(FORCE_DOWNLOAD)"

sync-barkla:
	@FORCE_SYNC=$(FORCE_SYNC) $(BASH)/simulation/sync-barkla2.sh \
	  "$(notdir $(PRMS_BOX) $(PRMS_SINK))" "$(TIMESTEPS)" "$(SIMULATION)" "$(BARKLA2_SIMULATION)"

PRM_NAME := $(basename $(notdir $(PRM)))
RUN      := $(PRM:.prm=.run)
run-aspect:
	@mkdir -p $(SIMULATION)/results/$(PRM_NAME)
	@if [ ! -f "$(RUN)" ]; then \
	  if [ "$(OS_SYSTEM)" = "rocky" ]; then \
	    sbatch --job-name="$(PRM_NAME)" \
	      --output="$(SIMULATION)/results/$(PRM_NAME)/$(PRM_NAME).log" \
	      --partition="nodes" \
	      --ntasks=$(NTASKS) \
	      --ntasks-per-node=$(NTASKSPERNODE) \
	      --time=$(TIME) \
	      --mail-user=$(MAIL_ADDRESS) \
	      --mail-type=$(MAIL_TYPE) \
	      --export=ALL,LOG_SH=$(LOG_SH) \
	      $(RUN_ASPECT) $(ASPECT_EXE) "$(PRM)" $(GCC) $(OPENMPI) $(OPENBLAS) $(CMAKE) 2>&1 | sed 's/^/ .. /'; \
	  else \
	    $(RUN_ASPECT) $(NTASKS) $(ASPECT_EXE) "$(PRM)" 2>&1 | tee -a "$(SIMULATION)/results/$(PRM_NAME)/$(PRM_NAME).log"; \
	  fi \
	fi

clean:
	@: nothing generated here

help:
	$(call LOG_INFO,Available targets:)
	$(call LOG_DETAIL,sync-barkla                Fetch NH benchmark results from Barkla2)
	$(call LOG_DETAIL,run-aspect PRM=<file.prm>  Run one ASPECT model (used by simulation/Makefile))
	$(call LOG_DETAIL,download                   Fetch archived datasets from Zenodo (box + sink))
	$(call LOG_DETAIL,clean                      Nothing to remove (no-op))
