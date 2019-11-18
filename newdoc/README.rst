###########################
README: The `newdoc` script
###########################

This script is used for generating empty module and assembly files when writing Red Hat or Fedora documentation in AsciiDoc. The generated files follow template guidelines set up by the Modular Documentation initiative: https://redhat-documentation.github.io/modular-docs/.

The script is now compatible with both Python 3 (for Fedora and community distributions) and Python 2.7 (for RHEL 7 and macOS).

It hasn't been tested on Windows.


============================
How do I install the script?
============================

* To install ``newdoc`` on Fedora or RHEL 8, use the Copr package repository::

    # dnf copr enable mareksu/newdoc
    # dnf install python3-newdoc

* On a different Linux distribution that includes Python 3, use the ``pip`` package manager, version 3::

    # pip3 install newdoc

* On RHEL 7, CentOS 7, or macOS, use the ``pip`` package manager, version 2::

    # pip install newdoc


==========================
How do I add a new module?
==========================

1. In the directory where modules are located, use the ``newdoc`` script to create a new file::

    modules-dir]$ newdoc --procedure "Setting up thing"

2. Rewrite the information in the template with your docs.

The script also accepts the ``--concept`` and ``--reference`` options. You can use these short forms instead: ``-p``, ``-c``, and ``-r``.


============================
How do I add a new assembly?
============================

1. In the directory where assemblies are located, use the ``newdoc`` script to create a new file::

    assemblies-dir]$ newdoc --assembly "Achieving thing"
    
2. Rewrite the information in the template with your docs.

    Add AsciiDoc include statements to include modules. See `Include Files <https://asciidoctor.org/docs/asciidoc-syntax-quick-reference/#include-files>`_ in the AsciiDoc Syntax Quick Reference.

You can use the short form of the ``--assembly`` option instead: ``newdoc -a "Achieving thing"``.


=============
Configuration
=============

``newdoc`` enables you to configure multiple aspects of its behavior:

* Custom templates for assemblies and modules,
* How IDs are capitalized when converted from a title,
* What symbol is used to replace spaces in IDs.

These options can be set in the ``newdoc.ini`` configuration file, which is located:

* On Fedora, RHEL, and other Linux distributions, in ``~/.config/newdoc/newdoc.ini``
* On macOS, in ``~/Library/Preferences/newdoc/newdoc.ini``

The configuration file is not created automatically: if you want to set custom options, create it using a plain text editor.

The file must always start with the ``[newdoc]`` header. An example configuration is available in this repo at ``examples/newdoc.ini``.


----------------
Custom templates
----------------

In the config file, you can set paths to custom AsciiDoc template files for each module type. The options are:

* ``assembly_template``
* ``concept_template``
* ``procedure_template``
* ``reference_template``

For example, to use a custom template for reference modules, use::

   reference_template = ~/.config/newdoc/my-reference-template.adoc

``newdoc`` performs substitutions on the templates using the Python ``string.template`` library. The following strings are replaced:

* ``${module_title}`` with the entered title of the module
* ``${module_id}`` with the generated ID of the module
* ``${filename}`` with the generated file name of the module

For more details on the template syntax, see: https://docs.python.org/3/library/string.html#template-strings


----------------
ID substitutions
----------------

* The ``id_case`` option in the config file controls how the letter case should change from the title to the ID:

    * ``id_case = lowercase``: All letters in the ID will be lower-case
    * ``id_case = capitalize``: The first letter will be upper-case, the rest lower-case
    * ``id_case = preserve``: Keep the capitalization as entered in the title

* The ``word_separator`` option lets you choose the symbol (or string) used to replace spaces in the ID. The default is a dash::

    word_separator = -

=====
Notes
=====

* If you prefer ``newdoc`` to generate file without the explanatory comments, add the ``--no-comments`` or ``-C`` option when creating documents.


====================
Additional resources
====================

* `Modular Documentation Reference Guide <https://redhat-documentation.github.io/modular-docs/>`_
* `AsciiDoc Mark-up Quick Reference for Red Hat Documentation <https://redhat-documentation.github.io/asciidoc-markup-conventions/>`_

