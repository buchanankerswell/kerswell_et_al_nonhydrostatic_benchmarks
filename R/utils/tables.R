write_postprocessed_summary_table <- function(postprocessed_csv, out_dir, quiet = TRUE) {
  if (!file.exists(postprocessed_csv)) {
    if (!quiet) log_error(paste("Input postprocessed CSV not found:", postprocessed_csv))
    return(invisible())
  }

  if (!quiet) log_info("Reading and formatting benchmark data")

  postprocessed_data <- suppressWarnings(read_csv(postprocessed_csv, show_col_types = FALSE))

  if (is.null(postprocessed_data) || !nrow(postprocessed_data)) {
    return(invisible())
  }

  out_path_md <- file.path(out_dir, "postprocessed.md")

  if (!quiet) log_artifact(out_path_md)

  formatted <- postprocessed_data |>
    mutate(
      # Cache stores display units (kJ/mol, 1/Ma, GPa); no conversion needed.
      rate410_per_Ma = rate410_per_Ma,
      suite_abbr = case_when(
        suite == "sink" ~ "Sink",
        TRUE ~ suite
      ),
      damp_num = suppressWarnings(as.numeric(str_extract(damp, "[\\d.e+-]+$"))),
      damp_ord = factor(damp, levels = unique(damp[order(dynp, damp, damp_num, res, z)]))
    ) |>
    arrange(suite_abbr, dynp, damp_ord, damp_num, res, z) |>
    select(
      Suite = suite_abbr,
      Model = model_id,
      Damping = damp,
      `Dynp on` = dynp,
      Res = res,
      `Z (1/s/K)` = z,
      `$\\delta z_{410}$ (km)` = disp410_km,
      `$\\delta w_{410}$ (km)` = width410_km,
      `$\\dot{X}_\\mathrm{max}$ (1/Ma)` = rate410_per_Ma,
      `$\\delta z_t$ (km)` = therm410_km,
      `$\\delta z_k$ (km)` = kin410_km
    ) |>
    mutate(across(c(`$\\dot{X}_\\mathrm{max}$ (1/Ma)`), ~ formatC(.x, format = "e", digits = 2))) |>
    mutate(across(c(`Z (1/s/K)`), ~ formatC(as.numeric(.x), format = "e", digits = 2))) |>
    mutate(across(c(`$\\delta z_{410}$ (km)`, `$\\delta w_{410}$ (km)`, `$\\delta z_t$ (km)`, `$\\delta z_k$ (km)`), ~ formatC(.x, format = "f", digits = 1)))

  col_align <- c("l", "l", "l", rep("r", ncol(formatted) - 3))

  md_table <- kable(formatted, format = "pipe", escape = FALSE, align = col_align)
  writeLines(md_table, out_path_md)
}
