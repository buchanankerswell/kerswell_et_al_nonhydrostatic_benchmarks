import subprocess
import sys
from argparse import ArgumentParser, ArgumentTypeError, Namespace
from pathlib import Path

from simulation.mesh.config import MeshConfig
from simulation.mesh.pipeline import FullPipeline, PlottingPipeline, PostProcessingPipeline
from simulation.params.transitions import PhaseTransition, find_surface_depth_offset, find_transition, load_depth_datum, read_dG_profile
from utils.logging import log_artifact, log_info
from tile import ImageTiler


def str2bool(v):
    if isinstance(v, bool):
        return v
    if v.lower() in ("yes", "true", "t", "y", "1"):
        return True
    elif v.lower() in ("no", "false", "f", "n", "0"):
        return False
    else:
        raise ArgumentTypeError("Boolean value expected.")


def parse_arguments() -> Namespace:
    """ """
    parser = ArgumentParser(description="Visualize and postprocess simulation results.")

    parser.add_argument("dG_profile_ol_wd", type=str, help="Path to olivine-wadsleyite dG profile")
    parser.add_argument("model_height", type=float, help="Model height [m]")
    parser.add_argument("surface_pressure", type=float, help="Surface pressure [Pa]")
    parser.add_argument("out_fig_dir", type=str, help="Output figure directory")
    parser.add_argument("out_data_dir", type=str, help="Flattened simulation/results dir")
    parser.add_argument("--suite-tag", type=str, required=True, help="Suite tag: box or sink")

    parser.add_argument("--model-ids", nargs="+", type=str, required=True, help="Simulation names")
    parser.add_argument("--timesteps", nargs="+", type=int, required=True, help="Output numbers to process")
    parser.add_argument("--in-dirs", nargs="+", type=str, required=True, help="Simulation results directories")
    parser.add_argument("--visualize-ids", nargs="*", type=str, default=None, help="Subset to render and tile (default: all).")
    parser.add_argument("--chunk", type=str, default=None, help="Chunk label (i/N) set by the parent when splitting work.")
    parser.add_argument("--suppress-artifact", type=str2bool, default=False, help="Skip suite artifact log (parent logs once).")

    parser.add_argument("--depth-corr-ol-wd", type=float, default=0.0, help="Depth correction for the olivine -> wadsleyite transition [m].")
    parser.add_argument(
        "--nominal-410",
        type=float,
        default=None,
        help="Runtime-adiabat 410 nominal depth [m]; supersedes profile + depth-corr for X_wd when given.",
    )
    parser.add_argument(
        "--x-step-limit-m", type=float, default=150e3, help="Representative-trace max x jump per depth slice [m] (project.mk TRACE_X_STEP_LIMIT)."
    )
    parser.add_argument(
        "--trace-x",
        type=float,
        default=None,
        help="Fixed representative-trace x [m]; vertical trace for isothermal suites. Overrides anomaly following.",
    )
    parser.add_argument(
        "--block-top-m", type=float, default=875e3, help="Block top [m] for the ambient-reference correction (project.mk BLOCK_Y_TOP)."
    )
    parser.add_argument(
        "--block-bottom-m", type=float, default=725e3, help="Block bottom [m] for the ambient-reference correction (project.mk BLOCK_Y_BOT)."
    )
    parser.add_argument("--gravity", type=float, default=9.81, help="Gravity [m/s^2] for the ambient-reference correction (project.mk GRAVITY).")
    parser.add_argument("--mode", type=str, choices=["postprocess", "visualize", "full"], default="full", help="Pipeline mode.")
    parser.add_argument("--save-csv", type=str2bool, default=True, help="Save structure data to csv.")
    parser.add_argument("--force-reprocess", type=str2bool, default=False, help="Force reprocessing and overwriting of cache.")
    parser.add_argument("--verbosity", type=int, default=0, help="Verbosity.")
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=0,
        help="Max models per process (0 = no chunking). Splits work across fresh processes to bound memory growth.",
    )

    return parser.parse_args()


def main():
    """ """
    args = parse_arguments()

    model_ids = args.model_ids or []
    in_dirs = args.in_dirs or []

    # Split work across fresh processes to bound memory growth (e.g. the
    # pyvista leak). Each child processes its subset and merges into the
    # shared on-disk caches, so reruns only redo unfinished chunks.
    if args.chunk_size and args.chunk_size > 0 and len(model_ids) > args.chunk_size:
        positionals = [
            args.dG_profile_ol_wd,
            str(args.model_height),
            str(args.surface_pressure),
            args.out_fig_dir,
            args.out_data_dir,
        ]
        n_chunks = (len(model_ids) + args.chunk_size - 1) // args.chunk_size
        log_info(f"Processing {len(model_ids)} models in {n_chunks} chunks")
        for idx, start in enumerate(range(0, len(model_ids), args.chunk_size)):
            chunk_ids = model_ids[start : start + args.chunk_size]
            chunk_dirs = in_dirs[start : start + args.chunk_size]
            cmd = [
                sys.executable,
                __file__,
                *positionals,
                "--model-ids",
                *chunk_ids,
                "--in-dirs",
                *chunk_dirs,
                "--timesteps",
                *[str(t) for t in (args.timesteps or [])],
                f"--depth-corr-ol-wd={args.depth_corr_ol_wd}",
                f"--mode={args.mode}",
                f"--save-csv={args.save_csv}",
                f"--suite-tag={args.suite_tag}",
                f"--block-top-m={args.block_top_m}",
                f"--block-bottom-m={args.block_bottom_m}",
                f"--gravity={args.gravity}",
                f"--force-reprocess={args.force_reprocess}",
                f"--verbosity={args.verbosity}",
            ]
            if args.visualize_ids:
                cmd += ["--visualize-ids", *args.visualize_ids]
            if args.nominal_410 is not None:
                cmd += [f"--nominal-410={args.nominal_410}"]
            if args.trace_x is not None:
                cmd += [f"--trace-x={args.trace_x}"]
            cmd += [f"--x-step-limit-m={args.x_step_limit_m}"]
            cmd += ["--suppress-artifact=true", f"--chunk={idx + 1}/{n_chunks}"]
            subprocess.run(cmd, check=True)
        if args.mode in ("postprocess", "full"):
            log_artifact(Path(args.out_data_dir) / f"structure-summary-{args.suite_tag}.csv")
        return

    model_height = args.model_height
    headers, data = read_dG_profile(args.dG_profile_ol_wd)
    depth_datum = load_depth_datum(str(Path(args.dG_profile_ol_wd).parent / "depth-datum.tsv"))
    surface_depth = find_surface_depth_offset(headers, data, args.surface_pressure)

    trans_data: dict[str, PhaseTransition] = {"X_wd": find_transition(headers, data, model_height, surface_depth)}
    trans_data["X_wd"].depth += args.depth_corr_ol_wd
    trans_data["X_wd"].y -= args.depth_corr_ol_wd

    if args.nominal_410 is not None and args.suite_tag in ("box", "sink"):
        trans_data["X_wd"].depth = args.nominal_410
        trans_data["X_wd"].y = model_height - args.nominal_410
        log_info(f"410 nominal overridden to runtime adiabat: {args.nominal_410 / 1e3:.1f} km")

    tsteps = args.timesteps or []
    in_dirs = [Path(p) for p in args.in_dirs] if args.in_dirs else []
    out_fig_dir = Path(args.out_fig_dir) if args.out_fig_dir else Path("./figures")
    out_data_dir = Path(args.out_data_dir) if args.out_data_dir else Path("./data")
    mode = args.mode or "visualize"
    save_csv = args.save_csv or True
    force_reprocess = args.force_reprocess or False
    verbosity = args.verbosity or 0

    fields_for_seismic_profiles = ["density", "seismic_Vp", "seismic_Vs"]

    # Isothermal suites: no thermal anomaly to follow, viscosity is uniform.
    # First tile row: dynamic pressure + density anomaly + vertical velocity.
    # Second tile row: driving energy + reaction rate + phase fraction.
    fields_to_plot = [
        "nonadiabatic_pressure",
        "nonadiabatic_density",
        "velocity_vertical",
        "dG_driving_0",
        "reaction_rate_C0",
        "xi_ol_wd",
    ]

    fields_for_seismic_profiles = ["density", "seismic_Vp", "seismic_Vs"]

    plot_config = MeshConfig()
    if args.suite_tag == "box":
        # Narrow box domain (300 x 1000 km): match the render window to the
        # domain aspect so tiled panels carry no side whitespace, and scale
        # pixel-based fonts/lines down with the window so titles, colorbars,
        # and the scale bar keep sink-like proportions.
        plot_config.plotter_window_size = [576, 1920]
        plot_config.cbar_title_font_size = 60
        plot_config.cbar_label_font_size = 60
        plot_config.scale_bar_label_font_size = 60
        plot_config.scale_bar_thickness = 15
    plot_config.file_map = {k: plot_config.file_map[k] for k in fields_to_plot if k in plot_config.file_map}
    plot_config.default_fig_dir = out_fig_dir

    pvtu_in_dirs = dict(zip(model_ids, in_dirs))
    visualize_ids = args.visualize_ids or list(pvtu_in_dirs.keys())
    chunk_vis_ids = [m for m in visualize_ids if m in pvtu_in_dirs]
    transition_summary_path = out_data_dir / f"structure-cache-{args.suite_tag}.pkl"
    seismic_profile_cache_path = out_data_dir / f"seismic-profile-cache-{args.suite_tag}.pkl"
    csv_path = out_data_dir / f"structure-summary-{args.suite_tag}.csv"
    out_seismic_profile_dir = out_data_dir / f"seismic_profiles_{args.suite_tag}"

    transition_summary = None
    seismic_profile_cache = None
    emit_artifact = not args.suppress_artifact
    chunk_tag = f"Chunk {args.chunk}: " if args.chunk else ""
    if mode == "postprocess":
        log_info(f"{chunk_tag}{len(pvtu_in_dirs)} models")
        pipeline = PostProcessingPipeline(
            config=plot_config,
            pvtu_in_dirs=pvtu_in_dirs,
            tsteps=tsteps,
            trans_data=trans_data,
            verbosity=verbosity,
            suite_tag=args.suite_tag,
            trace_x=args.trace_x,
            x_step_limit_m=args.x_step_limit_m,
            depth_datum=depth_datum,
            block_top_m=args.block_top_m,
            block_bot_m=args.block_bottom_m,
            gravity=args.gravity,
        )

        transition_summary, seismic_profile_cache = pipeline.run(transition_summary_path, seismic_profile_cache_path, force_reprocess)
        pipeline.export_transition_summary(csv_path, transition_summary)

        pipeline.export_seismic_profiles(out_seismic_profile_dir, fields_for_seismic_profiles, seismic_profile_cache)
        if emit_artifact:
            log_artifact(csv_path)

    elif mode == "visualize":
        if not transition_summary_path.exists() or force_reprocess:
            log_info(f"{chunk_tag}{len(pvtu_in_dirs)} models")
            post_pipeline = PostProcessingPipeline(
                config=plot_config,
                pvtu_in_dirs=pvtu_in_dirs,
                tsteps=tsteps,
                trans_data=trans_data,
                verbosity=verbosity,
                suite_tag=args.suite_tag,
                trace_x=args.trace_x,
                x_step_limit_m=args.x_step_limit_m,
                depth_datum=depth_datum,
                block_top_m=args.block_top_m,
                block_bot_m=args.block_bottom_m,
                gravity=args.gravity,
            )
            transition_summary, seismic_profile_cache = post_pipeline.run(transition_summary_path, seismic_profile_cache_path, force_reprocess)
        else:
            transition_summary = PlottingPipeline.load_cache(transition_summary_path)

        plot_pipeline = PlottingPipeline(
            config=plot_config,
            pvtu_in_dirs=pvtu_in_dirs,
            tsteps=tsteps,
            trans_data=trans_data,
            verbosity=verbosity,
            suite_tag=args.suite_tag,
            trace_x=args.trace_x,
            cache=transition_summary,
        )
        plot_pipeline.run(fields_to_plot, chunk_vis_ids)

    else:
        log_info(f"{chunk_tag}{len(pvtu_in_dirs)} models")
        pipeline = FullPipeline(
            config=plot_config,
            pvtu_in_dirs=pvtu_in_dirs,
            tsteps=tsteps,
            trans_data=trans_data,
            verbosity=verbosity,
            suite_tag=args.suite_tag,
            trace_x=args.trace_x,
            x_step_limit_m=args.x_step_limit_m,
            depth_datum=depth_datum,
            block_top_m=args.block_top_m,
            block_bot_m=args.block_bottom_m,
            gravity=args.gravity,
        )
        pipeline.run(
            fields_to_plot,
            fields_for_seismic_profiles,
            csv_path,
            out_seismic_profile_dir,
            transition_summary_path,
            seismic_profile_cache_path,
            save_csv,
            force_reprocess,
            visualize_ids,
        )
        if emit_artifact:
            log_artifact(csv_path)

    if mode in ["visualize", "full"]:
        tile_sets = {
            "set0": {"tags": None, "fields": ["nonadiabatic_pressure", "nonadiabatic_density", "velocity_vertical"]},
            "set1": {"tags": None, "fields": ["dG_driving_0", "reaction_rate_C0", "xi_ol_wd"]},
        }

        for model_id in chunk_vis_ids:
            for config in tile_sets.values():
                fields = config.get("fields", None)
                tags = config.get("tags", None)
                if fields and len(fields) == 3:
                    tiler = ImageTiler(plot_config, out_fig_dir / "meshes" / model_id, fields[0], fields[1], fields[2], tags)
                    tiler.tile_images()


if __name__ == "__main__":
    main()
