"""Report generation package."""

from .data_source import generate_sample_data
from .formatter import generate_report
from .writer import write_report

__all__ = ['generate_sample_data', 'generate_report', 'write_report']
