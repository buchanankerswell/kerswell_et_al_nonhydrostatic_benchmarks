# Nominal 410 depth (km): Mg100 versioned profile equilibrium
# (359.2 km via python/simulation/params/transitions.py) plus the 5 km
# ASPECT depth correction used at runtime. The measured front sits a few km
# deeper under dynamic-pressure loading; the band marks the reference only.
nominal_410_km <- 359.2 + 5.0

read_seismic_profile <- function(filepath) {
  df <- read_csv(filepath, show_col_types = FALSE)
  fname <- basename(filepath)
  df |>
    mutate(
      model_id = str_extract(fname, "(?<=seismic_profile_).*(?=_t[0-9]+_representative\\.csv)"),
      tstep = as.numeric(str_extract(fname, "(?<=_t)[0-9]+(?=_representative\\.csv)")),
      depth = depth / 1e3,
      trace_x = trace_x / 1e3,
    )
}

read_suite_profiles <- function(data_dir, suite_label) {
  files <- list.files(data_dir, pattern = "seismic_profile_.*_t[0-9]+_representative\\.csv", full.names = TRUE)
  if (!length(files)) {
    log_error(paste("no representative seismic profiles in:", data_dir))
    return(NULL)
  }
  df <- map_df(files, read_seismic_profile) |> mutate(suite = suite_label)
  df |>
    group_by(model_id) |>
    filter(tstep == max(tstep)) |>
    ungroup()
}

read_init_profile <- function(data_dir) {
  files <- list.files(data_dir, pattern = "seismic_profile_.*Dynp1_DampNone.*_t0_representative\\.csv", full.names = TRUE)
  if (!length(files)) {
    return(NULL)
  }
  read_seismic_profile(files[1]) |> filter(!is.na(seismic_Vp))
}

visualize_seismic_comparison <- function(data_dir_box, data_dir_sink, out_path, force_rewrite = FALSE) {
  if (!force_rewrite && plot_exists(out_path)) {
    return(invisible())
  }
  df <- bind_rows(
    read_suite_profiles(data_dir_box, "Box"),
    read_suite_profiles(data_dir_sink, "Sink-block")
  )
  if (is.null(df) || !nrow(df)) {
    return(invisible())
  }
  df <- df |> mutate(
    suite = factor(suite, levels = c("Box", "Sink-block")),
    damp = str_extract(model_id, "(?<=_Damp)[A-Za-z]+[\\d.e]*")
  )
  df_init_box <- read_init_profile(data_dir_box)
  df_init_sink <- read_init_profile(data_dir_sink)

  lim_vp <- range(c(
    df$seismic_Vp,
    if (!is.null(df_init_box)) df_init_box$seismic_Vp,
    if (!is.null(df_init_sink)) df_init_sink$seismic_Vp
  ), na.rm = TRUE)

  p_panel <- function(suite_label, init_df) {
    d <- df |> filter(suite == suite_label)
    panel <- ggplot(d, aes(x = seismic_Vp, y = depth, group = model_id)) +
      annotate("rect", xmin = -Inf, xmax = Inf, ymin = nominal_410_km - 10, ymax = nominal_410_km + 10, fill = "grey80", alpha = 0.7) +
      geom_path(aes(color = damp), linewidth = 1.6, alpha = 0.85) +
      scale_y_reverse() +
      scale_x_continuous(limits = lim_vp, breaks = c(8, 9, 10, 11, 12)) +
      labs(title = suite_label, x = expression(V[p] ~ (km / s)), y = "Depth (km)", color = "Damping") +
      theme_bw(base_size = 20) +
      theme_profile_comparison()
    if (!is.null(init_df)) {
      panel <- panel + geom_path(data = init_df, color = "black", linewidth = 1.2, show.legend = FALSE)
    }
    panel + annotate("text", x = 8.05, y = nominal_410_km + 30, label = "410", size = 6, hjust = 0, color = "gray30")
  }

  p <- p_panel("Box", df_init_box) |
    (p_panel("Sink-block", df_init_sink) + theme(axis.text.y = element_blank(), axis.title.y = element_blank()))
  ggsave(out_path, plot = p, width = 10, height = 6, dpi = 300, bg = "white", create.dir = TRUE)
  log_artifact(out_path)
}

# Tuned theme for the box/sink comparison figure.
theme_profile_comparison <- function() {
  theme(
    panel.grid.major = element_blank(),
    panel.grid.minor = element_blank(),
    panel.background = element_rect(fill = "grey90"),
    panel.spacing.x = unit(1.5, "cm"),
    plot.margin = margin(5, 5, 5, 5),
    plot.title = element_text(hjust = 0.5, size = 22, face = "bold", margin = margin(0, 0, 10, 0)),
    axis.ticks = element_blank(),
    legend.justification = "right",
    legend.position = "inside",
    legend.position.inside = c(0.93, 0.90),
    legend.direction = "horizontal",
    legend.key.height = unit(0.8, "lines"),
    legend.key.width = unit(1.2, "lines"),
    legend.box.margin = margin(2, 2, 2, 2),
    legend.margin = margin(),
    legend.title = element_text(size = 18, vjust = 1),
    legend.text = element_text(size = 13, margin = margin(5, 0, 0, 0)),
    legend.background = element_blank(),
    legend.ticks = element_line(color = "black", linewidth = 0.4),
    legend.ticks.length = unit(0.2, "lines"),
    legend.frame = element_rect(color = "black", linewidth = 0.4),
    legend.spacing.y = unit(1.0, "lines")
  )
}
