"""
Comparison Engine
Compares N modules across their comparison_dimensions.
Produces structured data for frontend visualization.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.module import Module
from src.schemas.compare import ComparisonResult, Score


DEFAULT_DIMENSIONS = [
    "performance",
    "scalability",
    "ease_of_use",
    "cost_efficiency",
    "community",
    "maturity",
    "flexibility",
    "data_privacy",
]


class ComparisonEngine:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def compare(
        self,
        slugs: list[str],
        dimensions: list[str] | None = None,
        weights: dict[str, float] | None = None,
    ) -> ComparisonResult:
        """
        Compare 2-5 modules across dimensions.
        Returns structured comparison data.
        """
        # Fetch modules
        result = await self.db.execute(
            select(Module).where(Module.slug.in_(slugs))
        )
        modules = {m.slug: m for m in result.scalars().all()}

        # Validate all requested modules exist
        missing = set(slugs) - set(modules.keys())
        if missing:
            raise ValueError(f"Modules not found: {', '.join(missing)}")

        # Determine dimensions to compare
        dims = dimensions or DEFAULT_DIMENSIONS
        weights = weights or {}

        # Build comparison matrix
        matrix: dict[str, dict[str, Score]] = {}
        for slug in slugs:
            module = modules[slug]
            scores = module.comparison_scores or {}
            matrix[slug] = {}

            for dim in dims:
                dim_data = scores.get(dim, {})
                raw_score = dim_data.get("score", 5)
                matrix[slug][dim] = Score(
                    value=raw_score,
                    justification=dim_data.get("justification", "No data available"),
                    normalized=raw_score / 10.0,
                )

        # Compute rankings per dimension
        rankings: dict[str, list[str]] = {}
        for dim in dims:
            ranked = sorted(
                slugs,
                key=lambda s: (-round(matrix[s][dim].value, 6), s),
            )
            rankings[dim] = ranked

        # Compute overall ranking (weighted)
        overall_scores: dict[str, float] = {}
        for slug in slugs:
            total = 0.0
            total_weight = 0.0
            for dim in dims:
                w = weights.get(dim, 1.0)
                total += matrix[slug][dim].value * w
                total_weight += w
            overall_scores[slug] = total / total_weight if total_weight > 0 else 0

        overall_ranking = sorted(
            slugs,
            key=lambda s: (-round(overall_scores[s], 6), s),
        )

        # Generate highlights (top 2 strengths for each module)
        highlights: dict[str, list[str]] = {}
        for slug in slugs:
            module = modules[slug]
            scores_sorted = sorted(
                dims,
                key=lambda d: matrix[slug][d].value,
                reverse=True,
            )
            top_dims = scores_sorted[:2]
            highlights[slug] = [
                f"Strong in {dim.replace('_', ' ')}: {matrix[slug][dim].justification}"
                for dim in top_dims
            ]

        # Generate recommendation text
        recommendation = self._generate_recommendation(
            slugs, modules, matrix, dims, overall_ranking, weights
        )

        return ComparisonResult(
            modules=overall_ranking,
            dimensions=dims,
            matrix={
                slug: {dim: score for dim, score in dim_scores.items()}
                for slug, dim_scores in matrix.items()
            },
            rankings=rankings,
            overall_ranking=overall_ranking,
            highlights=highlights,
            recommendation=recommendation,
        )

    def _generate_recommendation(
        self,
        slugs: list[str],
        modules: dict[str, Module],
        matrix: dict[str, dict[str, Score]],
        dims: list[str],
        overall_ranking: list[str],
        weights: dict[str, float],
    ) -> str:
        """Generate a natural language recommendation."""
        top = overall_ranking[0]
        top_module = modules[top]

        # Find what the top module excels at
        best_dims = sorted(
            dims,
            key=lambda d: matrix[top][d].value,
            reverse=True,
        )[:3]
        best_dim_names = [d.replace("_", " ") for d in best_dims]

        parts = [
            f"Based on the comparison, **{top_module.name}** ranks highest overall, "
            f"particularly excelling in {', '.join(best_dim_names)}.",
        ]

        # Note runner-up
        if len(overall_ranking) > 1:
            runner = overall_ranking[1]
            runner_module = modules[runner]
            runner_best = sorted(
                dims,
                key=lambda d: matrix[runner][d].value,
                reverse=True,
            )[:2]
            runner_dim_names = [d.replace("_", " ") for d in runner_best]
            parts.append(
                f" **{runner_module.name}** is a strong alternative, "
                f"especially for {' and '.join(runner_dim_names)}."
            )

        # Add weight context
        if weights:
            priority_dims = sorted(weights.keys(), key=lambda k: weights[k], reverse=True)[:2]
            priority_names = [d.replace("_", " ") for d in priority_dims]
            parts.append(
                f" Given your emphasis on {' and '.join(priority_names)}, "
                f"this ranking reflects those priorities."
            )

        return "".join(parts)

    async def find_alternatives(
        self, slug: str, limit: int = 5
    ) -> list[dict]:
        """Find the best alternatives to a given module."""
        result = await self.db.execute(
            select(Module).where(Module.slug == slug)
        )
        module = result.scalar_one_or_none()
        if not module:
            return []

        alternatives = module.alternatives or []
        return alternatives[:limit]
