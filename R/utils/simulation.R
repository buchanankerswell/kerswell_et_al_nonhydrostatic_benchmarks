# Postprocessed NH benchmark figures (box + sink suites, 410 transition).
# One row per model comes from simulation/results/postprocessed.csv
# (python postprocess target); damping groups parse straight from the UID.

suite_lab_box <- "Box"
suite_lab_sink <- "Sink"
suite_shapes <- c("Box" = 21, "Sink" = 22)
z_levels <- c("9.51e-08", "4.44e-04", "1.4e+04")
z_pal <- c("sluggish" = "#7FB3D5", "intermediate" = "#E41A1C", "quasi-equilibrium" = "#4D148C")

damp_family <- function(damp) {
  str_extract(damp, "^[A-Za-z]+")
}

damp_value <- function(damp) {
  suppressWarnings(as.numeric(str_extract(damp, "[\\d.e+-]+$")))
}

damp_display <- function(damp, dynp) {
  case_when(
    damp == "None" & dynp == 0 ~ "Equilibrium (No Feedback)",
    damp == "None" ~ "No Damping",
    damp_family(damp) == "Bimpl" ~ paste0("Implicit Bulk ", str_extract(damp, "[\\d.e+-]+$"), " (Pa s)"),
    damp_family(damp) == "Bexpl" ~ paste0("Explicit Bulk ", str_extract(damp, "[\\d.e+-]+$"), " (Pa s)"),
    damp_family(damp) == "Rel" ~ paste0("Relaxed ", str_extract(damp, "[\\d.e+-]+$"), " (s)"),
    damp_family(damp) == "Cap" ~ paste0("Capped ", str_extract(damp, "[\\d.e+-]+$"), " (Pa)"),
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
        suite == "box" ~ suite_lab_box,
        suite == "sink" ~ suite_lab_sink,
        TRUE ~ suite
      ), levels = c(suite_lab_box, suite_lab_sink)),
      res = factor(res, levels = c(4, 5, 6, 7)),
      # z round-trips through the CSV as a number, and as.character() on a
      # numeric vector formats 4.44e-04 as "0.000444" / 1.4e+04 as "14000",
      # so level matching must happen in numeric space, not on strings.
      z = factor(
        case_when(
          abs(as.numeric(z) - 9.51e-08) < 1e-14 ~ "sluggish",
          abs(as.numeric(z) - 4.44e-04) < 1e-10 ~ "intermediate",
          abs(as.numeric(z) - 1.4e+04) < 1 ~ "quasi-equilibrium",
          TRUE ~ NA_character_
        ),
        levels = c("sluggish", "intermediate", "quasi-equilibrium")
      ),
      damp_family = damp_family(damp),
      damp_num = damp_value(damp),
      damp_family_ord = factor(damp_family, levels = c("None", "Bimpl", "Bexpl", "Rel", "Cap")),
      damp_display = damp_display(damp, dynp)
    ) |>
    arrange(suite, dynp, damp_family_ord, damp_num) |>
    mutate(damp_display = factor(damp_display, levels = unique(damp_display)))
  df
}

structure_strip <- function(data, y_var, y_label, show_legend = FALSE) {
  ggplot(data, aes(x = damp_display, y = !!sym(y_var))) +
    geom_point(aes(fill = z, shape = suite), size = 4, color = "black", stroke = 0.5, alpha = 0.9, show.legend = show_legend) +
    scale_fill_manual(values = z_pal, drop = FALSE, name = "Reaction Speed") +
    scale_shape_manual(values = suite_shapes, drop = FALSE, name = "Suite") +
    guides(fill = guide_legend(override.aes = list(size = 3.5, shape = 21))) +
    facet_wrap(~res, nrow = 1, labeller = as_labeller(function(x) paste("Resolution", x))) +
    labs(y = y_label, x = NULL) +
    theme_bw(base_size = 14) +
    theme_bench() +
    theme(
      axis.text.x = element_text(angle = 30, hjust = 1, size = 10),
      plot.margin = margin(5, 10, 5, 60)
    )
}

visualize_benchmark_structure <- function(df, out_path, force_rewrite = FALSE) {
  if (!force_rewrite && plot_exists(out_path)) {
    return(invisible())
  }
  ensure_output_dir(out_path)
  p_disp <- structure_strip(df, "disp410_km", "410 Displacement (km)")
  p_width <- structure_strip(df, "width410_km", "410 Width (km)")
  p_rate <- structure_strip(df, "rate410", expression(Highest~dot(X)~"(1/Ma)"))
  p_kin <- structure_strip(df, "kin410_km", "Kinetic Contribution (km)", show_legend = TRUE)
  p <- (p_disp | p_width) / (p_rate | p_kin) +
    plot_layout(guides = "collect") &
    theme(legend.position = "right")
  ggsave(out_path, plot = p, width = 14, height = 8, dpi = 300, bg = "white", create.dir = TRUE)
  log_artifact(out_path)
}

theme_bench <- function() {
  theme(
    panel.grid.major = element_blank(),
    panel.grid.minor = element_blank(),
    panel.background = element_rect(fill = "grey92"),
    plot.margin = margin(5, 5, 5, 5),
    axis.ticks = element_blank(),
    legend.text = element_text(size = 11),
    legend.background = element_blank()
  )
}
