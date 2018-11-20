# coding: utf-8
from __future__ import absolute_import, division, print_function


def autodoc_process_signature(
        app, what, name, obj, options, signature, return_annotation,
):
    try:
        signature = obj.__parverdoc_signature__
    except AttributeError:
        pass
    else:
        return signature, return_annotation


def setup(app):
    app.connect('autodoc-process-signature', autodoc_process_signature)
