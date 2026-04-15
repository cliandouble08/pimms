# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What is PIMMS

PIMMS (Proteomics Imputation Modeling Mass Spectrometry) is a Python package (`pimms-learn` on PyPI, imported as `pimmslearn`) for imputing missing values in label-free quantitative mass spectrometry proteomics data using self-supervised deep learning. Published in Nature Communications (2024). It provides:

1. A **scikit-learn-style transformer interface** for easy use in notebooks/scripts
2. A **Snakemake comparison workflow** for benchmarking imputation methods including R-based methods

## Environment Setup

```bash
# Full environment (conda/mamba recommended):
mamba env create -n pimms -f environment.yml
conda activate pimms

# Minimal install (pip only):
pip install pimms-learn
pip install pimms-learn[docs]  # for documentation building
```

## Common Commands

### Testing
```bash
# Run all tests
pytest .

# Run a single test file
pytest tests/test_ae.py

# Run with coverage
pytest --cov=pimmslearn
```

### Linting and Formatting
```bash
# Format (CI uses black + isort on pimmslearn/ only)
black pimmslearn
isort pimmslearn

# Lint
ruff check pimmslearn
```

### Running Notebooks as Scripts
Notebooks in `project/` are dual-format (jupytext): both `.ipynb` and `.py:percent` (`.py`) files are kept in sync.

```bash
cd project

# Check available parameters
papermill 01_0_split_data.ipynb --help-notebook

# Execute a notebook as script (output = second arg)
papermill 01_1_train_VAE.ipynb runs/out_VAE.ipynb

# Convert .py to .ipynb and run
jupytext --to ipynb -k - -o - 01_1_train_KNN.py | papermill - runs/01_1_train_KNN.ipynb
```

### Snakemake Workflows
All workflow commands run from the `project/` folder:

```bash
cd project

# Dry-run demo (50-sample HeLa protein groups)
snakemake -c1 -p -n

# Execute demo workflow
snakemake -c1 -p

# Run with a specific config
snakemake --configfile config/single_dev_dataset/example/config.yaml -p -c1 -n

# Imputation comparison + differential analysis (Alzheimer example)
snakemake -s workflow/Snakefile_v2.smk --configfile config/alzheimer_study/config.yaml -p -c2
snakemake -s workflow/Snakefile_ald_comparison.smk --configfile config/alzheimer_study/comparison.yaml -p -c1

# Build website output
pimms-setup-imputation-comparison -f project/runs/alzheimer_study/
pimms-add-diff-comp -f project/runs/alzheimer_study/ -sf_cp project/runs/alzheimer_study/diff_analysis/AD
cd project/runs/alzheimer_study/ && sphinx-build -n --keep-going -b html ./ ./_build/
```

## Code Architecture

### Package: `pimmslearn/`

The installable Python package. Key modules:

- **`sklearn/ae_transformer.py`** — `AETransformer` class: scikit-learn `TransformerMixin` wrapping DAE/VAE models. Uses FastAI `Learner` internally. Input: wide DataFrame (samples × features). Normalizes internally via `StandardScaler` + `SimpleImputer` preprocessing pipeline.
- **`sklearn/cf_transformer.py`** — `CollaborativeFilteringTransformer`: scikit-learn interface for CF model. Input: long-format `pd.Series` with MultiIndex `(sample, feature)`.
- **`models/vae.py`** — PyTorch `nn.Module` implementations for VAE and DAE. Encoder/decoder with BatchNorm1D and LeakyReLU. Symmetric architecture (decoder mirrors encoder).
- **`models/`** — also contains `ae.py` (autoencoder training logic), `analysis.py`, `collect_dumps.py`
- **`io/`** — data loading/saving: `datasplits.py` (`DataSplits` class with train_X/val_y/test_y splits), `datasets.py`, `dataloaders.py`, `format.py`, `load.py`, `types.py`
- **`analyzers/`** — post-training analysis: `analyzers.py`, `compare_predictions.py`, `diff_analysis.py`
- **`cmd_interface/`** — CLI entry points: `pimms-setup-imputation-comparison` and `pimms-add-diff-comp` for building Sphinx-based result websites
- **`pandas/`** — error calculation (`calc_errors.py`), missing data utilities (`missing_data.py`)
- **`plotting/`** — plotting defaults and plotly helpers
- **`imputation.py`** — heuristic imputation methods (standard deviation-based, KNN)
- **`normalization.py`**, **`transform.py`**, **`filter.py`**, **`sampling.py`** — data preprocessing utilities
- **`nb.py`** — notebook utilities (papermill/jupytext helpers)
- **`data_handling.py`** — general data handling utilities

### Project: `project/`

A standalone folder (can be copied separately once `pimmslearn` is installed) containing the experimental workflow. Key structure:

- **`workflow/`** — Snakemake workflow files (`Snakefile_v2.smk`, `Snakefile_ald_comparison.smk`, etc.)
- **`config/`** — YAML config files per experiment (data path, model hyperparameters, split settings)
- **`data/`** — input datasets (e.g. `data/dev_datasets/HeLa_6070/`)
- **`runs/`** — output of experiments (created at runtime)
- **`src/R_NAGuideR/`** — R scripts for NAGuideR-based imputation methods

Notebook naming conventions in `project/`:
- `00_*` — data inspection/manipulation
- `01_*` — single experiment (split, train one model, performance plots)
- `02_*` — grid search aggregation and analysis
- `03_*` — best model comparison across datasets
- `04_*` — tutorials (scikit-learn interface)
- `10_*` — ALD differential analysis workflow
- `misc_*` — exploratory notebooks

### Data Flow

1. **Input**: Wide (samples × features) or long (Sample ID, Feature, Value) CSV/pickle files with log2-transformed intensities
2. **Split** (`01_0_split_data`): Creates `DataSplits` with train/val/test, simulates missing values for evaluation
3. **Train** (`01_1_train_<model>`): Fits one imputation model, saves predictions to `runs/<experiment>/preds/pred_real_na_<model>.csv`
4. **Evaluate** (`01_2_performance_plots`): Compares imputation error (MAE/MSE) across methods

### Version

Version is derived dynamically from git tags via `setuptools_scm` (see `pyproject.toml`). No hardcoded version in source.

### Key Constraints

- `pingouin<0.6.0` — pingouin renamed internal columns in 0.6.0 (breaking change)
- `fastprogress<1.1.0` — compatibility with ipython
- `pandas<3.0` — pandas 3.0 has breaking changes
- Windows is not fully supported for the conda workflow (some R packages like `rrcovNA` can't be built from source on Windows)
