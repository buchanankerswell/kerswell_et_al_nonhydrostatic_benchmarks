# Set the default goal before includes
.DEFAULT_GOAL := help

# Include definitions
include project.mk

.PHONY: build models slab-models benchmarks visualize-benchmarks sync-barkla visualize manuscript download environments clean deep-clean help

build: environments download visualize manuscript
	$(call LOG_INFO,Study built successfully!)

models:
	@$(MAKE) --no-print-directory -C $(SIMULATION) all-models

slab-models:
	@$(MAKE) --no-print-directory -C $(SIMULATION) slab-models-sw-suite
	@$(MAKE) --no-print-directory -C $(SIMULATION) slab-models-nc-suite
	@$(MAKE) --no-print-directory -C $(SIMULATION) slab-models-test-suite

benchmarks:
	@$(MAKE) --no-print-directory -C $(SIMULATION) benchmarks

visualize-benchmarks:
	@$(MAKE) --no-print-directory -C $(PYTHON) meshes-benchmarks

sync-barkla:
	@$(MAKE) --no-print-directory -C $(BASH) sync-barkla

visualize:
	@$(MAKE) --no-print-directory -C $(PYTHON) visualize
	@$(MAKE) --no-print-directory -C $(R) visualize

manuscript:
	@$(MAKE) --no-print-directory -C $(DRAFT) all

download:
	@$(MAKE) --no-print-directory -C $(BASH) download

environments:
	@if ! conda info --envs | awk '{print $$1}' | grep -qx "$(CONDA_ENV)"; then conda env create -f $(PYTHON)/environment.yaml; fi
	@Rscript $(R)/environment.R

clean:
	@$(MAKE) --no-print-directory -C $(BASH) clean
	@$(MAKE) --no-print-directory -C $(PYTHON) clean
	@$(MAKE) --no-print-directory -C $(R) clean
	@$(MAKE) --no-print-directory -C $(SIMULATION) clean
	@$(MAKE) --no-print-directory -C $(DRAFT) clean
	@find . -name ".DS_Store" -type f -delete

deep-clean: clean
	@$(MAKE) --no-print-directory -C $(SIMULATION) deep-clean
	@$(MAKE) --no-print-directory -C $(DRAFT) deep-clean

help:
	$(call LOG_INFO,Available targets:)
	$(call LOG_DETAIL,build                Fetch data and reproduce figures and manuscript)
	$(call LOG_DETAIL,models               Run all slab ASPECT models (SW + NC + TEST))
	$(call LOG_DETAIL,slab-models          Run ASPECT slab models (SW + NC + TEST))
	$(call LOG_DETAIL,benchmarks           Run NH benchmarks (box + sink-block))
	$(call LOG_DETAIL,sync-barkla          Sync slab data from Barkla2 (NH sync TBD))
	$(call LOG_DETAIL,visualize            Visualize slab results (SW + NC))
	$(call LOG_DETAIL,visualize-benchmarks Visualize NH benchmarks (box + sink meshes))
	$(call LOG_DETAIL,manuscript           Render manuscript + SI + response)
	$(call LOG_DETAIL,download             Fetch archived datasets from Zenodo)
	$(call LOG_DETAIL,environments         Create Conda environments)
	$(call LOG_DETAIL,clean                Remove generated files (safe))
	$(call LOG_DETAIL,deep-clean           Remove results and data (use with caution!))
