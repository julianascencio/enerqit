"""Sphinx settings following the executable-gallery scientific package pattern."""

project = "EnerQit"
author = "EnerQit contributors"
release = "0.1.0"
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.viewcode",
    "sphinx.ext.githubpages",
    "numpydoc",
    "sphinx_gallery.gen_gallery",
]
html_theme = "furo"
html_title = "EnerQit"
html_baseurl = "https://julianascencio.github.io/enerqit/"
html_static_path = ["_static"]
html_css_files = ["enerqit.css"]
html_favicon = "_static/favicon.svg"
html_theme_options = {
    "source_repository": "https://github.com/julianascencio/enerqit/",
    "source_branch": "main",
    "source_directory": "docs/sphinx/source/",
    "light_css_variables": {
        "color-brand-primary": "#126859",
        "color-brand-content": "#126859",
    },
    "dark_css_variables": {
        "color-brand-primary": "#83e3c4",
        "color-brand-content": "#83e3c4",
    },
}
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
