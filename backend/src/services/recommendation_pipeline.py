"""Backward-compatible exports for Phase-2 pipelines."""

from src.services.pipelines.base import PipelineResult, attach_pipeline_context
from src.services.pipelines.vector_db import VectorDbRecommendationPipeline

__all__ = ["PipelineResult", "VectorDbRecommendationPipeline", "attach_pipeline_context"]
