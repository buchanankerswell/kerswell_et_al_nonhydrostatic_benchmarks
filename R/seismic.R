#!/usr/bin/env Rscript

main <- function() {
  args <- commandArgs(trailingOnly = TRUE)

  if (length(args) < 4) {
    cat(" !! Warning: Usage: seismic.R [util_dir] [data_dir_box] [data_dir_sink] [out_dir] [force_rewrite] [nominal_box_m] [nominal_sink_m]\n")
    return(invisible())
  }

  util_dir <- args[1]
  data_dir_box <- args[2]
  data_dir_sink <- args[3]
  out_dir <- args[4]
  force_rewrite <- if (length(args) >= 5) parse_logical(args[5]) else FALSE
  nominal_box <- if (length(args) >= 6) as.numeric(args[6]) / 1e3 else NULL
  nominal_sink <- if (length(args) >= 7) as.numeric(args[7]) / 1e3 else NULL

  lapply(list.files(util_dir, pattern = "\\.R$", full.names = TRUE), source)

  if (!dir.exists(out_dir)) dir.create(out_dir, recursive = TRUE)

  out_path <- file.path(out_dir, "seismic-box-sink.png")

  extra <- list(force_rewrite = force_rewrite)
  if (!is.null(nominal_box)) extra$nominal_box_km <- nominal_box
  if (!is.null(nominal_sink)) extra$nominal_sink_km <- nominal_sink
  do.call(visualize_seismic_comparison, c(list(data_dir_box, data_dir_sink, out_path), extra))
}

if (!interactive() && (sys.nframe() == 0 || identical(environment(), globalenv()))) {
  main()
}
