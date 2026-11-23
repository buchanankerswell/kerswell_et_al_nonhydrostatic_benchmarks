from argparse import ArgumentParser, Namespace
from pathlib import Path

from burnman import Composite, minerals
from profiles import AdiabaticProfile, DrivingForceProfile


def parse_arguments() -> Namespace:
    """Read command-line arguments."""
    parser = ArgumentParser(description="Generate an isentropic adiabat using BurnMan")

    parser.add_argument("model_id", type=str, help="ID of the Perple_X model")
    parser.add_argument("mg_number", type=int, nargs="+", help="Mg# composition")
    parser.add_argument("out_data_dir", type=str, help="Output data directory")
    parser.add_argument("out_fig_dir", type=str, help="Output figure directory")

    parser.add_argument("--potential-temperature", type=float, default=1573.0, help="Potential temperature (K) (default: 1573.0)")
    parser.add_argument("--out-table-resolution", type=int, default=128, help="Perple_X table resolution (count) (default: 128)")
    parser.add_argument("--out-profile-resolution", type=int, default=501, help="Adiabat profile resolution (count) (default: 501)")
    parser.add_argument("--planet-radius", type=float, default=6370e03, help="Planet radius (m) (default: 6370e03)")
    parser.add_argument("--surface-gravity", type=float, default=9.81, help="Surface gravity (m/s^2) (default: 9.81)")
    parser.add_argument("--dpi", type=int, default=100, help="Figure resolution (project.mk FIG_DPI; draft 100, manuscript 330)")

    return parser.parse_args()


def main() -> None:
    """Build the BurnMan adiabat and the 410/520/660 reaction tables."""
    args = parse_arguments()

    out_data_dir = Path(args.out_data_dir)
    out_fig_dir = Path(args.out_fig_dir)
    out_table = out_data_dir / f"{args.model_id}-material-table.tab"
    out_adiabat = out_data_dir / f"{args.model_id}-adiabatic-profile.tsv"

    adiabat = AdiabaticProfile(
        model_id=args.model_id,
        out_table=out_table,
        out_profile=out_adiabat,
        potential_temperature=args.potential_temperature,
        out_table_resolution=args.out_table_resolution,
        out_profile_resolution=args.out_profile_resolution,
        planet_radius=args.planet_radius,
        surface_gravity=args.surface_gravity,
    )

    for mg in args.mg_number:
        out_reaction_410 = out_data_dir / f"olivine-wadsleyite-profile-Mg{mg}.tsv"
        out_reaction_520 = out_data_dir / f"wadsleyite-ringwoodite-profile-Mg{mg}.tsv"
        out_reaction_660 = out_data_dir / f"ringwoodite-postspinel-profile-Mg{mg}.tsv"

        mg_frac = mg / 100

        # Define minerals
        ol = minerals.SLB_2024.olivine([mg_frac, 1 - mg_frac])
        wa = minerals.SLB_2024.wadsleyite([mg_frac, 1 - mg_frac])
        ri = minerals.SLB_2024.ringwoodite([mg_frac, 1 - mg_frac])
        bg = minerals.SLB_2024.bridgmanite([mg_frac, 1 - mg_frac, 0.0, 0.0, 0.0, 0.0, 0.0])
        fp = minerals.SLB_2024.ferropericlase([mg_frac, 1 - mg_frac, 0.0, 0.0, 0.0])

        # Mantle materials (mixture fractions differ from the balanced-reaction moles)
        upper_mantle = Composite([ol], [1.0], name="upper-mantle")
        upper_mtz = Composite([wa], [1.0], name="upper-mtz")
        lower_mtz = Composite([ri], [1.0], name="lower-mtz")
        lower_mantle = Composite([bg, fp], [0.8, 0.2], name="lower-mantle")

        reaction_410 = DrivingForceProfile(
            material_a=upper_mantle,
            n_total_a=1,
            material_b=upper_mtz,
            n_total_b=1,
            in_profile=adiabat,
            out_profile=out_reaction_410,
            out_fig_dir=out_fig_dir,
            dpi=args.dpi,
        )
        reaction_410.visualize()

        reaction_520 = DrivingForceProfile(
            material_a=upper_mtz,
            n_total_a=1,
            material_b=lower_mtz,
            n_total_b=1,
            in_profile=adiabat,
            out_profile=out_reaction_520,
            out_fig_dir=out_fig_dir,
            dpi=args.dpi,
        )
        reaction_520.visualize()

        # Balance the 660 reaction: 1 mol ringwoodite -> 1 mol bridgmanite
        # + 0.25 mol ferropericlase (= 1.25 mol product).
        reaction_660 = DrivingForceProfile(
            material_a=lower_mtz,
            n_total_a=1,
            material_b=lower_mantle,
            n_total_b=1.25,
            in_profile=adiabat,
            out_profile=out_reaction_660,
            out_fig_dir=out_fig_dir,
            dpi=args.dpi,
        )
        reaction_660.visualize()


if __name__ == "__main__":
    main()
