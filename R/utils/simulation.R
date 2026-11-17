# Postprocessed NH benchmark figures (box + sink suites, 410 transition).
# One row per model comes from simulation/data/postprocessed.csv
# (python postprocess target); damping groups parse straight from the UID.

SUITE_LAB_BOX <- "Box"
SUITE_LAB_SINK <- "Sink-block"
SUITE_PAL <- c("Box" = "#E41A1C", "Sink-block" = "#377EB8")
SUITE_SHAPES <- c("Box" = 21, "Sink-block" = 22)

damp_kind <- function(damp) {
  str_extract(damp, "^[A-Za-z]+")
}

damp_label <- function(damp, dynp) {
  case_when(
    damp == "None" & dynp == 0 ~ "equilibrium (no feedback)",
    damp == "None" ~ "undamped",
    damp_kind(damp) == "Bimpl" ~ paste0("implicit bulk \u03b6=", str_extract(damp, "[\\d.e]+$")),
    damp_kind(damp) == "Bexpl" ~ paste0("explicit bulk \u03b6=", str_extract(damp, "[\\d.e]+$")),
    damp_kind(damp) == "Rel" ~ paste0("relaxed \u03c4=", str_extract(damp, "[\\d.e]+$"), " s"),
    damp_kind(damp) == "Cap" ~ paste0("capped ", str_extract(damp, "[\\d.e]+$"), " Pa"),
    TRUE ~ damp
  )
}

read_benchmark_postprocessed <- function(postprocessed_csv) {
  if (!file.exists(postprocessed_csv)) {
    log_error(paste("missing postprocessed output:", postprocessed_csv, "(run `make -C python postprocess` first)"))
    return(invisible())
  }
  df <- suppressWarnings(read_csv(postprocessed_csv, show_col_types = FALSE)) |>
    mutate(
      suite = factor(case_when(
        suite == "box" ~ SUITE_LAB_BOX,
        suite == "sink" ~ SUITE_LAB_SINK,
        TRUE ~ suite
      ), levels = c(SUITE_LAB_BOX, SUITE_LAB_SINK)),
      kind = damp_kind(damp),
      kind_ord = factor(kind, levels = c("None", "Bimpl", "Bexpl", "Rel", "Cap")),
      label = damp_label(damp, dynp)
    ) |>
    arrange(suite, dynp, kind_ord, damp) |>
    mutate(label = factor(label, levels = unique(label)))
  df
}

structure_panel <- function(data, y_var, y_label, show_legend = FALSE) {
  ggplot(data, aes(x = label, y = !!sym(y_var))) +
    geom_point(aes(fill = suite, shape = suite), size = 4, color = "black", stroke = 0.5, alpha = 0.9, show.legend = show_legend) +
    scale_fill_manual(values = SUITE_PAL, drop = FALSE) +
    scale_shape_manual(values = SUITE_SHAPES, drop = FALSE) +
    guides(fill = guide_legend(override.aes = list(size = 3.5))) +
    labs(y = y_label, x = NULL, fill = NULL, shape = NULL) +
    theme_bw(base_size = 14) +
    theme_bench() +
    theme(axis.text.x = element_text(angle = 30, hjust = 1, size = 10))
}

visualize_benchmark_structure <- function(df, out_path, force_rewrite = FALSE) {
  if (!force_rewrite && plot_exists(out_path)) {
    return(invisible())
  }
  ensure_output_dir(out_path)
  p_disp <- structure_panel(df, "disp410_km", "410 displacement (km)")
  p_width <- structure_panel(df, "width410_km", "410 width (km)")
  p_rate <- structure_panel(df, "rate410", "Max reaction rate (1/s)")
  p_kin <- structure_panel(df, "kin410_km", "Kinetic contribution (km)", show_legend = TRUE)
  p <- (p_disp | p_width) / (p_rate | p_kin) +
    plot_layout(guides = "collect") &
    theme(legend.position = "right")
  ggsave(out_path, plot = p, width = 12, height = 7, dpi = 300, bg = "white", create.dir = TRUE)
  log_artifact(out_path)
}

theme_bench <- function() {
  theme(
    panel.grid.major = element_blank(),
    panel.grid.minor = element_blank(),
    panel.background = element_rect(fill = "grey92"),
    plot.margin = margin(5, 5, 5, 5),
    axis.ticks = element_blank(),
    legend.title = element_blank(),
    legend.text = element_text(size = 11),
    legend.background = element_blank()
  )
}
