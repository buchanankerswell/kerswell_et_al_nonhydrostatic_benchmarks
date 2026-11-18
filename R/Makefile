# Set the default goal before includes
.DEFAULT_GOAL := help

# Include definitions
include $(realpath $(dir $(lastword $(MAKEFILE_LIST)))/../project.mk)

CLEAN := $(FIGS_STRUCTURE) $(FIGS_SEISMIC) $(POSTPROCESSED_MD)

.PHONY: all visualize tables adiabat simulation seismic clean help

all: visualize
visualize: adiabat simulation seismic

tables: $(POSTPROCESSED_CSV)
	@Rscript $(R)/tables.R $(R)/utils $(POSTPROCESSED_CSV) $(SIMULATION)/results

adiabat:
	@for model in $(PERPLEX_MODELS); do Rscript $(R)/adiabat.R $(R)/utils $$model $(SIMULATION)/data $(FIGS)/adiabat; done

seismic: $(MESH_CSV_BOX_SUITE) $(MESH_CSV_SINK_SUITE)
	@Rscript $(R)/seismic.R $(R)/utils $(SEISMIC_BOX_SUITE) $(SEISMIC_SINK_SUITE) $(FIGS_SEISMIC) $(FORCE_REWRITE) $(NOMINAL_410_BOX) $(NOMINAL_410_SINK400)

simulation: $(POSTPROCESSED_CSV)
	@mkdir -p $(SIMULATION)/results
	@Rscript $(R)/simulation.R $(R)/utils $(POSTPROCESSED_CSV) $(FIGS_STRUCTURE) $(FORCE_REWRITE)

$(MESH_CSV_BOX_SUITE):
	@$(MAKE) --no-print-directory -C $(PYTHON) meshes-box-suite
$(MESH_CSV_SINK_SUITE):
	@$(MAKE) --no-print-directory -C $(PYTHON) meshes-sink-suite

$(POSTPROCESSED_CSV):
	@$(MAKE) --no-print-directory -C $(PYTHON) postprocess

clean:
	@$(call SAFE_RM_LIST,$(CLEAN))

help:
	$(call LOG_INFO,Available targets:)
	$(call LOG_DETAIL,visualize   Visualize all results (box + sink benchmarks))
	$(call LOG_DETAIL,adiabat     Visualize adiabatic profiles)
	$(call LOG_DETAIL,simulation  Visualize combined benchmark results)
	$(call LOG_DETAIL,seismic     Visualize combined seismic profiles)
	$(call LOG_DETAIL,tables      Write combined result tables)
	$(call LOG_DETAIL,clean       Remove generated files (safe))
