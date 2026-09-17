"""Sphinx configuration for the project documentation."""

from pathlib import Path
import sys


# Make the src-layout package importable when Sphinx is invoked directly.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

project = "Quantum Circuit Simulator"
copyright = "2026, Finn Pedace and Jannis Schuhmacher"
author = "Finn Pedace and Jannis Schuhmacher"
release = "0.1.0"

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.mathjax",
    "sphinx.ext.viewcode",
]
autosummary_generate = True
autodoc_member_order = "bysource"
autodoc_typehints = "description"

exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]
language = "de"

html_theme = "alabaster"
html_title = f"{project} {release}"
