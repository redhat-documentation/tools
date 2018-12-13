atree - print a tree of asciidoc document inclusions

syntax: atree file|directory [file|directory]...

Prints a tree of asciidoc document inclusions.

INPUT
-----

The only possible parameter is the top level file, or a directory with the file, or a glob pattern for these. You can add this parameter multiple times.


OUTPUT
------

Included files are printed in order of appearance. Indentation shows the level of nesting. If the inclusion of a file is modified in some way, this is displayed:

* If a file is included, but the inclusion is commented out, the line with the included path begins with the // characters, to idicate the file is included but does not affect output:

  // this-is-a-commented-out-file.adoc

* If a file is included, but the inclusion is altered by conditionals, an additional line is shown which explains the conditionals, such as:

  modules/developer/con_hardening_c_cpp_code.adoc
      \- !!!  ifndef::developer-book

* If a file can not be read, its inclusion will be displayed, but no includes inside that file can be analyzed.


EXAMPLE
-------

1. Clone the Fedora quick docs repository:

   $ git clone https://pagure.io/fedora-docs/quick-docs.git

2. Change to the directory with top-level AsciiDoc files:

   $ cd quick-docs/modules/ROOT/pages

3. Show tree of some of the files: 

   $ atree securing-the-system-by-keeping-it-up-to-date.adoc
   securing-the-system-by-keeping-it-up-to-date.adoc
       {partialsdir}/con_why-it-is-important-keeping-your-system-up-to-date.adoc
       {partialsdir}/proc_manual-updating-using-gui.adoc
       {partialsdir}/proc_manual-updating-using-cli.adoc
       {partialsdir}/proc_setting-automatic-updates.adoc


KNOWN ISSUES
------------

* If an attribute is used in the include macro, the attribute is not uderstood and thus also not expanded. The include is displayed, but the actual file can not be loaded and thus any further inclusions are not shown.

* All includes in comments are listed, including these that are not intended as part of the document, but only comment.


HINTS
-----

* If there is only a single AsciiDoc file in the directory, atree will assume that's the one you want analyzed, even if you do not specify it.

* You can specify the input with glob patterns, including directory traversal /**/. This lets you construct very powerful queries.

* You can use egrep to add search and highlighting:
  atree | egrep --color "SOME-FILE-I-WANT-HIGHLIGHTED|$"

