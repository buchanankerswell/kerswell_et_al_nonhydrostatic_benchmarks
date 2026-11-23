# Single source of truth for numeric constants shared by the R figures
# (the R analogue of python/simulation/mesh/config.py). Values mirror
# project.mk; R entry scripts source the whole utils/ directory, so
# everything defined here is visible to every figure and table.

# Seconds per mega-annum: file reaction rates are 1/s, figures use 1/Ma.
s_per_ma <- 3.154e13
