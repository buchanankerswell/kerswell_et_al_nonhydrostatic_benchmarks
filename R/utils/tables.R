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
      suite_abbr = case_when(
        suite == "box" ~ "Box",
        suite == "sink" ~ "Sink",
        TRUE ~ suite
      ),
      damp_ord = factor(damp, levels = unique(damp[order(dynp, damp)]))
    ) |>
    arrange(suite_abbr, dynp, damp_ord, res) |>
    select(
      Suite = suite_abbr,
      Model = model_id,
      Damping = damp,
      `Dynp on` = dynp,
      Res = res,
      `$\\delta z_{410}$` = disp410_km,
      `$\\delta w_{410}$` = width410_km,
      `$\\dot{X}_\\mathrm{max}$` = rate410,
      `$\\delta z_t$` = therm410_km,
      `$\\delta z_k$` = kin410_km
    ) |>
    mutate(across(c(`$\\dot{X}_\\mathrm{max}$`), ~ formatC(.x, format = "e", digits = 2))) |>
    mutate(across(c(`$\\delta z_{410}$`, `$\\delta w_{410}$`, `$\\delta z_t$`, `$\\delta z_k$`), ~ formatC(.x, format = "f", digits = 1)))

  col_align <- c("l", "l", "l", rep("r", ncol(formatted) - 3))

  md_table <- kable(formatted, format = "pipe", escape = FALSE, align = col_align)
  writeLines(md_table, out_path_md)
}
