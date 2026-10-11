"""Sphinx settings following the executable-gallery scientific package pattern."""

project = "EnerQit"
author = "EnerQit contributors"
release = "0.1.0"
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.viewcode",
    "numpydoc",
    "sphinx_gallery.gen_gallery",
]
html_theme = "alabaster"
html_title = "EnerQit 0.1.0"
exclude_patterns = ["_build"]
numpydoc_show_class_members = False
sphinx_gallery_conf = {
    "examples_dirs": "../../examples",
    "gallery_dirs": "auto_examples",
    "filename_pattern": r"/plot_",
    "download_all_examples": False,
    "abort_on_example_error": True,
    "remove_config_comments": True,
    "matplotlib_animations": False,
}
