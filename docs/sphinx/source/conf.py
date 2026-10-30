"""Scientific documentation using the same PyData layout as OrbitalPV."""

import html
import json
import os
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
EXAMPLES = ROOT / "docs" / "examples"
sys.path.insert(0, str(ROOT))

from enerqit import __version__  # noqa: E402

project = "EnerQit"
author = "ASVA Consulting and EnerQit contributors"
copyright = "2026, ASVA Consulting and EnerQit contributors"
release = __version__
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.mathjax",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx.ext.githubpages",
    "sphinx_gallery.gen_gallery",
]
autosummary_generate = True
autodoc_typehints = "description"
autodoc_member_order = "bysource"
napoleon_google_docstring = True
napoleon_numpy_docstring = True
exclude_patterns = ["_build", "auto_examples"]

html_theme = "pydata_sphinx_theme"
html_title = "EnerQit"
html_baseurl = "https://julianascencio.github.io/enerqit/"
html_static_path = ["_static"]
html_css_files = ["enerqit.css"]
html_favicon = "_static/favicon.svg"
html_show_sourcelink = False
html_theme_options = {
    "github_url": "https://github.com/julianascencio/enerqit",
    "use_edit_page_button": True,
    "show_toc_level": 2,
    "show_prev_next": False,
    "navbar_align": "left",
    "header_links_before_dropdown": 5,
}
html_context = {
    "github_user": "julianascencio",
    "github_repo": "enerqit",
    "github_version": "main",
    "doc_path": "docs/sphinx/source",
}
sphinx_gallery_conf = {
    "examples_dirs": str(EXAMPLES),
    "gallery_dirs": "gallery",
    "filename_pattern": r"/plot_",
    "download_all_examples": False,
    "abort_on_example_error": True,
    "remove_config_comments": True,
    "matplotlib_animations": False,
}


def gallery_source_links(app, pagename, templatename, context, doctree):
    """Send gallery edit links to maintained scripts rather than generated RST."""
    if pagename == "gallery/index":
        source = "docs/examples/README.rst"
    elif pagename.startswith("gallery/plot_"):
        source = f"docs/examples/{pagename.rsplit('/', 1)[-1]}.py"
    elif pagename.endswith("sg_execution_times"):
        context["page_source_suffix"] = None
        return
    else:
        return
    file_name = f"{pagename}{context['page_source_suffix']}"
    context["gallery_sources"] = {file_name: source}
    context["edit_page_url_template"] = (
        "{{ github_url }}/{{ github_user }}/{{ github_repo }}/edit/"
        "{{ github_version }}/{{ gallery_sources[file_name] }}"
    )
    context["edit_page_provider_name"] = "GitHub"


def preserve_gallery_urls(app, exception):
    """Keep published auto_examples URLs and downloads working after the redesign."""
    if exception is not None or app.builder.format != "html":
        return
    output = Path(app.outdir)
    gallery = output / "gallery"
    for source in gallery.rglob("*"):
        if not source.is_file():
            continue
        alias = output / "auto_examples" / source.relative_to(gallery)
        if source.suffix == ".html":
            alias.parent.mkdir(parents=True, exist_ok=True)
            target = os.path.relpath(source, alias.parent).replace(os.sep, "/")
            escaped = html.escape(target, quote=True)
            alias.write_text(
                "<!doctype html>\n<html lang=\"en\"><head><meta charset=\"utf-8\">\n"
                '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
                '<title>EnerQit — Example Gallery</title>\n'
                f'<link rel="canonical" href="{escaped}">\n'
                f'<meta http-equiv="refresh" content="0; url={escaped}">\n'
                f"<script>window.location.replace({json.dumps(target)}"
                "+window.location.search+window.location.hash);</script>\n"
                f'</head><body><p>This example has moved to <a href="{escaped}">'
                "the Example Gallery</a>.</p></body></html>\n",
                encoding="utf-8",
            )
        elif source.suffix in {".py", ".ipynb", ".zip"}:
            alias.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, alias)


def setup(app):
    app.connect("html-page-context", gallery_source_links)
    app.connect("build-finished", preserve_gallery_urls)
