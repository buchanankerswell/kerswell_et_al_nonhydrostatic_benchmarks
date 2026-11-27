# Minimal benchmark set: the main damping runs at Z_MID Res6
# plus timestep scaling (undamped Res6 at double CFL only — the halved-CFL
# sink run blows up deterministically in the initial transient, see
# project.mk). REGISTER_NH_SINK takes: list dynp dampkind dampval block
# (kg/m^3) z (1/s/K) res (level) [cfl]. dampval is plugin-side SI (no year
# conversion): s for Rel, Pa s for Bimpl/Bexpl, Pa for Cap. z stays 1/s/K.
# An empty cfl keeps the suite default (CFL_SINK, dimensionless).
$(eval $(call REGISTER_NH_SINK,UIDS_SINK_SUITE,1,none,0,400,$(Z_MID),6))
$(eval $(call REGISTER_NH_SINK,UIDS_SINK_SUITE,0,none,0,400,$(Z_MID),6))
$(eval $(call REGISTER_NH_SINK,UIDS_SINK_SUITE,1,Bimpl,1e19,400,$(Z_MID),6))
$(eval $(call REGISTER_NH_SINK,UIDS_SINK_SUITE,1,Bimpl,1e20,400,$(Z_MID),6))
$(eval $(call REGISTER_NH_SINK,UIDS_SINK_SUITE,1,Bexpl,1e19,400,$(Z_MID),6))
$(eval $(call REGISTER_NH_SINK,UIDS_SINK_SUITE,1,Rel,3.156e10,400,$(Z_MID),6))
$(eval $(call REGISTER_NH_SINK,UIDS_SINK_SUITE,1,Rel,3.156e11,400,$(Z_MID),6))
$(eval $(call REGISTER_NH_SINK,UIDS_SINK_SUITE,1,Cap,2e8,400,$(Z_MID),6))
$(eval $(call REGISTER_NH_SINK,UIDS_SINK_SUITE,1,none,0,400,$(Z_MID),6,1.0))

# Batch A: resolvable relaxed-pressure taus plus damped CFL0.25 rescue twins.
$(eval $(call REGISTER_NH_SINK,UIDS_SINK_SUITE,1,Rel,3.156e8,400,$(Z_MID),6))
$(eval $(call REGISTER_NH_SINK,UIDS_SINK_SUITE,1,Rel,3.156e9,400,$(Z_MID),6))
$(eval $(call REGISTER_NH_SINK,UIDS_SINK_SUITE,1,Rel,3.156e12,400,$(Z_MID),6))
$(eval $(call REGISTER_NH_SINK,UIDS_SINK_SUITE,1,Cap,2e8,400,$(Z_MID),6,0.25))
$(eval $(call REGISTER_NH_SINK,UIDS_SINK_SUITE,1,Bimpl,1e19,400,$(Z_MID),6,0.25))
$(eval $(call REGISTER_NH_SINK,UIDS_SINK_SUITE,1,Rel,3.156e11,400,$(Z_MID),6,0.25))

# Batch B: bulk and cap sensitivity at Res6.
$(eval $(call REGISTER_NH_SINK,UIDS_SINK_SUITE,1,Bimpl,1e18,400,$(Z_MID),6))
$(eval $(call REGISTER_NH_SINK,UIDS_SINK_SUITE,1,Bexpl,1e20,400,$(Z_MID),6))
$(eval $(call REGISTER_NH_SINK,UIDS_SINK_SUITE,1,Cap,1e8,400,$(Z_MID),6))
$(eval $(call REGISTER_NH_SINK,UIDS_SINK_SUITE,1,Cap,4e8,400,$(Z_MID),6))

# Batch C: mesh scaling (Res7 fine, Res5 coarse anchor).
$(eval $(call REGISTER_NH_SINK,UIDS_SINK_SUITE,1,none,0,400,$(Z_MID),7))
$(eval $(call REGISTER_NH_SINK,UIDS_SINK_SUITE,1,Cap,2e8,400,$(Z_MID),7))
$(eval $(call REGISTER_NH_SINK,UIDS_SINK_SUITE,1,Rel,3.156e11,400,$(Z_MID),7))
$(eval $(call REGISTER_NH_SINK,UIDS_SINK_SUITE,1,Bimpl,1e19,400,$(Z_MID),7))
$(eval $(call REGISTER_NH_SINK,UIDS_SINK_SUITE,1,none,0,400,$(Z_MID),5))
$(eval $(call REGISTER_NH_SINK,UIDS_SINK_SUITE,1,Cap,2e8,400,$(Z_MID),5))

# Batch D: kinetic decoupling (DynpDens), no-feedback reference twins across
# mesh and CFL sweeps, Rel ladder completion at Res5 and CFL1.0, tau threshold
# brackets (30 yr, 300 yr), and kinetic prefactor Z sweep (Z_LO, Z_HI).
$(eval $(call REGISTER_NH_SINK,UIDS_SINK_SUITE,dens,none,0,400,$(Z_MID),6))
$(eval $(call REGISTER_NH_SINK,UIDS_SINK_SUITE,0,none,0,400,$(Z_MID),5))
$(eval $(call REGISTER_NH_SINK,UIDS_SINK_SUITE,0,none,0,400,$(Z_MID),7))
$(eval $(call REGISTER_NH_SINK,UIDS_SINK_SUITE,0,none,0,400,$(Z_MID),6,0.25))
$(eval $(call REGISTER_NH_SINK,UIDS_SINK_SUITE,0,none,0,400,$(Z_MID),6,1.0))
$(eval $(call REGISTER_NH_SINK,UIDS_SINK_SUITE,1,Rel,3.156e11,400,$(Z_MID),5))
$(eval $(call REGISTER_NH_SINK,UIDS_SINK_SUITE,1,Rel,3.156e11,400,$(Z_MID),6,1.0))
$(eval $(call REGISTER_NH_SINK,UIDS_SINK_SUITE,1,Rel,9.468e8,400,$(Z_MID),6))
$(eval $(call REGISTER_NH_SINK,UIDS_SINK_SUITE,1,Rel,9.468e9,400,$(Z_MID),6))
$(eval $(call REGISTER_NH_SINK,UIDS_SINK_SUITE,1,none,0,400,$(Z_LO),6))
$(eval $(call REGISTER_NH_SINK,UIDS_SINK_SUITE,0,none,0,400,$(Z_LO),6))
$(eval $(call REGISTER_NH_SINK,UIDS_SINK_SUITE,1,Rel,3.156e11,400,$(Z_LO),6))
$(eval $(call REGISTER_NH_SINK,UIDS_SINK_SUITE,1,none,0,400,$(Z_HI),6))
$(eval $(call REGISTER_NH_SINK,UIDS_SINK_SUITE,0,none,0,400,$(Z_HI),6))
$(eval $(call REGISTER_NH_SINK,UIDS_SINK_SUITE,1,Rel,3.156e11,400,$(Z_HI),6))

$(foreach id,$(ID_S1) $(ID_S2) $(ID_S3) $(ID_S4) $(ID_S5) $(ID_S6) $(ID_S7) $(ID_S8) $(ID_SCFL10) $(ID_S9) $(ID_S10) $(ID_S11) $(ID_S12) $(ID_S13) $(ID_S14) $(ID_S15) $(ID_S16) $(ID_S17) $(ID_S18) $(ID_S19) $(ID_S20) $(ID_S21) $(ID_S22) $(ID_S23) $(ID_S24) $(ID_S25) $(ID_S26) $(ID_S27) $(ID_S28) $(ID_S29) $(ID_S30) $(ID_S31) $(ID_S32) $(ID_S33) $(ID_S34) $(ID_S35) $(ID_S36) $(ID_S37) $(ID_S38) $(ID_S39),$(if $(filter $(id),$(UIDS_SINK_SUITE)),,$(error !! UID $(id) not registered in UIDS_SINK_SUITE)))

ASPECT_DATA      := $(SIMULATION)/data
ASPECT_TEMPLATES := $(SIMULATION)/params/templates
ASPECT_CONFIGS   := $(SIMULATION)/configs
ASPECT_PLUGIN    := $(SIMULATION)/plugins/build/libnh-kinetics.release.so \
                    $(SIMULATION)/plugins/build/libnh-kinetics.debug.so \
                    $(SIMULATION)/plugins/build/CMakeFiles \
                    $(SIMULATION)/plugins/build/Makefile \
                    $(SIMULATION)/plugins/build/CMakeCache.txt \
                    $(SIMULATION)/plugins/build/cmake_install.cmake \
                    $(SIMULATION)/plugins/build/compile_commands.json

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

$(PRMS_GLOBALS_SINK): $(ASPECT_CONFIGS)/%.globals.prm: $(ASPECT_TEMPLATES)/NH/shared/globals.prm
	$(call GENERATE_NH_PRM,$<,$*,$@)
$(PRMS_SOLVER_SINK): $(ASPECT_CONFIGS)/%.solver.prm: $(ASPECT_TEMPLATES)/NH/shared/solver.prm
	$(call GENERATE_NH_PRM,$<,$*,$@)
$(PRMS_MATERIAL_SINK): $(ASPECT_CONFIGS)/%.material.prm: $(ASPECT_TEMPLATES)/NH/shared/material.prm
	$(call GENERATE_NH_PRM,$<,$*,$@)
$(PRMS_POSTPROCESS_SINK): $(ASPECT_CONFIGS)/%.postprocess.prm: $(ASPECT_TEMPLATES)/NH/shared/postprocess.prm
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

$(PRMS_SINK): $(ASPECT_CONFIGS)/%.prm: $(ASPECT_TEMPLATES)/NH/sink/top.prm
	$(call GENERATE_NH_PRM,$<,$*,$@)
