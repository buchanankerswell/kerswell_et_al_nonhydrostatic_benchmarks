# Sink benchmark figures for the 410 transition.
# One row per model from simulation/results/postprocessed.csv; damping
# groups parse straight from the UID.

suite_lab_sink <- "Sink"
suite_shapes <- c("Sink" = 22)
# Reaction-rate anchors (1/s/K) (defaults mirror project.mk Z_LO/Z_MID/Z_HI;
# R/simulation.R overrides them from the command line).
z_levels <- c("9.51e-08", "4.44e-04", "1.4e+04")
z_pal <- c("sluggish" = "#7FB3D5", "intermediate" = "#E41A1C", "quasi-equilibrium" = "#4D148C")

damp_family <- function(damp) {
  str_extract(damp, "^[A-Za-z]+")
}

damp_value <- function(damp) {
  suppressWarnings(as.numeric(str_extract(damp, "[\\d.e+-]+$")))
}

# Short per-run labels matching python bench_label (config.py): damping
# token plus Res variant and no-feedback tags, so every benchmark run
# maps to a unique legend entry.
damp_display <- function(damp, dynp, res = "6") {
  parts <- damp
  parts <- ifelse(as.character(res) != "6", paste0(parts, " Res", res), parts)
  ifelse(dynp == 0, paste0(parts, " (no feedback)"), parts)
}

read_benchmark_postprocessed <- function(postprocessed_csv) {
  if (!file.exists(postprocessed_csv)) {
    log_error(paste("missing postprocessed output:", postprocessed_csv, "(run `make -C python postprocess` first)"))
    return(invisible())
  }
  # z round-trips through the CSV as a number, and as.character() on a
  # numeric vector formats 4.44e-04 as "0.000444" / 1.4e+04 as "14000",
  # so level matching must happen in numeric space, not on strings.
  z_vals <- suppressWarnings(as.numeric(z_levels))
  df <- suppressWarnings(read_csv(postprocessed_csv, show_col_types = FALSE)) |>
    mutate(
      # Cache stores display units (kJ/mol, 1/Ma, GPa); no conversion needed.
      rate410_per_Ma = rate410_per_Ma,
      # Full color key matching python damp_key/DAMP_COLORS (res/CFL
      # variants and no-feedback controls each map to a unique color).
      damp_key = ifelse(dynp == 0, paste0(damp, "_Off"), damp),
      damp_key = ifelse(as.character(res) != "6", paste0(damp_key, "_Res", res), damp_key),
      suite = factor(case_when(
        suite == "sink" ~ suite_lab_sink,
        TRUE ~ suite
      ), levels = c(suite_lab_sink)),
      res = factor(res, levels = c(4, 5, 6, 7)),
      z = factor(
        case_when(
          abs(as.numeric(z) - z_vals[1]) < 1e-14 ~ "sluggish",
          abs(as.numeric(z) - z_vals[2]) < 1e-10 ~ "intermediate",
          abs(as.numeric(z) - z_vals[3]) < 1 ~ "quasi-equilibrium",
          TRUE ~ NA_character_
        ),
        levels = c("sluggish", "intermediate", "quasi-equilibrium")
      ),
      damp_family = damp_family(damp),
      damp_num = damp_value(damp),
      damp_family_ord = factor(damp_family, levels = c("None", "Bimpl", "Bexpl", "Rel", "Cap")),
      damp_display = damp_display(damp, dynp, res)
    ) |>
    arrange(suite, dynp, damp_family_ord, damp_num) |>
    mutate(damp_display = factor(damp_display, levels = unique(damp_display)))
  df
}

structure_strip <- function(data, y_var, y_label, show_legend = FALSE, show_x = FALSE) {
  key_levels <- unique(data$damp_key)
  disp_labels <- vapply(key_levels, function(k) as.character(data$damp_display[data$damp_key == k][1]), character(1))
  p <- ggplot(data, aes(x = suppressWarnings(as.numeric(as.character(res))), y = !!sym(y_var))) +
    geom_point(aes(color = damp_key), size = 2.5, alpha = 0.9, position = position_jitter(width = 0.12, seed = 1), show.legend = show_legend) +
    scale_color_manual(values = damp_pal, breaks = key_levels, labels = disp_labels, name = "Damping", drop = FALSE, guide = guide_legend(nrow = 7)) +
    scale_x_continuous(breaks = c(5, 6, 7)) +
    labs(y = y_label, x = if (show_x) "Resolution" else NULL) +
    theme_bw(base_size = 14) +
    theme_bench() +
    theme(plot.margin = margin(5, 5, 5, 25))
  if (!show_x) {
    p <- p + theme(axis.text.x = element_blank(), axis.ticks.x = element_blank())
  }
  p
}

visualize_benchmark_structure <- function(df, out_path, force_rewrite = FALSE, fig_dpi = 100) {
  if (!force_rewrite && plot_exists(out_path)) {
    return(invisible())
  }
  ensure_output_dir(out_path)
  p_disp <- structure_strip(df, "disp410_km", "410 Displacement (km)")
  p_width <- structure_strip(df, "width410_km", "410 Width (km)")
  p_rate <- structure_strip(df, "rate410_per_Ma", expression(Max ~ dot(X) ~ "(1/Ma)"), show_x = TRUE)
  p_kin <- structure_strip(df, "kin410_km", "Kinetic Contribution (km)", show_legend = TRUE, show_x = TRUE)
  p <- (p_disp | p_width) / (p_rate | p_kin) +
    plot_layout(guides = "collect") &
    theme(legend.position = "bottom")
  ggsave(out_path, plot = p, width = 6.5, height = 5.2, dpi = fig_dpi, bg = "white", create.dir = TRUE)
  log_artifact(out_path)
}

theme_bench <- function() {
  theme(
    panel.grid.major = element_blank(),
    panel.grid.minor = element_blank(),
    panel.background = element_rect(fill = "grey92"),
    plot.margin = margin(5, 5, 5, 5),
    axis.ticks = element_blank(),
    legend.text = element_text(size = 11.2),
    legend.background = element_blank(),
    legend.key = element_blank()
  )
}
