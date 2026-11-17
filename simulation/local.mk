# NH benchmark UIDs: explicit REGISTER calls (paper + scaling + laptop + smoke).
# REGISTER_NH_BOX args: list dynp dampkind dampval z res cfl end.
# REGISTER_NH_SINK args: list dynp dampkind dampval block z res cfl end.
# Paper sets must match ID_B*/ID_S* in project.mk (asserted below).
$(eval $(call REGISTER_NH_BOX,UIDS_BOX_SUITE,1,none,0,$(Z_KIN),5,7e-01,1e7))
$(eval $(call REGISTER_NH_BOX,UIDS_BOX_SUITE,0,none,0,$(Z_KIN),5,7e-01,1e7))
$(eval $(call REGISTER_NH_BOX,UIDS_BOX_SUITE,1,Bimpl,1e21,$(Z_KIN),5,7e-01,1e7))
$(eval $(call REGISTER_NH_BOX,UIDS_BOX_SUITE,1,Bexpl,1e20,$(Z_KIN),5,7e-01,1e7))
$(eval $(call REGISTER_NH_BOX,UIDS_BOX_SUITE,1,Rel,3.156e12,$(Z_KIN),5,7e-01,1e7))
$(eval $(call REGISTER_NH_BOX,UIDS_BOX_SUITE,1,Cap,1e7,$(Z_KIN),5,7e-01,1e7))
$(eval $(call REGISTER_NH_BOX,UIDS_BOX_SUITE,1,none,0,$(Z_KIN),4,7e-01,1e7))
$(eval $(call REGISTER_NH_BOX,UIDS_BOX_SUITE,0,none,0,$(Z_KIN),4,7e-01,1e7))
$(eval $(call REGISTER_NH_BOX,UIDS_BOX_SUITE,1,Bimpl,1e21,$(Z_KIN),4,7e-01,1e7))
$(eval $(call REGISTER_NH_BOX,UIDS_BOX_SUITE,1,Bexpl,1e20,$(Z_KIN),4,7e-01,1e7))
$(eval $(call REGISTER_NH_BOX,UIDS_BOX_SUITE,1,Rel,3.156e12,$(Z_KIN),4,7e-01,1e7))
$(eval $(call REGISTER_NH_BOX,UIDS_BOX_SUITE,1,Cap,1e7,$(Z_KIN),4,7e-01,1e7))
$(eval $(call REGISTER_NH_BOX,UIDS_BOX_SUITE,1,none,0,$(Z_KIN),6,7e-01,1e7))
$(eval $(call REGISTER_NH_BOX,UIDS_BOX_SUITE,0,none,0,$(Z_KIN),6,7e-01,1e7))
$(eval $(call REGISTER_NH_BOX,UIDS_BOX_SUITE,1,Bimpl,1e21,$(Z_KIN),6,7e-01,1e7))
$(eval $(call REGISTER_NH_BOX,UIDS_BOX_SUITE,1,Bexpl,1e20,$(Z_KIN),6,7e-01,1e7))
$(eval $(call REGISTER_NH_BOX,UIDS_BOX_SUITE,1,Rel,3.156e12,$(Z_KIN),6,7e-01,1e7))
$(eval $(call REGISTER_NH_BOX,UIDS_BOX_SUITE,1,Cap,1e7,$(Z_KIN),6,7e-01,1e7))
$(eval $(call REGISTER_NH_BOX,UIDS_BOX_SUITE,1,none,0,$(Z_KIN),5,3.5e-01,1e7))
$(eval $(call REGISTER_NH_BOX,UIDS_BOX_SUITE,1,none,0,$(Z_KIN),5,1.4e0,1e7))

$(eval $(call REGISTER_NH_SINK,UIDS_SINK_SUITE,1,none,0,400,$(Z_KIN),6,5e-01,5e6))
$(eval $(call REGISTER_NH_SINK,UIDS_SINK_SUITE,0,none,0,400,$(Z_KIN),6,5e-01,5e6))
$(eval $(call REGISTER_NH_SINK,UIDS_SINK_SUITE,1,Bimpl,1e19,400,$(Z_KIN),6,5e-01,5e6))
$(eval $(call REGISTER_NH_SINK,UIDS_SINK_SUITE,1,Bimpl,1e20,400,$(Z_KIN),6,5e-01,5e6))
$(eval $(call REGISTER_NH_SINK,UIDS_SINK_SUITE,1,Bexpl,1e19,400,$(Z_KIN),6,5e-01,5e6))
$(eval $(call REGISTER_NH_SINK,UIDS_SINK_SUITE,1,Rel,3.156e10,400,$(Z_KIN),6,5e-01,5e6))
$(eval $(call REGISTER_NH_SINK,UIDS_SINK_SUITE,1,Rel,3.156e11,400,$(Z_KIN),6,5e-01,5e6))
$(eval $(call REGISTER_NH_SINK,UIDS_SINK_SUITE,1,Cap,2e8,400,$(Z_KIN),6,5e-01,5e6))
$(eval $(call REGISTER_NH_SINK,UIDS_SINK_SUITE,1,none,0,400,$(Z_KIN),4,5e-01,1e6))
$(eval $(call REGISTER_NH_SINK,UIDS_SINK_SUITE,1,none,0,0,$(Z_KIN),4,5e-01,1e6))
$(eval $(call REGISTER_NH_SINK,UIDS_SINK_SUITE,1,none,0,400,$(Z_KIN),5,5e-01,2e6))
$(eval $(call REGISTER_NH_SINK,UIDS_SINK_SUITE,0,none,0,400,$(Z_KIN),5,5e-01,2e6))
$(eval $(call REGISTER_NH_SINK,UIDS_SINK_SUITE,1,Bimpl,1e19,400,$(Z_KIN),5,5e-01,2e6))
$(eval $(call REGISTER_NH_SINK,UIDS_SINK_SUITE,1,Bimpl,1e20,400,$(Z_KIN),5,5e-01,2e6))
$(eval $(call REGISTER_NH_SINK,UIDS_SINK_SUITE,1,Bexpl,1e19,400,$(Z_KIN),5,5e-01,2e6))
$(eval $(call REGISTER_NH_SINK,UIDS_SINK_SUITE,1,Rel,3.156e10,400,$(Z_KIN),5,5e-01,2e6))
$(eval $(call REGISTER_NH_SINK,UIDS_SINK_SUITE,1,Rel,3.156e11,400,$(Z_KIN),5,5e-01,2e6))
$(eval $(call REGISTER_NH_SINK,UIDS_SINK_SUITE,1,Cap,2e8,400,$(Z_KIN),5,5e-01,2e6))
$(eval $(call REGISTER_NH_SINK,UIDS_SINK_SUITE,1,none,0,400,$(Z_KIN),5,2.5e-01,5e6))
$(eval $(call REGISTER_NH_SINK,UIDS_SINK_SUITE,1,Bimpl,1e19,400,$(Z_KIN),5,2.5e-01,5e6))
$(eval $(call REGISTER_NH_SINK,UIDS_SINK_SUITE,1,none,0,400,$(Z_KIN),5,5e-01,5e6))
$(eval $(call REGISTER_NH_SINK,UIDS_SINK_SUITE,1,Bimpl,1e19,400,$(Z_KIN),5,5e-01,5e6))

$(foreach id,$(ID_B1) $(ID_B2) $(ID_B3) $(ID_B4) $(ID_B5) $(ID_B6),$(if $(filter $(id),$(UIDS_BOX_SUITE)),,$(error !! UID $(id) not registered in UIDS_BOX_SUITE)))
$(foreach id,$(ID_S1) $(ID_S2) $(ID_S3) $(ID_S4) $(ID_S5) $(ID_S6) $(ID_S7) $(ID_S8) $(ID_STEST) $(ID_SNOBLOCK),$(if $(filter $(id),$(UIDS_SINK_SUITE)),,$(error !! UID $(id) not registered in UIDS_SINK_SUITE)))

ASPECT_DATA      := $(SIMULATION)/data
ASPECT_TEMPLATES := $(SIMULATION)/params/templates
ASPECT_CONFIGS   := $(SIMULATION)/configs
ASPECT_PLUGIN    := $(SIMULATION)/plugins/build/libnh-kinetics.release.so \
                    $(SIMULATION)/plugins/build/libnh-kinetics.debug.so \
                    $(SIMULATION)/plugins/build/CMakeFiles \
                    $(SIMULATION)/plugins/build/Makefile \
                    $(SIMULATION)/plugins/build/CMakeCache.txt \
                    $(SIMULATION)/plugins/build/cmake_install.cmake

PRMS_GLOBALS_BOX     := $(foreach uid,$(UIDS_BOX_SUITE),$(ASPECT_CONFIGS)/$(uid).globals.prm)
PRMS_SOLVER_BOX      := $(foreach uid,$(UIDS_BOX_SUITE),$(ASPECT_CONFIGS)/$(uid).solver.prm)
PRMS_GEOMETRY_BOX    := $(foreach uid,$(UIDS_BOX_SUITE),$(ASPECT_CONFIGS)/$(uid).geometry.prm)
PRMS_BOUNDARY_BOX    := $(foreach uid,$(UIDS_BOX_SUITE),$(ASPECT_CONFIGS)/$(uid).boundary.prm)
PRMS_COMPOSITION_BOX := $(foreach uid,$(UIDS_BOX_SUITE),$(ASPECT_CONFIGS)/$(uid).composition.prm)
PRMS_INITIAL_BOX     := $(foreach uid,$(UIDS_BOX_SUITE),$(ASPECT_CONFIGS)/$(uid).initial.prm)
PRMS_PHYSICS_BOX     := $(foreach uid,$(UIDS_BOX_SUITE),$(ASPECT_CONFIGS)/$(uid).physics.prm)
PRMS_MATERIAL_BOX    := $(foreach uid,$(UIDS_BOX_SUITE),$(ASPECT_CONFIGS)/$(uid).material.prm)
PRMS_POSTPROCESS_BOX := $(foreach uid,$(UIDS_BOX_SUITE),$(ASPECT_CONFIGS)/$(uid).postprocess.prm)
PRMS_BOX             := $(foreach uid,$(UIDS_BOX_SUITE),$(ASPECT_CONFIGS)/$(uid).prm)

PRMS_GLOBALS_SINK     := $(foreach uid,$(UIDS_SINK_SUITE),$(ASPECT_CONFIGS)/$(uid).globals.prm)
PRMS_SOLVER_SINK      := $(foreach uid,$(UIDS_SINK_SUITE),$(ASPECT_CONFIGS)/$(uid).solver.prm)
PRMS_GEOMETRY_SINK    := $(foreach uid,$(UIDS_SINK_SUITE),$(ASPECT_CONFIGS)/$(uid).geometry.prm)
PRMS_BOUNDARY_SINK    := $(foreach uid,$(UIDS_SINK_SUITE),$(ASPECT_CONFIGS)/$(uid).boundary.prm)
PRMS_COMPOSITION_SINK := $(foreach uid,$(UIDS_SINK_SUITE),$(ASPECT_CONFIGS)/$(uid).composition.prm)
PRMS_INITIAL_SINK     := $(foreach uid,$(UIDS_SINK_SUITE),$(ASPECT_CONFIGS)/$(uid).initial.prm)
PRMS_PHYSICS_SINK     := $(foreach uid,$(UIDS_SINK_SUITE),$(ASPECT_CONFIGS)/$(uid).physics.prm)
PRMS_MATERIAL_SINK    := $(foreach uid,$(UIDS_SINK_SUITE),$(ASPECT_CONFIGS)/$(uid).material.prm)
PRMS_POSTPROCESS_SINK := $(foreach uid,$(UIDS_SINK_SUITE),$(ASPECT_CONFIGS)/$(uid).postprocess.prm)
PRMS_SINK             := $(foreach uid,$(UIDS_SINK_SUITE),$(ASPECT_CONFIGS)/$(uid).prm)

$(PRMS_GLOBALS_BOX) $(PRMS_GLOBALS_SINK): $(ASPECT_CONFIGS)/%.globals.prm: $(ASPECT_TEMPLATES)/NH/shared/globals.prm
	$(call GENERATE_NH_PRM,$<,$*,$@)
$(PRMS_SOLVER_BOX) $(PRMS_SOLVER_SINK): $(ASPECT_CONFIGS)/%.solver.prm: $(ASPECT_TEMPLATES)/NH/shared/solver.prm
	$(call GENERATE_NH_PRM,$<,$*,$@)
$(PRMS_MATERIAL_BOX) $(PRMS_MATERIAL_SINK): $(ASPECT_CONFIGS)/%.material.prm: $(ASPECT_TEMPLATES)/NH/shared/material.prm
	$(call GENERATE_NH_PRM,$<,$*,$@)
$(PRMS_POSTPROCESS_BOX) $(PRMS_POSTPROCESS_SINK): $(ASPECT_CONFIGS)/%.postprocess.prm: $(ASPECT_TEMPLATES)/NH/shared/postprocess.prm
	$(call GENERATE_NH_PRM,$<,$*,$@)

$(PRMS_GEOMETRY_BOX): $(ASPECT_CONFIGS)/%.geometry.prm: $(ASPECT_TEMPLATES)/NH/box/geometry.prm
	$(call GENERATE_NH_PRM,$<,$*,$@)
$(PRMS_BOUNDARY_BOX): $(ASPECT_CONFIGS)/%.boundary.prm: $(ASPECT_TEMPLATES)/NH/box/boundary.prm
	$(call GENERATE_NH_PRM,$<,$*,$@)
$(PRMS_COMPOSITION_BOX): $(ASPECT_CONFIGS)/%.composition.prm: $(ASPECT_TEMPLATES)/NH/box/composition.prm
	$(call GENERATE_NH_PRM,$<,$*,$@)
$(PRMS_INITIAL_BOX): $(ASPECT_CONFIGS)/%.initial.prm: $(ASPECT_TEMPLATES)/NH/box/initial.prm
	$(call GENERATE_NH_PRM,$<,$*,$@)
$(PRMS_PHYSICS_BOX): $(ASPECT_CONFIGS)/%.physics.prm: $(ASPECT_TEMPLATES)/NH/box/physics.prm
	$(call GENERATE_NH_PRM,$<,$*,$@)

$(PRMS_GEOMETRY_SINK): $(ASPECT_CONFIGS)/%.geometry.prm: $(ASPECT_TEMPLATES)/NH/sink/geometry.prm
	$(call GENERATE_NH_PRM,$<,$*,$@)
$(PRMS_BOUNDARY_SINK): $(ASPECT_CONFIGS)/%.boundary.prm: $(ASPECT_TEMPLATES)/NH/sink/boundary.prm
	$(call GENERATE_NH_PRM,$<,$*,$@)
$(PRMS_COMPOSITION_SINK): $(ASPECT_CONFIGS)/%.composition.prm: $(ASPECT_TEMPLATES)/NH/sink/composition.prm
	$(call GENERATE_NH_PRM,$<,$*,$@)
$(PRMS_INITIAL_SINK): $(ASPECT_CONFIGS)/%.initial.prm: $(ASPECT_TEMPLATES)/NH/sink/initial.prm
	$(call GENERATE_NH_PRM,$<,$*,$@)
$(PRMS_PHYSICS_SINK): $(ASPECT_CONFIGS)/%.physics.prm: $(ASPECT_TEMPLATES)/NH/sink/physics.prm
	$(call GENERATE_NH_PRM,$<,$*,$@)

$(PRMS_BOX): $(ASPECT_CONFIGS)/%.prm: $(ASPECT_TEMPLATES)/NH/box/top.prm
	$(call GENERATE_NH_PRM,$<,$*,$@)
$(PRMS_SINK): $(ASPECT_CONFIGS)/%.prm: $(ASPECT_TEMPLATES)/NH/sink/top.prm
	$(call GENERATE_NH_PRM,$<,$*,$@)
