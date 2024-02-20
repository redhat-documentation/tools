# atree - print a tree of asciidoc document inclusions

Prints a tree of asciidoc document inclusions.

syntax:

```
atree [file|directory|option]...
```


## Input

The possible parameters are:

* Top level file
* Directory with a top level file
* Glob pattern for files or directories
* Option

You can specify as many inputs as needed. Inputs are processed in order of appearance. This means that options must be specified before the files they are supposed to affect.

If no input files or directories are specified, the current directory is tried.

### Path handling details

When atree encounters a glob pattern, it expands it first and then handles the resulting paths as if listed manually.

If a path is a file, atree tries to parse and analyze it as an AsciiDoc file. If a path is a directory instead, atree checks for existence of files in this order:

1. `master.adoc`
2. `index.adoc`
3. any `*.adoc` file, but only if there is just a single such file


### Options

* `-a`  Use annotated output (default).
* `-b`  Use full path output.
* `-l`  Use literal include line output.

* `-c`  Display commented-out includes in annotated mode.
* `-x`  Analyze commented-out includes.
* `-h`  Hide hints for human user.

All options in the second group have their inverse in uppercase, which is also the default state. For example, atree does not show commented out includes by default, but you can get them with `-c`, and later return to the default with `-C`.


## Output

Output differs by mode. Default mode is annotated.

### Annotated output

This output mode is intended for consumption by humans. Included files are printed in order of appearance. Indentation shows the level of nesting. If the inclusion of a file is modified in some way, this is displayed:

* If a file is included, but the inclusion is commented out, the line with the included path begins with the `//` characters, to indicate the file is included but does not affect output:

    ```
    // this-is-a-commented-out-file.adoc
    ```

* If a file is included, but the inclusion is altered by conditionals, an additional line is shown which explains the conditionals, such as:

    ```
    modules/developer/con_hardening_c_cpp_code.adoc
        \- !!!  ifndef::developer-book
    ```

* If a file can not be read, its inclusion will be displayed, but no includes inside that file can be analyzed.

* If a file cannot be analyzed, the reason will be shown with flags. The flags are:
  
    * `R!` the file includes itself, infinitely recursive inclusion
    * `N!` the file does not exist
    * `X!` the file name is not valid
  
    Example of outputs with flags:
  
    ```
    N! some/nonexistent/file.adoc
    //R! the-same-file.adoc
    X! an|invalid*path/somefile.adoc
    ```


### Full path output

This mode is intended for consumption by other tools. The output consists only of absolute paths, one on a line. No indenting to show include level is printed. Commented out files will not be listed. Conditionals and flags are not displayed. Invalid or nonexistent files will still be listed.

Note that using the `-c` option will enable analysis of commented out includes, but they will not be shown.

### Literal output

This mode prints include lines as encountered in the files. Handling of flags, conditions, comments etc. is identical to full path output.

The top level file has no include statement and therefore has a special line: `<top: the-top-file.adoc>`.

Note that attributes are expanded before this listing, so the includes are not verbatim as shown in the files.


## Example

1. Clone the Fedora quick docs repository:

   ```
   $ git clone https://pagure.io/fedora-docs/quick-docs.git
   ```

2. Change to the directory with top-level AsciiDoc files:

   ```
   $ cd quick-docs/modules/ROOT/pages
   ```

3. Show tree of some of the files:

   ```
   $ atree securing-the-system-by-keeping-it-up-to-date.adoc
   securing-the-system-by-keeping-it-up-to-date.adoc
       {partialsdir}/con_why-it-is-important-keeping-your-system-up-to-date.adoc
       {partialsdir}/proc_manual-updating-using-gui.adoc
       {partialsdir}/proc_manual-updating-using-cli.adoc
       {partialsdir}/proc_setting-automatic-updates.adoc
   ```


## Known issues

* AsciiDoctor apparently uses some special handling for absolute paths. This syntax is not understood by atree and the file will be treated as non-existent (`N!`).

  See also https://github.com/redhat-documentation/tools/issues/21

* If an attribute is used in the include macro, the attribute must be defined in the document tree. There is no way to define an attribute manually / externally. Because undefined attributes can not not expanded, includes containing these are displayed, but the actual files can not be loaded and thus any further inclusions are not shown.

* All includes in comments are listed, including these that are not intended as part of the document, but only comment. There is no way to distinguish these automatically.


## Hints

* If there is only a single AsciiDoc file in the directory, atree will assume that is the one you want analyzed, even if you do not specify it.

* You can specify the input with glob patterns, including directory traversal `/**/`. This lets you construct very powerful queries.

* You can pipe atree output to egrep to add search and highlighting:

    ```
    $ atree | egrep --color "SOME-FILE-I-WANT-HIGHLIGHTED|$"
    ```

* When in doubt, check the source...
