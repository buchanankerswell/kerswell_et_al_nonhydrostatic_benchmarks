# Kerswell et al. (2027; in prep)

## Repository

This repository provides all materials for the manuscript *TBD* (Kerswell et al., 2027; in prep), including all datasets required to compile the study and scripts to reproduce all results and figures.

## Prerequisite software

### Python

I recommend installing the [miniforge](https://github.com/conda-forge/miniforge) python distribution. This includes a minimal installation of python (plus some dependencies) and the package manager [conda](https://docs.conda.io/en/latest/), which is required to build the necessary python environment for this study.

### R

R is a programming language used to visualize the results in this study. R can be downloaded from the [R Project homepage](https://www.r-project.org). Follow their instructions to install R on your machine.

### Pandoc

Pandoc is a universal document converter used to build a PDF version of the manuscript, which written in Markdown. Pandoc can be downloaded from the [Pandoc homepage](https://pandoc.org). Follow their instructions to install Pandoc on your machine.

## Reproducing the study

`make build` fetches the archived datasets, reproduces all results and figures, and builds a pdf version of the manuscript. It does not run simulations:

```bash
# Clone this repository
git clone https://github.com/buchanankerswell/kerswell_et_al_660_kinetics.git

# Change into the directory
cd kerswell_et_al_660_kinetics

# Get data and reproduce figures
make build
```

The full set of ASPECT solution files and 660 structural measurement dataset are downloaded from the [Zenodo dataset record](https://doi.org/10.5281/zenodo.24120946) during the build.

To run the simulations from scratch instead, link your installs at the project root as `<aspect_install_dir> -> aspect/` and `<dealii_install_dir> -> dealii/` (needed only for this step), then run `make models`. See [candi](https://github.com/dealii/candi) (deal.II >= v9.7.0) and [ASPECT](https://github.com/geodynamics/aspect) (ASPECT >= 3.1.0) for installation instructions.

## Coauthors

- [John Wheeler](https://scholar.google.com/citations?user=jsfp2-8AAAAJ&hl=en&oi=ao) (Department of Earth, Oceans and Ecological Sciences, University of Liverpool)
- [Rene Gassmöller](https://scholar.google.com/citations?user=Vk8SmssAAAAJ&hl=en&oi=ao) (GEOMAR Helmholtz Centre for Ocean Research Kiel)

## Acknowledgement

This work was funded by the UKRI NERC Large Grant no. NE/V018477/1. All computations were undertaken on Barkla2, part of the High Performance Computing facilities at the University of Liverpool, who graciously provided expert support. We thank the Computational Infrastructure for Geodynamics ([https://geodynamics.org](https://geodynamics.org)) which is funded by the National Science Foundation under awards EAR-0949446 and EAR-1550901 for supporting the development of ASPECT.

## Data Availability

All simulation outputs and post-processed data for reproducing this work are archived on Zenodo (TBD), as well as all analysis code (TBD). All data and code within these repositories are MIT Licensed and free for use and distribution (see license details). ASPECT version 3.1.0 ([Bangerth et al., 2024](https://doi.org/10.5281/zenodo.22814863)) was used for the computations in this study and is freely available under the GPL v2.0 or later license.

## Abstract

TBD
