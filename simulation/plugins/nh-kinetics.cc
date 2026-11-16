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

#include "nh-kinetics.h"

#include <deal.II/base/numbers.h>
#include <deal.II/base/parameter_handler.h>
#include <deal.II/base/patterns.h>
#include <deal.II/base/point.h>

#include <aspect/global.h>

#include <cmath>
#include <string>
#include <vector>

namespace aspect
{
  namespace MaterialModel
  {
    template <int dim>
    NHKinetics<dim>::NHKinetics() = default;



    template <int dim>
    void
    NHKinetics<dim>::initialize()
    {
      reaction_chain.initialize_simulator(this->get_simulator());
      reaction_chain.initialize();

      const unsigned int n_reactions = reaction_chain.n_reactions();
      const unsigned int n_phases    = n_reactions + 1;

      reaction_field_indices.clear();
      for (unsigned int c = 0; c < this->introspection().n_compositional_fields; ++c)
        {
          // Chain progress variables are exactly the xi_* fields; auxiliary
          // fields (density_field, relaxed_pressure, block, ...) are excluded.
          const std::string field_name = this->introspection().name_for_compositional_index(c);
          if (field_name.rfind("xi_", 0) == 0)
            reaction_field_indices.push_back(c);
        }

      AssertThrow(reaction_field_indices.size() == n_reactions,
                  ExcMessage("The number of xi_* cumulative reaction progress fields does not match "
                             "the number of reactions in the chain."));

      // Size property index arrays
      rho_idx.assign(n_phases, numbers::invalid_unsigned_int);
      alpha_idx.assign(n_phases, numbers::invalid_unsigned_int);
      beta_idx.assign(n_phases, numbers::invalid_unsigned_int);
      cp_idx.assign(n_phases, numbers::invalid_unsigned_int);
      Vp_idx.assign(n_phases, numbers::invalid_unsigned_int);
      Vs_idx.assign(n_phases, numbers::invalid_unsigned_int);
      dVp_dT_idx.assign(n_phases, numbers::invalid_unsigned_int);
      dVs_dT_idx.assign(n_phases, numbers::invalid_unsigned_int);

      dG_idx.assign(n_reactions, numbers::invalid_unsigned_int);
      dS_idx.assign(n_reactions, numbers::invalid_unsigned_int);
      dV_idx.assign(n_reactions, numbers::invalid_unsigned_int);

      // Initialize profiles and assign indices
      for (unsigned int r = 0; r < n_reactions; ++r)
        {
          profiles[r].initialize(this->get_mpi_communicator());

          dG_idx[r] = profiles[r].get_column_index_from_name("delta_molar_gibbs");
          dS_idx[r] = profiles[r].get_column_index_from_name("delta_molar_entropy");
          dV_idx[r] = profiles[r].get_column_index_from_name("delta_molar_volume");
        }

      for (unsigned int p = 0; p < n_phases; ++p)
        {
          const bool from_a        = (p == 0);
          const unsigned int r     = from_a ? 0 : p - 1;
          const std::string suffix = from_a ? "_a" : "_b";

          rho_idx[p]    = profiles[r].get_column_index_from_name("density" + suffix);
          alpha_idx[p]  = profiles[r].get_column_index_from_name("thermal_expansivity" + suffix);
          beta_idx[p]   = profiles[r].get_column_index_from_name("compressibility" + suffix);
          cp_idx[p]     = profiles[r].get_column_index_from_name("specific_heat" + suffix);
          Vp_idx[p]     = profiles[r].maybe_get_column_index_from_name("pressure_wave_velocity" + suffix);
          dVp_dT_idx[p] = profiles[r].maybe_get_column_index_from_name("pressure_wave_velocity_T_derivative" + suffix);
          Vs_idx[p]     = profiles[r].maybe_get_column_index_from_name("shear_wave_velocity" + suffix);
          dVs_dT_idx[p] = profiles[r].maybe_get_column_index_from_name("shear_wave_velocity_T_derivative" + suffix);
        }
    }



    template <int dim>
    bool
    NHKinetics<dim>::is_compressible() const
    {
      return true;
    }



    template <int dim>
    void
    NHKinetics<dim>::evaluate(const MaterialModel::MaterialModelInputs<dim> &in, MaterialModel::MaterialModelOutputs<dim> &out) const
    {
      // Set up additional output objects
      std::shared_ptr<PrescribedFieldOutputs<dim>>   prescribed_field_out = out.template get_additional_output_object<PrescribedFieldOutputs<dim>>();
      std::shared_ptr<ReactionRateOutputs<dim>>      reaction_rate_out    = out.template get_additional_output_object<ReactionRateOutputs<dim>>();
      std::shared_ptr<NHKineticsOutputs<dim>>       nh_kinetics_out     = out.template get_additional_output_object<NHKineticsOutputs<dim>>();
      std::shared_ptr<SeismicAdditionalOutputs<dim>> seismic_out = out.template get_additional_output_object<SeismicAdditionalOutputs<dim>>();
      std::shared_ptr<MaterialModel::AdditionalMaterialOutputsStokesRHS<dim>> stokes_rhs_out =
        out.template get_additional_output_object<MaterialModel::AdditionalMaterialOutputsStokesRHS<dim>>();

      const unsigned int n_reactions = reaction_chain.n_reactions();
      const unsigned int n_phases    = n_reactions + 1;

      const bool output_diagnostics  = (nh_kinetics_out != nullptr);

      // Get compositional field indices
      const unsigned int projected_density_idx = this->introspection().compositional_name_exists("density_field")
                                                 ? this->introspection().compositional_index_for_name("density_field")
                                                 : numbers::invalid_unsigned_int;
      const unsigned int relaxed_pressure_idx = (relaxation_time_dynamic_pressure > 0.0 &&
                                                 this->introspection().compositional_name_exists("relaxed_pressure"))
                                                ? this->introspection().compositional_index_for_name("relaxed_pressure")
                                                : numbers::invalid_unsigned_int;

      for (unsigned int q = 0; q < in.n_evaluation_points(); ++q)
        {
          const Point<dim> position = in.position[q];

          const double P = in.pressure[q];
          const double T = in.temperature[q];

          const double   P_ref = this->get_adiabatic_conditions().pressure(position);
          const double   T_ref = this->get_adiabatic_conditions().temperature(position);
          const Point<1> profile_pos(P_ref);

          // Non-hydrostatic driving pressure (relaxed-pressure variant):
          // reactions see the low-pass-filtered pressure when enabled, else
          // the instantaneous Stokes pressure. The deviation from the adiabat
          // is capped (capped-pressure variant) when requested.
          double p_drive = P;
          if (relaxed_pressure_idx != numbers::invalid_unsigned_int)
            p_drive = in.composition[q][relaxed_pressure_idx];
          double dynamic_pressure = p_drive - P_ref;
          if (max_dynamic_pressure_correction > 0.0)
            dynamic_pressure = std::clamp(dynamic_pressure,
                                          -max_dynamic_pressure_correction,
                                          max_dynamic_pressure_correction);

          // Explicit bulk-viscosity damping force (explicit-bulk variant).
          // Penalty on the divergence rate: rhs_p = +(zeta/eta_ref)*div(u_old),
          // assembled into the continuity equation. Requires strain-rate
          // input; silently does nothing without it.
          if (stokes_rhs_out != nullptr && bulk_viscosity_explicit > 0.0 && in.requests_property(MaterialProperties::additional_outputs))
            {
              double div_u = 0.0;
              if (q < in.strain_rate.size())
                {
                  const double tr = trace(in.strain_rate[q]);
                  if (!std::isnan(tr))
                    div_u = tr;
                }
              stokes_rhs_out->rhs_p[q] =
                (bulk_viscosity_explicit / viscosity) * div_u;
            }

          // Initialize reaction rates to zero for all compositional fields
          if (reaction_rate_out != nullptr)
            for (unsigned int c = 0; c < this->introspection().n_compositional_fields; ++c)
              reaction_rate_out->reaction_rates[q][c] = 0.0;

          // Get cumulative reaction progress from compositional fields
          std::vector<double> reaction_progress_values(n_reactions);
          for (unsigned int r = 0; r < n_reactions; ++r)
            reaction_progress_values[r] = in.composition[q][reaction_field_indices[r]];

          // Ensure physical range [0, 1] and monotonicity xi[i] <= xi[i-1]
          const std::vector<double> reaction_progress_clamped = reaction_chain.clamp_cumulative_progress(reaction_progress_values);

          // Storage for all phases
          std::vector<double> densities(n_phases, 0.0);
          std::vector<double> alphas(n_phases, 0.0);
          std::vector<double> betas(n_phases, 0.0);
          std::vector<double> cps(n_phases, 0.0);
          std::vector<double> Vps(n_phases, 0.0);
          std::vector<double> Vss(n_phases, 0.0);

          // Get properties from profiles (phase p comes from reaction 0 side
          // _a for p == 0, else from reaction p-1 side _b)
          for (unsigned int p = 0; p < n_phases; ++p)
            {
              const bool from_a    = (p == 0);
              const unsigned int r = from_a ? 0 : p - 1;

              densities[p] = profiles[r].get_data_component(profile_pos, rho_idx[p]);
              alphas[p]    = profiles[r].get_data_component(profile_pos, alpha_idx[p]);
              betas[p]     = profiles[r].get_data_component(profile_pos, beta_idx[p]);
              cps[p]       = profiles[r].get_data_component(profile_pos, cp_idx[p]);

              if (seismic_out != nullptr && Vp_idx[p] != numbers::invalid_unsigned_int)
                {
                  Vps[p] = profiles[r].get_data_component(profile_pos, Vp_idx[p]);
                  if (dVp_dT_idx[p] != numbers::invalid_unsigned_int)
                    Vps[p] += profiles[r].get_data_component(profile_pos, dVp_dT_idx[p]) * (T - T_ref);
                }
              if (seismic_out != nullptr && Vs_idx[p] != numbers::invalid_unsigned_int)
                {
                  Vss[p] = profiles[r].get_data_component(profile_pos, Vs_idx[p]);
                  if (dVs_dT_idx[p] != numbers::invalid_unsigned_int)
                    Vss[p] += profiles[r].get_data_component(profile_pos, dVs_dT_idx[p]) * (T - T_ref);
                }
            }

          // Compute phase mass fractions from cumulative reaction progress
          const std::vector<double> mass_fractions = reaction_chain.compute_phase_mass_fractions(reaction_progress_clamped, densities);

          if (output_diagnostics)
            for (unsigned int p = 0; p < n_phases; ++p)
              nh_kinetics_out->phase_mass_fractions[p][q] = mass_fractions[p];

          // Compute volume fractions from mass fractions
          const std::vector<double> volume_fractions = MaterialUtilities::compute_volumes_from_masses(mass_fractions, densities, true);

          // Average density, thermal expansivity, compressibility (volume-weighted)
          const double rho_avg   = MaterialUtilities::average_value(volume_fractions, densities, MaterialUtilities::arithmetic);
          const double alpha_avg = MaterialUtilities::average_value(volume_fractions, alphas, MaterialUtilities::arithmetic);
          const double beta_avg  = MaterialUtilities::average_value(volume_fractions, betas, MaterialUtilities::arithmetic);

          // Average specific heat (mass-weighted)
          const double cp_avg = MaterialUtilities::average_value(mass_fractions, cps, MaterialUtilities::arithmetic);

          // Average seismic velocities (volume-weighted)
          if (seismic_out != nullptr && in.requests_property(MaterialProperties::additional_outputs))
            {
              if (Vps[0] > 0.0)
                seismic_out->vp[q] = MaterialUtilities::average_value(volume_fractions, Vps, MaterialUtilities::arithmetic);
              if (Vss[0] > 0.0)
                seismic_out->vs[q] = MaterialUtilities::average_value(volume_fractions, Vss, MaterialUtilities::arithmetic);
            }

          out.densities[q]                      = rho_avg;
          out.thermal_expansion_coefficients[q] = alpha_avg;
          out.compressibilities[q]              = beta_avg;
          out.thermal_conductivities[q]         = k;
          out.specific_heat[q]                  = cp_avg;
          out.entropy_derivative_pressure[q]    = 0.0;
          out.entropy_derivative_temperature[q] = 0.0;

          // Apply temperature and pressure corrections to density
          const double temperature_correction_density = (T - T_ref) * alpha_avg;
          const double pressure_correction_density    = use_dynamic_pressure_correction_for_density ? dynamic_pressure * beta_avg : 0.0;
          const double density_factor                 = (1.0 - temperature_correction_density) * (1.0 + pressure_correction_density);
          out.densities[q]                            = rho_avg * density_factor;

          // Sinking-block scaffolding: prescribed density excess carried by
          // the compositional 'block' field. Zero when the field is absent.
          if (this->introspection().compositional_name_exists("block"))
            out.densities[q] += block_density_excess * in.composition[q][this->introspection().compositional_index_for_name("block")];

          // Compute viscosity temperature dependence: exp(-A * (T - T_ref) / T_ref)
          double visc_temperature_dependence = std::max(std::min(std::exp(-thermal_viscosity_exponent * (T - T_ref) / T_ref), 1e3), 1e-3);
          if (std::isnan(visc_temperature_dependence))
            visc_temperature_dependence = 1.0;

          if (output_diagnostics)
            nh_kinetics_out->visc_temperature_dependence[q] = visc_temperature_dependence;

          // Compute viscosity with Gibbs-anchored phase prefactors.
          // Transition fractions f_r -> 1 when the high-pressure phase is
          // stable (dG < 0); chained into mutually exclusive stability
          // fractions (partition of unity), decoupled from the kinetic fields.
          if (in.requests_property(MaterialProperties::viscosity))
            {
              const double w = gibbs_viscosity_width;

              std::vector<double> f_transition(n_reactions, 0.0);
              for (unsigned int r = 0; r < n_reactions; ++r)
                {
                  const double dG_val = profiles[r].get_data_component(profile_pos, dG_idx[r]);
                  f_transition[r] = 0.5 * (1.0 - std::tanh(dG_val / w));
                }

              std::vector<double> phi(n_phases, 1.0);
              double accumulated_prod = 1.0;
              for (unsigned int p = 0; p < n_phases; ++p)
                {
                  if (p == 0)
                    phi[p] = 1.0 - f_transition[0];
                  else if (p < n_reactions)
                    {
                      accumulated_prod *= f_transition[p - 1];
                      phi[p] = accumulated_prod * (1.0 - f_transition[p]);
                    }
                  else
                    {
                      accumulated_prod *= f_transition[p - 1];
                      phi[p] = accumulated_prod;
                    }
                }

              double log_prefactor = 0.0;
              for (unsigned int p = 0; p < n_phases; ++p)
                log_prefactor += phi[p] * std::log(phase_viscosity_prefactors[p]);

              const double visc_depth_dependence = std::exp(log_prefactor);
              const double eta                   = viscosity * visc_temperature_dependence * visc_depth_dependence;
              out.viscosities[q]                 = std::min(std::max(eta, minimum_viscosity), maximum_viscosity);
            }

          // Evaluate reaction rates and driving energies.
          //
          // NOTE on units: the chain returns SI rates (s^-1) and the operator
          // splitter integrates in seconds, so kinetic prefactors Z are
          // entered directly in SI units (e.g. Z = 4.44e-04 1/s/K gives the
          // same effective kinetics as the cookbook's Z = 1.4e+04 divided by
          // year_in_seconds). No time conversion is applied here; the
          // cookbook's division is arguably a units bug, flagged for a
          // separate upstream fix.
          if (reaction_rate_out != nullptr &&
              (in.requests_property(MaterialProperties::reaction_rates) ||
               in.requests_property(MaterialProperties::additional_outputs)))
            {
              for (unsigned int r = 0; r < n_reactions; ++r)
                {
                  const double dG_ref = profiles[r].get_data_component(profile_pos, dG_idx[r]);
                  const double dS     = profiles[r].get_data_component(profile_pos, dS_idx[r]);
                  const double dV     = profiles[r].get_data_component(profile_pos, dV_idx[r]);

                  const double gibbs_driving = dG_ref
                                               + (use_dynamic_pressure_correction_for_gibbs ? dynamic_pressure * dV : 0.0)
                                               - (T - T_ref) * dS;

                  if (output_diagnostics)
                    nh_kinetics_out->corrected_gibbs[r][q] = gibbs_driving;

                  reaction_rate_out->reaction_rates[q][reaction_field_indices[r]] =
                    reaction_chain.net_forward_reaction_rate(T, P, gibbs_driving, reaction_progress_clamped[r], r);
                }
            }

          for (unsigned int c = 0; c < this->introspection().n_compositional_fields; ++c)
            out.reaction_terms[q][c] = 0.0;
        }

      // Calculate projected density reaction terms
      if (projected_density_idx != numbers::invalid_unsigned_int)
        for (unsigned int q = 0; q < in.n_evaluation_points(); ++q)
          out.reaction_terms[q][projected_density_idx] = out.densities[q] - in.composition[q][projected_density_idx];

      // Relax the dynamic pressure field toward the instantaneous Stokes
      // pressure: d(p_bar)/dt = (P - p_bar) / tau_rel, integrated by the
      // operator-splitting reaction solver like the xi fields.
      if (relaxed_pressure_idx != numbers::invalid_unsigned_int && reaction_rate_out != nullptr)
        for (unsigned int q = 0; q < in.n_evaluation_points(); ++q)
          reaction_rate_out->reaction_rates[q][relaxed_pressure_idx] =
            (in.pressure[q] - in.composition[q][relaxed_pressure_idx]) / relaxation_time_dynamic_pressure;

      // Update projected density field
      if (prescribed_field_out != nullptr && projected_density_idx != numbers::invalid_unsigned_int)
        for (unsigned int i = 0; i < in.position.size(); ++i)
          prescribed_field_out->prescribed_field_outputs[i][projected_density_idx] = out.densities[i];
    }



    template <int dim>
    void
    NHKinetics<dim>::clamp_reaction_progress_fields(MaterialModel::MaterialModelInputs<dim> &in) const
    {
      const unsigned int n_reactions = reaction_chain.n_reactions();

      for (unsigned int q = 0; q < in.n_evaluation_points(); ++q)
        {
          std::vector<double> reaction_progress_values(n_reactions);
          for (unsigned int r = 0; r < n_reactions; ++r)
            reaction_progress_values[r] = in.composition[q][reaction_field_indices[r]];

          const std::vector<double> reaction_progress_clamped = reaction_chain.clamp_cumulative_progress(reaction_progress_values);

          for (unsigned int r = 0; r < n_reactions; ++r)
            in.composition[q][reaction_field_indices[r]] = reaction_progress_clamped[r];
        }
    }



    template <int dim>
    void
    NHKinetics<dim>::declare_parameters(ParameterHandler &prm)
    {
      prm.enter_subsection("Material model");
      {
        prm.enter_subsection("NH kinetics");
        {
          ReactionModel::ReactionChain<dim>::declare_parameters(prm);

          prm.declare_entry("Data directory",
                            "simulation/benchmark_data/",
                            Patterns::DirectoryName(),
                            "Directory containing the per-reaction thermodynamic data profiles.");
          prm.declare_entry("Data file names",
                            "olivine-wadsleyite-profile-Mg100.tsv",
                            Patterns::List(Patterns::Anything()),
                            "'|'-separated list of thermodynamic data files, one per reaction.");

          prm.enter_subsection("Ascii data model");
          {
            Utilities::AsciiDataProfile<dim>::declare_parameters(prm,
                                                                 "simulation/benchmark_data/",
                                                                 "olivine-wadsleyite-profile-Mg100.tsv");
          }
          prm.leave_subsection();

          prm.declare_entry("Viscosity", "1e21", Patterns::Double(0.), "Reference viscosity. Units: Pa s");
          prm.declare_entry("Minimum viscosity", "1e19", Patterns::Double(0.), "Minimum viscosity cutoff. Units: Pa s");
          prm.declare_entry("Maximum viscosity", "1e24", Patterns::Double(0.), "Maximum viscosity cutoff. Units: Pa s");
          prm.declare_entry("Thermal viscosity exponent", "0.0", Patterns::Double(0.), "Exponent A in exp(-A*(T-T_ref)/T_ref). Dimensionless.");
          prm.declare_entry("Phase viscosity prefactors",
                            "1.0, 1.0",
                            Patterns::List(Patterns::Double(0.)),
                            "Comma-separated list of dimensionless viscosity prefactors, one per phase (n_reactions + 1).");
          prm.declare_entry("Gibbs viscosity width",
                            "1000.0",
                            Patterns::Double(0.),
                            "Width of the tanh viscosity transition in Gibbs free energy space. Units: J/mol");

          prm.declare_entry("Thermal conductivity", "4.0", Patterns::Double(0.), "Reference thermal conductivity. Units: W/m/K");

          prm.declare_entry("Use dynamic pressure correction for density", "true", Patterns::Bool(), "Apply dynamic pressure correction to density.");
          prm.declare_entry("Use dynamic pressure correction for gibbs",
                            "false",
                            Patterns::Bool(),
                            "Apply dynamic pressure correction to Gibbs free energy.");

          prm.declare_entry("Relaxation time for dynamic pressure",
                            "0.0",
                            Patterns::Double(0.),
                            "Relaxation time tau_rel for the low-pass-filtered dynamic pressure (relaxed-pressure variant). "
                            "Reactions are driven by the relaxed pressure field 'relaxed_pressure', which must be "
                            "defined as a compositional field. Units: s. Zero disables relaxation.");
          prm.declare_entry("Explicit bulk viscosity",
                            "0.0",
                            Patterns::Double(0.),
                            "Explicit bulk viscosity zeta for the lagged Stokes RHS damping force (explicit-bulk variant). "
                            "Requires 'Enable additional Stokes RHS' in the Formulation section. "
                            "Stable for zeta below the shear viscosity. Units: Pa s. Zero disables the force.");
          prm.declare_entry("Maximum dynamic pressure correction",
                            "0.0",
                            Patterns::Double(0.),
                            "Magnitude cap on (P_drive - P_ref) applied to density and Gibbs energy (capped-pressure variant). "
                            "Units: Pa. Zero or negative disables capping.");
          prm.declare_entry("Block density excess",
                            "0.0",
                            Patterns::Double(),
                            "Density excess added wherever the compositional 'block' field is 1 "
                            "(sinking-block benchmark scaffolding). Units: kg/m^3. Zero disables it.");
        }
        prm.leave_subsection();
      }
      prm.leave_subsection();
    }



    template <int dim>
    void
    NHKinetics<dim>::parse_parameters(ParameterHandler &prm)
    {
      prm.enter_subsection("Material model");
      {
        prm.enter_subsection("NH kinetics");
        {
          data_directory  = Utilities::expand_ASPECT_SOURCE_DIR(prm.get("Data directory"));
          data_file_names = Utilities::split_string_list(prm.get("Data file names"), "|");

          reaction_chain.parse_parameters(prm);

          const unsigned int n_reactions = reaction_chain.n_reactions();
          const unsigned int n_phases    = n_reactions + 1;

          AssertThrow(data_file_names.size() == n_reactions,
                      ExcMessage("The number of entries in 'Data file names' must match the number of reactions."));

          profiles.resize(n_reactions);
          for (unsigned int r = 0; r < n_reactions; ++r)
            {
              prm.enter_subsection("Ascii data model");
              profiles[r].parse_parameters(prm);
              prm.leave_subsection();

              profiles[r].data_directory = data_directory;
              profiles[r].data_file_name = data_file_names[r];
            }

          viscosity                                   = prm.get_double("Viscosity");
          minimum_viscosity                           = prm.get_double("Minimum viscosity");
          maximum_viscosity                           = prm.get_double("Maximum viscosity");
          thermal_viscosity_exponent                  = prm.get_double("Thermal viscosity exponent");
          phase_viscosity_prefactors                  = Utilities::string_to_double(Utilities::split_string_list(prm.get("Phase viscosity prefactors")));
          AssertThrow(phase_viscosity_prefactors.size() == n_phases,
                      ExcMessage("The number of entries in 'Phase viscosity prefactors' must match the number of phases (n_reactions + 1)."));
          gibbs_viscosity_width                       = prm.get_double("Gibbs viscosity width");
          k                                           = prm.get_double("Thermal conductivity");
          use_dynamic_pressure_correction_for_density = prm.get_bool("Use dynamic pressure correction for density");
          use_dynamic_pressure_correction_for_gibbs   = prm.get_bool("Use dynamic pressure correction for gibbs");
          relaxation_time_dynamic_pressure            = prm.get_double("Relaxation time for dynamic pressure");
          bulk_viscosity_explicit                     = prm.get_double("Explicit bulk viscosity");
          max_dynamic_pressure_correction             = prm.get_double("Maximum dynamic pressure correction");
          block_density_excess                        = prm.get_double("Block density excess");
        }
        prm.leave_subsection();
      }
      prm.leave_subsection();

      AssertThrow(reaction_chain.n_reactions() > 0, ExcMessage("At least one phase transformation must be defined."));
      AssertThrow(gibbs_viscosity_width > 0.0, ExcMessage("Gibbs viscosity width must be positive."));

      this->model_dependence.viscosity            = NonlinearDependence::none;
      this->model_dependence.density              = NonlinearDependence::pressure | NonlinearDependence::temperature;
      this->model_dependence.compressibility      = NonlinearDependence::none;
      this->model_dependence.specific_heat        = NonlinearDependence::none;
      this->model_dependence.thermal_conductivity = NonlinearDependence::none;
    }



    template <int dim>
    void
    NHKinetics<dim>::create_additional_named_outputs(MaterialModel::MaterialModelOutputs<dim> &out) const
    {
      if (out.template get_additional_output_object<ReactionRateOutputs<dim>>() == nullptr)
        {
          const unsigned int n_points = out.n_evaluation_points();
          out.additional_outputs.push_back(
            std::make_unique<MaterialModel::ReactionRateOutputs<dim>>(n_points, this->introspection().n_compositional_fields));
        }

      if (this->introspection().composition_type_exists(CompositionalFieldDescription::density) &&
          out.template get_additional_output_object<PrescribedFieldOutputs<dim>>() == nullptr)
        {
          const unsigned int n_points = out.n_evaluation_points();
          out.additional_outputs.push_back(
            std::make_unique<MaterialModel::PrescribedFieldOutputs<dim>>(n_points, this->introspection().n_compositional_fields));
        }

      if (out.template get_additional_output_object<NHKineticsOutputs<dim>>() == nullptr)
        {
          const unsigned int n_points    = out.n_evaluation_points();
          const unsigned int n_reactions = reaction_chain.n_reactions();
          out.additional_outputs.push_back(
            std::make_unique<MaterialModel::NHKineticsOutputs<dim>>(n_points, n_reactions + 1, n_reactions));
        }

      // Explicit bulk-viscosity force needs the Stokes RHS outputs.
      // The assembler also auto-creates these when 'Enable additional Stokes
      // RHS' is set; creating them here keeps direct evaluate() calls working.
      if (bulk_viscosity_explicit > 0.0 &&
          out.template get_additional_output_object<MaterialModel::AdditionalMaterialOutputsStokesRHS<dim>>() == nullptr)
        {
          const unsigned int n_points = out.n_evaluation_points();
          out.additional_outputs.push_back(
            std::make_unique<MaterialModel::AdditionalMaterialOutputsStokesRHS<dim>>(n_points));
        }

      if (out.template get_additional_output_object<SeismicAdditionalOutputs<dim>>() == nullptr)
        {
          const unsigned int n_points = out.n_evaluation_points();
          out.additional_outputs.push_back(std::make_unique<MaterialModel::SeismicAdditionalOutputs<dim>>(n_points));
        }
    }



    namespace
    {
      std::vector<std::string>
      make_additional_output_names(const unsigned int n_phases, const unsigned int n_reactions)
      {
        std::vector<std::string> names;
        names.emplace_back("visc_temperature_dependence");
        for (unsigned int p = 0; p < n_phases; ++p)
          names.emplace_back("X_phase_" + std::to_string(p));
        for (unsigned int r = 0; r < n_reactions; ++r)
          names.emplace_back("dG_driving_" + std::to_string(r));
        return names;
      }
    } // namespace

    template <int dim>
    NHKineticsOutputs<dim>::NHKineticsOutputs(const unsigned int n_points,
                                              const unsigned int n_phases_,
                                              const unsigned int n_reactions_)
      : NamedAdditionalMaterialOutputs<dim>(make_additional_output_names(n_phases_, n_reactions_))
      , visc_temperature_dependence(n_points, numbers::signaling_nan<double>())
      , phase_mass_fractions(n_phases_, std::vector<double>(n_points, numbers::signaling_nan<double>()))
      , corrected_gibbs(n_reactions_, std::vector<double>(n_points, numbers::signaling_nan<double>()))
      , n_phases(n_phases_)
      , n_reactions(n_reactions_)
    {}



    template <int dim>
    std::vector<double>
    NHKineticsOutputs<dim>::get_nth_output(const unsigned int idx) const
    {
      AssertIndexRange(idx, 1 + n_phases + n_reactions);
      if (idx == 0)
        return visc_temperature_dependence;
      if (idx < 1 + n_phases)
        return phase_mass_fractions[idx - 1];
      return corrected_gibbs[idx - 1 - n_phases];
    }
  } // namespace MaterialModel
} // namespace aspect

namespace aspect
{
  namespace MaterialModel
  {
    ASPECT_REGISTER_MATERIAL_MODEL(
      NHKinetics,
      "NH kinetics",
      "Chain-based phase transformation kinetics for non-hydrostatic benchmarks. "
      "Reactions form a ReactionChain (kinetic models per the 'Reaction chain' subsection); "
      "kinetic prefactors Z are SI rates directly integrated by the operator splitter (no time conversion). "
      "Reactions are driven by the dynamic pressure, optionally relaxed, capped, or damped.")
  } // namespace MaterialModel
} // namespace aspect
