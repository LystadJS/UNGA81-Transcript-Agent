"""Local model workbench. No approved model is bundled with the application."""
from .runtime import analyze_segments, predict_pair, source_windows

__all__ = ['analyze_segments', 'predict_pair', 'source_windows']
