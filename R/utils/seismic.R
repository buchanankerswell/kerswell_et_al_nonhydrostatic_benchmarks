# Profile-reference 410 depth (km, true depth): the Gibbs energy
# difference is zero in the BurnMan isentrope at 422.6 km.
# Passed explicitly by R/seismic.R.
nominal_410_sink_km <- 422.6

# Shared damping palette (same families as the structure panels). Per-value
# shades keep the paired Bimpl/Rel values distinct. None-family variants
# (CFL twins, no-feedback controls, off-default resolutions) get their own
# shades so every run in a panel is unique. Mirrors python DAMP_COLORS
# in simulation/mesh/config.py hex-for-hex.
damp_pal <- c(
  "None" = "#000000", "None_CFL1.0" = "#737373",
  "None_Dens" = "#2171B5",
  "None_Off" = "#08306B", "None_Off_Res5" = "#6BAED6", "None_Off_Res7" = "#08519C",
  "None_CFL0.25_Off" = "#9ECAE1", "None_CFL1.0_Off" = "#4292C6",
  "None_Res5" = "#969696", "None_Res7" = "#525252",
  "Bimpl1e19" = "#EF3B2C", "Bimpl1e19_CFL0.25" = "#FB6A4A", "Bimpl1e19_Res7" = "#FC9272",
  "Bimpl1e18" = "#E41A1C", "Bimpl1e20" = "#A50F15",
  "Bexpl1e19" = "#74ADD1", "Bexpl1e20" = "#377EB8",
  "Rel3.156e8" = "#C7E9C0", "Rel9.468e8" = "#B2E2B2",
  "Rel3.156e9" = "#A1D99B", "Rel9.468e9" = "#74C476",
  "Rel3.156e11_CFL0.25" = "#ADDD8E", "Rel3.156e11_CFL1.0" = "#238B45",
  "Rel3.156e11_Res5" = "#78C679", "Rel3.156e11_Res7" = "#4DAF4A",
  "Rel3.156e12" = "#00441B",
  "Rel3.156e10" = "#A6D96A", "Rel3.156e11" = "#1B7837",
  "Cap1e8" = "#984EA3", "Cap2e8" = "#C51B7D",
  "Cap2e8_CFL0.25" = "#F768A1", "Cap2e8_Res5" = "#F1B6DA", "Cap2e8_Res7" = "#8C0B4B",
  "Cap4e8" = "#762A83"
)

read_seismic_profile <- function(filepath) {
  df <- read_csv(filepath, show_col_types = FALSE)
  fname <- basename(filepath)
  df |>
    mutate(
      model_id = str_extract(fname, "(?<=seismic-profile-).*(?=-t[0-9]+-representative\\.csv)"),
      timestep = as.numeric(str_extract(fname, "(?<=-t)[0-9]+(?=-representative\\.csv)")),
      depth = true_depth_km,
      trace_x = trace_x / 1e3,
    )
}

read_suite_profiles <- function(data_dir, suite_label) {
  files <- list.files(data_dir, pattern = "seismic-profile-.*-t[0-9]+-representative\\.csv", full.names = TRUE)
  if (!length(files)) {
    log_error(paste("no representative seismic profiles in:", data_dir))
    return(NULL)
  }
  df <- map_df(files, read_seismic_profile) |> mutate(suite = suite_label)
  df |>
    group_by(model_id) |>
    filter(timestep == max(timestep)) |>
    ungroup()
}

read_init_profile <- function(data_dir) {
  files <- list.files(data_dir, pattern = "seismic-profile-.*DynpOn_DampNone.*-t0-representative\\.csv", full.names = TRUE)
  if (!length(files)) {
    return(NULL)
  }
  read_seismic_profile(files[1]) |> filter(!is.na(seismic_Vp))
}

visualize_seismic_comparison <- function(data_dir_sink, out_path, nominal_sink_km = nominal_410_sink_km,
                                         force_rewrite = FALSE, fig_dpi = 100) {
  if (!force_rewrite && plot_exists(out_path)) {
    return(invisible())
  }
  df <- read_suite_profiles(data_dir_sink, "Sink")
  if (is.null(df) || !nrow(df)) {
    return(invisible())
  }
  df <- df |>
    mutate(
      suite = factor(suite, levels = c("Sink")),
      damp = str_extract(model_id, "(?<=_Damp)[A-Za-z]+[\\d.e+-]*"),
      cfl = str_extract(model_id, "(?<=_CFL)[\\d.]+"),
      res = str_extract(model_id, "(?<=_Res)[0-9]+"),
      dynp = factor(str_extract(model_id, "(?<=_Dynp)(On|Dens|Off)"), levels = c("On", "Dens", "Off"))
    ) |>
    mutate(damp = ifelse(!is.na(cfl), paste0(damp, "_CFL", cfl), damp)) |>
    mutate(damp = ifelse(dynp == "Off", paste0(damp, "_Off"), ifelse(dynp == "Dens", paste0(damp, "_Dens"), damp))) |>
    mutate(damp = ifelse(!is.na(res) & res != "6", paste0(damp, "_Res", res), damp))
  df_init_sink <- read_init_profile(data_dir_sink)

  lim_vp <- range(c(
    df$seismic_Vp,
    if (!is.null(df_init_sink)) df_init_sink$seismic_Vp
  ), na.rm = TRUE)

  seismic_suite_panel <- function(suite_label, init_df, nominal_km) {
    d <- df |> filter(suite == suite_label)
    panel <- ggplot(d, aes(x = seismic_Vp, y = depth, group = model_id)) +
      annotate("rect", xmin = -Inf, xmax = Inf, ymin = nominal_km - 10, ymax = nominal_km + 10, fill = "grey80", alpha = 0.7) +
      geom_path(aes(color = damp, linetype = dynp), linewidth = 1.6, alpha = 0.85) +
      scale_y_reverse() +
      scale_x_continuous(limits = lim_vp, breaks = c(8, 9, 10, 11, 12)) +
      scale_color_manual(values = damp_pal, drop = TRUE, na.value = "grey50", name = "Damping") +
      scale_linetype_manual(values = c("On" = "solid", "Dens" = "dotdash", "Off" = "dashed"), drop = TRUE, name = "Feedback") +
      labs(x = expression(V[p] ~ "(km/s)"), y = "Depth (km)") +
      theme_bw(base_size = 14) +
      theme_profile_comparison()
    if (!is.null(init_df)) {
      panel <- panel + geom_path(data = init_df, color = "black", linewidth = 1.2, show.legend = FALSE)
    }
    panel + annotate("text", x = 8.05, y = nominal_km + 30, label = "410", size = 4, hjust = 0, color = "gray30")
  }

  p <- seismic_suite_panel("Sink", df_init_sink, nominal_sink_km)
  p <- p + theme(legend.position = "right")
  ggsave(out_path, plot = p, width = 6.5, height = 5.0, dpi = fig_dpi, bg = "white", create.dir = TRUE)
  log_artifact(out_path)
}

# Tuned theme for the sink profile figure.
theme_profile_comparison <- function() {
  theme(
    panel.grid.major = element_blank(),
    panel.grid.minor = element_blank(),
    panel.background = element_rect(fill = "grey90"),
    panel.spacing.x = unit(1.5, "cm"),
    plot.margin = margin(5, 5, 5, 5),
    plot.title = element_text(hjust = 0.5, size = 22, face = "bold", margin = margin(0, 0, 10, 0)),
    axis.ticks = element_blank(),
    legend.position = "right",
    legend.justification = NULL,
    legend.direction = "vertical",
    legend.key.height = unit(0.8, "lines"),
    legend.key.width = unit(1.2, "lines"),
    legend.box.margin = margin(2, 2, 2, 2),
    legend.margin = margin(),
    legend.title = element_text(size = 14, vjust = 1),
    legend.text = element_text(size = 11.2, margin = margin(5, 0, 0, 0)),
    legend.background = element_blank(),
    legend.ticks = element_line(color = "black", linewidth = 0.4),
    legend.ticks.length = unit(0.2, "lines"),
    legend.frame = element_rect(color = "black", linewidth = 0.4),
    legend.spacing.y = unit(1.0, "lines")
  )
}
