import fastai.data.core
import fastai.learner
import torch.nn

import pimmslearn.transform
from pimmslearn.analyzers import Analysis


class ModelAnalysis(Analysis):
    """Class describing what an ModelAnalysis
    is supposed to have as attributes."""

    model: torch.nn.Module
    dls: fastai.data.core.DataLoaders
    learn: fastai.learner.Learner
    params: dict
    transform: pimmslearn.transform.VaepPipeline
