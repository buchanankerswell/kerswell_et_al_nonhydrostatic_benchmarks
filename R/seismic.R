#!/usr/bin/env Rscript

main <- function() {
  args <- commandArgs(trailingOnly = TRUE)

  if (length(args) < 3) {
    cat(" !! Warning: Usage: seismic.R [util_dir] [data_dir_sink] [out_dir] [force_rewrite] [nominal_sink_m]\n")
    return(invisible())
  }

  util_dir <- args[1]
  data_dir_sink <- args[2]
  out_dir <- args[3]

  lapply(list.files(util_dir, pattern = "\\.R$", full.names = TRUE), source)

  force_rewrite <- if (length(args) >= 4) parse_logical(args[4]) else FALSE
  nominal_sink <- if (length(args) >= 5) as.numeric(args[5]) / 1e3 else NULL
  # Figure resolution from project.mk FIG_DPI (draft 100, manuscript 330).
  fig_dpi <- if (length(args) >= 6) as.numeric(args[6]) else 100

  if (!dir.exists(out_dir)) dir.create(out_dir, recursive = TRUE)

  out_path <- file.path(out_dir, "seismic-sink.png")

  extra <- list(force_rewrite = force_rewrite, fig_dpi = fig_dpi)
  if (!is.null(nominal_sink)) extra$nominal_sink_km <- nominal_sink
  do.call(visualize_seismic_comparison, c(list(data_dir_sink, out_path), extra))
}

if (!interactive() && (sys.nframe() == 0 || identical(environment(), globalenv()))) {
  main()
}
