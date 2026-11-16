/*
  Copyright (C) 2011 - 2025 by the authors of the ASPECT code.

  This file is part of ASPECT.

  ASPECT is free software; you can redistribute it and/or modify
  it under the terms of the GNU General Public License as published by
  the Free Software Foundation; either version 2, or (at your option)
  any later version.

  ASPECT is distributed in the hope that it will be useful,
  but WITHOUT ANY WARRANTY; without even the implied warranty of
  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
  GNU General Public License for more details.

  You should have received a copy of the GNU General Public License
  along with ASPECT; see the file LICENSE.  If not see
  <http://www.gnu.org/licenses/>.
*/

#ifndef _aspect_nh_kinetics_h
#define _aspect_nh_kinetics_h

#include <deal.II/base/patterns.h>
#include <deal.II/base/types.h>

#include <aspect/adiabatic_conditions/interface.h>
#include <aspect/geometry_model/interface.h>
#include <aspect/material_model/reaction_model/reaction_chain.h>
#include <aspect/material_model/interface.h>
#include <aspect/simulator_access.h>
#include <aspect/utilities.h>

#include <string>
#include <vector>

namespace aspect
{
  namespace MaterialModel
  {
    /**
     * A compressible material model that implements 1-3 phase transformations
     * as a ReactionChain (ol-wd, wd-ri, ri-ps), driven by dynamic
     * (non-hydrostatic) pressure for non-hydrostatic benchmark experiments.
     *
     * The chain length N is set by the "Reaction chain/Kinetic models" list;
     * the model expects exactly N cumulative reaction progress fields plus an
     * optional projected "density_field" and an optional "relaxed_pressure"
     * field (relaxed-pressure variant). Per-reaction thermodynamic reference
     * data come from ASCII .tsv profiles. Non-hydrostatic extensions:
     * relaxed dynamic-pressure driving force, explicit bulk-viscosity Stokes
     * RHS force, and a capped dynamic-pressure correction.
     *
     * Unlike the upstream MTZ kinetics cookbook, kinetic prefactors Z are
     * entered in SI units (1/s/K, 1/s/K-style) and used directly: ASPECT's
     * operator splitter integrates in seconds, so no year conversion is
     * applied. (The cookbook divides by year_in_seconds; see the note in
     * evaluate().)
     *
     * Viscosity uses per-phase prefactors blended via tanh transitions
     * centred on the equilibrium phase boundaries (dG = 0), decoupled from
     * the kinetic phase fields.
     *
     * @ingroup MaterialModels
     */
    template <int dim>
    class NHKinetics : public MaterialModel::Interface<dim>, public ::aspect::SimulatorAccess<dim>
    {
      public:
        NHKinetics();

        void
        initialize() override;

        bool
        is_compressible() const override;

        void
        evaluate(const MaterialModel::MaterialModelInputs<dim> &in, MaterialModel::MaterialModelOutputs<dim> &out) const override;

        void
        clamp_reaction_progress_fields(MaterialModel::MaterialModelInputs<dim> &in) const override;

        static void
        declare_parameters(ParameterHandler &prm);

        void
        parse_parameters(ParameterHandler &prm) override;

        void
        create_additional_named_outputs(MaterialModel::MaterialModelOutputs<dim> &out) const override;

      private:
        /**
         * Reaction chain manager configuring kinetic models for the
         * sequential phase transitions.
         */
        ReactionModel::ReactionChain<dim> reaction_chain;

        /**
         * Array of ASCII data profiles storing the thermodynamic and physical
         * data for each reaction.
         */
        std::vector<Utilities::AsciiDataProfile<dim>> profiles;

        /**
         * Data directory and per-reaction file names for the ASCII profiles.
         */
        std::string data_directory;
        std::vector<std::string> data_file_names;

        /**
         * Per-phase material property column indices.
         */
        std::vector<unsigned int> rho_idx, alpha_idx, beta_idx, cp_idx;
        std::vector<unsigned int> Vp_idx, Vs_idx, dVp_dT_idx, dVs_dT_idx;

        /**
         * Per-reaction thermodynamic property column indices.
         */
        std::vector<unsigned int> dG_idx, dS_idx, dV_idx;

        /**
         * Cached indices of the cumulative reaction progress fields
         * (all compositional fields except density_field/relaxed_pressure).
         */
        std::vector<unsigned int> reaction_field_indices;

        /**
         * Reference viscosity. Units: Pa s
         */
        double viscosity;

        /**
         * Minimum and maximum viscosity cutoffs. Units: Pa s
         */
        double minimum_viscosity;
        double maximum_viscosity;

        /**
         * Exponent A in the temperature dependence exp(-A * (T - T_ref) / T_ref).
         * Dimensionless
         */
        double thermal_viscosity_exponent;

        /**
         * Per-phase viscosity prefactors, one per phase (n_reactions + 1).
         * Dimensionless
         */
        std::vector<double> phase_viscosity_prefactors;

        /**
         * Width of the tanh viscosity transition in Gibbs free energy space.
         * Units: J/mol
         */
        double gibbs_viscosity_width;

        /**
         * Reference thermal conductivity. Units: W/m/K
         */
        double k;

        bool use_dynamic_pressure_correction_for_density;
        bool use_dynamic_pressure_correction_for_gibbs;

        /**
         * Relaxation time for the low-pass-filtered (relaxed) dynamic pressure
         * used as the reaction driving pressure (relaxed-pressure variant).
         * Units: s. Zero disables relaxation.
         */
        double relaxation_time_dynamic_pressure;

        /**
         * Explicit bulk viscosity for the lagged Stokes RHS damping force
         * (explicit-bulk variant). Units: Pa s. Zero disables the force.
         */
        double bulk_viscosity_explicit;

        /**
         * Magnitude cap on the dynamic pressure correction (P_drive - P_ref)
         * applied to density and Gibbs energy (capped-pressure variant).
         * Units: Pa. Zero or negative disables capping.
         */
        double max_dynamic_pressure_correction;

        /**
         * Prescribed density excess carried by the compositional 'block'
         * field (sinking-block benchmark scaffolding: a dense anomaly that
         * sinks through the phase horizon). Units: kg/m^3. Zero disables it.
         */
        double block_density_excess;
    };



    /**
     * Additional output fields for the NHKinetics material model.
     */
    template <int dim>
    class NHKineticsOutputs : public NamedAdditionalMaterialOutputs<dim>
    {
      public:
        NHKineticsOutputs(const unsigned int n_points,
                          const unsigned int n_phases,
                          const unsigned int n_reactions);

        std::vector<double>
        get_nth_output(const unsigned int idx) const override;

        /**
         * Viscosity temperature dependence term exp(-A * (T - T_ref) / T_ref).
         * Dimensionless
         */
        std::vector<double> visc_temperature_dependence;

        /**
         * Phase mass fractions [phase][point]. Dimensionless
         */
        std::vector<std::vector<double>> phase_mass_fractions;

        /**
         * Corrected Gibbs driving energy actually used for each reaction
         * (dG_ref + dynamic-pressure term - thermal term) [reaction][point].
         * Units: J/mol
         */
        std::vector<std::vector<double>> corrected_gibbs;

      private:
        unsigned int n_phases;
        unsigned int n_reactions;
    };
  } // namespace MaterialModel
} // namespace aspect

#endif
