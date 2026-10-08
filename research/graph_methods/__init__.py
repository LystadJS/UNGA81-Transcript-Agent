"""Development-only, source-aware spectral clustering and diffusion maps."""
from .core import GraphError, GraphPolicy, build_affinity, validate_input, equal_population
from .algorithms import (
    SpectralPolicy, DiffusionPolicy, spectral_clustering, diffusion_map,
    baseline_comparison, fidelity, grouped_leave_one_out, parameter_sensitivity,
)
from .interchange import to_interchange_v1, paired_representations
from .w1_bridge import availability as w1_availability, compare_w1_partition

__all__ = [
    "GraphError", "GraphPolicy", "build_affinity", "validate_input",
    "equal_population", "SpectralPolicy", "DiffusionPolicy",
    "spectral_clustering", "diffusion_map", "baseline_comparison",
    "fidelity", "grouped_leave_one_out", "parameter_sensitivity",
    "to_interchange_v1", "paired_representations", "w1_availability", "compare_w1_partition",
]
