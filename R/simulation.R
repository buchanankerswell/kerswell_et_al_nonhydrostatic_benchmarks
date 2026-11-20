#!/usr/bin/env Rscript

main <- function() {
  args <- commandArgs(trailingOnly = TRUE)

  if (length(args) < 4) {
    cat(" !! Warning: Usage: simulation.R [util_dir] [postprocessed_csv] [out_dir] [force_rewrite] [z_lo] [z_mid] [z_hi]\n")
    return(invisible())
  }

  util_dir <- args[1]
  postprocessed_csv <- args[2]
  out_dir <- args[3]

  lapply(list.files(util_dir, pattern = "\\.R$", full.names = TRUE), source)

  force_rewrite <- if (length(args) >= 4) parse_logical(args[4]) else FALSE
  if (length(args) >= 7) {
    z_levels <<- c(args[5], args[6], args[7])
  }

  df <- read_benchmark_postprocessed(postprocessed_csv)
  if (is.null(df) || !nrow(df)) {
    return(invisible())
  }

  out_path_structure <- file.path(out_dir, "structure-box-sink.png")

  visualize_benchmark_structure(df, out_path_structure, force_rewrite = force_rewrite)
}

if (!interactive() && (sys.nframe() == 0 || identical(environment(), globalenv()))) {
  main()
}
