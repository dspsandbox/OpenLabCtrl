import os
import sys
import json
from datetime import date
import sphinx.util.inspect as _sphinx_inspect
import sphinx.ext.autodoc as _autodoc
from sphinx.ext.autodoc import AttributeDocumenter, ClassDocumenter

def _json_default(obj):
    if isinstance(obj, type):
        return obj.__name__
    if isinstance(obj, int):
        return hex(obj)
    return repr(obj)

_orig_object_description = _sphinx_inspect.object_description

def _object_description(obj):
    if isinstance(obj, (dict, list)):
        return ""
    return _orig_object_description(obj)

_sphinx_inspect.object_description = _object_description
_autodoc.object_description = _object_description

def _contains_types(obj):
    if isinstance(obj, type):
        return True
    if isinstance(obj, dict):
        return any(_contains_types(v) for v in list(obj.keys()) + list(obj.values()))
    if isinstance(obj, (list, tuple)):
        return any(_contains_types(v) for v in obj)
    return False

def _format_with_links(obj, indent=0):
    pad = "  " * indent
    inner = "  " * (indent + 1)
    if isinstance(obj, type):
        return f":class:`~{obj.__module__}.{obj.__name__}`"
    elif isinstance(obj, dict):
        if not obj:
            return "{}"
        parts = []
        items = list(obj.items())
        for i, (k, v) in enumerate(items):
            comma = "," if i < len(items) - 1 else ""
            parts.append(f'{inner}"{k}": {_format_with_links(v, indent + 1)}{comma}')
        return "{\n" + "\n".join(parts) + f"\n{pad}}}"
    elif isinstance(obj, list):
        if not obj:
            return "[]"
        parts = []
        for i, v in enumerate(obj):
            comma = "," if i < len(obj) - 1 else ""
            parts.append(f"{inner}{_format_with_links(v, indent + 1)}{comma}")
        return "[\n" + "\n".join(parts) + f"\n{pad}]"
    elif isinstance(obj, int):
        return f'"{hex(obj)}"'
    else:
        return json.dumps(obj)

_orig_sort_members = ClassDocumenter.sort_members
_class_registry: dict = {}

def _sort_inherited_last(self, documenters, order):
    documenters = _orig_sort_members(self, documenters, order)
    try:
        if not isinstance(self.object, type):
            return documenters
        _class_registry[self.object.__name__] = self.object
        own_names = set(vars(self.object))
        own = [(d, s) for d, s in documenters if d.objpath and d.objpath[-1] in own_names]
        inh = [(d, s) for d, s in documenters if not (d.objpath and d.objpath[-1] in own_names)]
        return own + inh
    except Exception:
        return documenters

ClassDocumenter.sort_members = _sort_inherited_last


def _inherited_defining_class(what, name, obj):
    parts = name.split('.')
    if len(parts) < 2:
        return None, None
    class_name = parts[-2]
    member_name = parts[-1]
    target = obj.fget if isinstance(obj, property) else obj
    qualname = getattr(target, '__qualname__', None)

    if qualname and '.' in qualname:
        qualname_class = qualname.rsplit('.', 1)[0]
        if '<' not in qualname_class:
            defining_class = qualname_class.split('.')[-1]
            if defining_class != class_name:
                return defining_class, getattr(target, '__module__', None)

    # Fallback for plain class attributes (no __qualname__): walk MRO
    cls = _class_registry.get(class_name)
    if cls is not None and member_name not in vars(cls):
        for parent in cls.__mro__[1:]:
            if member_name in vars(parent) and parent is not object:
                return parent.__name__, parent.__module__

    return None, None


def _suppress_inherited_signature(app, what, name, obj, options, signature, return_annotation):
    if what not in ('method', 'property'):
        return None
    defining_class, _ = _inherited_defining_class(what, name, obj)
    if defining_class is not None:
        # record_typehints already stored annotations; remove them so
        # merge_typehints (object-description-transform) won't add a Parameters section
        app.env.temp_data.get('annotations', {}).pop(name, None)
        return ('', None)
    return None


def _mark_inherited(app, what, name, obj, options, lines):
    if what not in ('method', 'property'):
        return
    member_name = name.split('.')[-1]
    defining_class, module = _inherited_defining_class(what, name, obj)
    if defining_class is None:
        return
    role = 'meth' if what == 'method' else 'attr'
    suffix = '()' if what == 'method' else ''
    display = f'{defining_class}.{member_name}{suffix}'
    ref = f':{role}:`{display} <{module}.{defining_class}.{member_name}>`' if module else f':{role}:`{display}`'
    lines.clear()
    lines.append(f'See {ref}.')


def _strip_enum_preamble(_app, what, _name, _obj, _options, lines):
    if what == 'class' and lines and lines[0].strip() == 'An enumeration.':
        lines.pop(0)
        while lines and lines[0].strip() == '':
            lines.pop(0)


def setup(app):
    app.connect('autodoc-process-signature', _suppress_inherited_signature)
    app.connect('autodoc-process-docstring', _mark_inherited)
    app.connect('autodoc-process-docstring', _strip_enum_preamble)


_orig_attr_directive_header = AttributeDocumenter.add_directive_header

def _patched_attr_directive_header(self, sig):
    if isinstance(self.parent, type):
        member_name = self.objpath[-1] if self.objpath else None
        if member_name and member_name not in vars(self.parent):
            self.options.no_value = True
    _orig_attr_directive_header(self, sig)

AttributeDocumenter.add_directive_header = _patched_attr_directive_header

_orig_add_content = AttributeDocumenter.add_content

def _patched_add_content(self, more_content):
    _orig_add_content(self, more_content)
    try:
        obj = self.object
    except Exception:
        return
    # For any inherited attribute inject a link and skip the content block
    if isinstance(self.parent, type):
        member_name = self.objpath[-1] if self.objpath else None
        if member_name and member_name not in vars(self.parent):
            for parent_cls in self.parent.__mro__[1:]:
                if member_name in vars(parent_cls) and parent_cls is not object:
                    display = f'{parent_cls.__name__}.{member_name}'
                    ref = f':attr:`{display} <{parent_cls.__module__}.{parent_cls.__name__}.{member_name}>`'
                    src = self.get_sourcename()
                    self.add_line(f'See {ref}.', src)
                    self.add_line('', src)
                    break
            return
    if not isinstance(obj, (dict, list)):
        return
    src = self.get_sourcename()
    self.add_line("", src)
    if _contains_types(obj):
        formatted = _format_with_links(obj)
        self.add_line(".. parsed-literal::", src)
        self.add_line("", src)
        for line in formatted.splitlines():
            self.add_line("   " + line, src)
    else:
        formatted = json.dumps(obj, indent=2, default=_json_default)
        self.add_line(".. code-block:: json", src)
        self.add_line("", src)
        for line in formatted.splitlines():
            self.add_line("   " + line, src)
    self.add_line("", src)

AttributeDocumenter.add_content = _patched_add_content

sys.path.insert(0, os.path.abspath("../driver/src"))

try:
    import tomllib
except ImportError:
    import tomli as tomllib

with open(os.path.join(os.path.dirname(__file__), "../driver/pyproject.toml"), "rb") as _f:
    _pyproject = tomllib.load(_f)

project = _pyproject["project"]["name"]
author = _pyproject["project"]["authors"][0]["name"]
release = _pyproject["project"]["version"]
copyright = f"{date.today().year}, {author}"

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx.ext.intersphinx",
    "myst_nb",
]

nb_execution_mode = "off"
suppress_warnings = ["myst.header", "myst.xref_missing"]

autodoc_mock_imports = ["zynq_tcp_ctrl"]
autodoc_member_order = "bysource"
autodoc_typehints = "description"
autodoc_preserve_defaults = True

napoleon_google_docstring = True
napoleon_numpy_docstring = True

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "numpy": ("https://numpy.org/doc/stable", None),
}

html_theme = "furo"
html_title = f"OpenLabCtrl {release}"

exclude_patterns = ["_build"]
