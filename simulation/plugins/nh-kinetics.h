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
     * Material model for phase changes with finite reaction speed
     * (olivine-wadsleyite and deeper transitions). Rate prefactors Z are
     * SI rates, used as-is. Viscosity follows equilibrium stability,
     * not reaction progress.
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
        // Reaction chain and per-reaction thermodynamic tables.
        ReactionModel::ReactionChain<dim> reaction_chain;

        /**
         * Column indices into the tables, resolved in initialize().
         */
        std::vector<Utilities::AsciiDataProfile<dim>> profiles;

        /**
         * Data directory and per-reaction file names for the ASCII profiles.
         */
        std::string data_directory;
        std::vector<std::string> data_file_names;

        // Table column indices, resolved in initialize().
        std::vector<unsigned int> rho_idx, alpha_idx, beta_idx, cp_idx;
        std::vector<unsigned int> Vp_idx, Vs_idx, dVp_dT_idx, dVs_dT_idx;
        std::vector<unsigned int> dG_idx, dS_idx, dV_idx;

        // Indices of the reaction progress fields.
        std::vector<unsigned int> reaction_field_indices;

        // Reference viscosity. Units: Pa s
        double viscosity;

        // Viscosity floor and ceiling. Units: Pa s
        double minimum_viscosity;
        double maximum_viscosity;

        // Exponent in exp(-A*(T-T_ref)/T_ref). Units: none
        double thermal_viscosity_exponent;

        // Per-phase prefactors. Units: none
        std::vector<double> phase_viscosity_prefactors;

        // Smoothing width of the viscosity switch in Gibbs energy. Units: J/mol
        double gibbs_viscosity_width;

        // Reference thermal conductivity. Units: W/m/K
        double k;

        bool use_dynamic_pressure_correction_for_density;
        bool use_dynamic_pressure_correction_for_gibbs;

        // Relaxation time. Units: s (model seconds, not years). Zero disables it.
        double relaxation_time_dynamic_pressure;

        // Explicit bulk viscosity. Units: Pa s. Zero disables it.
        double bulk_viscosity_explicit;

        // Upper limit on the driving pressure. Units: Pa. Zero or negative disables it.
        double max_dynamic_pressure_correction;

        // Extra density where the block field is 1. Units: kg/m^3.
        // Zero disables it.
        double block_density_excess;

        // Ambient (block-free) reference: subtract the static block load
        // that the 1D adiabat includes. No effect when the excess above is zero.
        bool use_ambient_reference_column;

        // Block top and bottom y. Units: m. Must match the initial composition.
        double ambient_block_top_y;
        double ambient_block_bottom_y;

        // Gravity for the load correction. Units: m/s^2
        double gravity_magnitude;
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
