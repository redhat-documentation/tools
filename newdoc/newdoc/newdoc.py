#!/usr/bin/env python3

from __future__ import print_function, unicode_literals
import sys
import os
import io
import argparse
from string import Template

NEWDOC_VERSION = "1.3.2"

# Record whether we're running under Python 2 or 3
PYVERSION = sys.version_info.major

# The configparser module is called ConfigParser in Python2
if PYVERSION == 2:
    import ConfigParser as cp
else:
    import configparser as cp

# Force Python 2 to use the UTF-8 encoding. Otherwise, loading a template
# containing Unicode characters fails.
if PYVERSION == 2:
    reload(sys)
    sys.setdefaultencoding('utf8')

# The directory where the script is located
SCRIPT_HOME_DIR = os.path.dirname(__file__)

# The directory where templates are located, relative to this script
TEMPLATES_DIR = os.path.join(SCRIPT_HOME_DIR, "templates")

DEFAULT_OPTIONS = {
    "id_case": "lowercase",
    "word_separator": "-",
    # The names of template files for different doc types
    "assembly_template": os.path.join(TEMPLATES_DIR, "assembly_title.adoc"),
    "concept_template": os.path.join(TEMPLATES_DIR, "con_title.adoc"),
    "procedure_template": os.path.join(TEMPLATES_DIR, "proc_title.adoc"),
    "reference_template": os.path.join(TEMPLATES_DIR, "ref_title.adoc"),
    # Templates can be downloaded from a repository
    "online_templates": False
}

# def get_config_dir() -> str:
def get_config_dir():
    """
    Finds the appropriate user configuration directory where newdoc can store
    its configuration.
    Extracted form the appdirs library: https://github.com/ActiveState/appdirs
    """
    # Typical user config directories are:
    #   Mac OS X:  ~/Library/Preferences/<AppName>
    #   Unix:      ~/.config/<AppName>     # or in $XDG_CONFIG_HOME, if defined
    #   Win *:     same as user_data_dir
    platform = sys.platform

    if platform == "linux":
        os_config_dir = os.getenv("XDG_CONFIG_HOME", os.path.expanduser("~/.config"))
    elif platform == "darwin":
        os_config_dir = os.path.expanduser("~/Library/Preferences/")
    elif platform == "win32":
        print("newdoc has not been tested on Windows, and the configuration "
              "file functionality is not available here.")
        os_config_dir = None
    else:
        os_config_dir = os.path.expanduser("~/.config")

    return os.path.join(os_config_dir, "newdoc")

# def get_config() -> dict:
def get_config():
    """
    Tries to find config options in the platform-specific user config file,
    otherwise falls back to defaults.
    """
    config_dir = get_config_dir()
    config_file = os.path.join(config_dir, "newdoc.ini")

    # Copy default options to start with:
    options = DEFAULT_OPTIONS

    # Search for matching keys in the config file; if found,
    # update the options dict with them
    if os.path.isfile(config_file):
        config = cp.ConfigParser()
        try:
            config.read(config_file)
        except cp.MissingSectionHeaderError:
            print("Error: The [newdoc] section is required in the configuration file.")
            exit(1)

        for k in options.keys():
            # The configparser library is different in Python 2 and 3.
            # This si the only 2/3-compatible way I've found for optional keys.
            try:
                options[k] = config.get("newdoc", k)
            except cp.NoOptionError:
                pass

    return options


# def convert_title_to_id(title: str, doc_type: str) -> str:
def convert_title_to_id(title, doc_type, options):
    """
    Converts the human-readable title to an ID string.
    """

    # Some substitution rules, such as capitalization and word separator,
    # are found in the `options` dict inherited from the calling scope
    if options["id_case"] in ["lowercase", "lower-case", "lower case"]:
        # Convert to lowercase:
        converted_id = title.lower()
    elif options["id_case"] in ["capitalize", "capitalise"]:
        # First letter capitalized, subsequent letters lower-case:
        converted_id = title.capitalize()
    elif options["id_case"] in ["preserve", "original"]:
        converted_id = title
    else:
        print("Error: ID capitalization option not recognized: '{}'".format(
            options["id_case"]))
        exit(1)

    # This dict specifies all char substitutions to make on the ID
    subst_map = {
        " ": options["word_separator"],
        "(": "",
        ")": "",
        "?": "",
        "!": "",
        "'": "",
        '"': "",
        "#": "",
        "%": "",
        "&": "",
        "*": "",
        ",": "",
        ".": "-",
        "/": "-",
        ":": "-",
        ";": "",
        "@": "",
        "[": "",
        "]": "",
        "\\": "",
        # TODO: Curly braces shouldn't appear in the title in the first place.
        # They'd be interpreted as attributes there.
        # Print an error in that case? Escape them with AciiDoc escapes?
        "{": "",
        "}": ""
    }

    # Python 2 needs special treatment
    if PYVERSION == 2:
        for k in subst_map.keys():
            v = subst_map[k]
            converted_id = converted_id.replace(k, v)
    # Python 3 can use the `translate` function
    else:
        trans_table = str.maketrans(subst_map)

        # Perform the substitutions specified by the above dict/table
        converted_id = converted_id.translate(trans_table)

    # Make sure the converted ID doesn't contain double dashes ("--"), because
    # that breaks references to the ID
    while "--" in converted_id:
        converted_id = converted_id.replace("--", "-")

    return converted_id


# def strip_comments(adoc_text: str) -> str:
def strip_comments(adoc_text):
    """
    This function accepts AsciiDoc source and returns a copy of it
    that is stripped of all line starting with "//".
    """

    # Split the text into lines and select only those that don't start
    # with "//"
    lines = adoc_text.splitlines()
    no_comments = [l for l in lines if not l.startswith("//")]

    # Connect the lines again, deleting empty leading lines
    return "\n".join(no_comments).lstrip()

# def write_file(converted_id: str, module_content: str) -> None:
def write_file(out_file, module_content):
    """
    This function writes the generated content into the appropriate file,
    performing necessary checks
    """

    # In Python 2, the `input` function is called `raw_input`
    if PYVERSION == 2:
        compatible_input = raw_input
    else:
        compatible_input = input

    # Check if the file exists; abort if so
    if os.path.exists(out_file):
        print('File already exists: "{}"'.format(out_file))

        # Ask the user how to proceed, loop after an unexpected answer
        decision = None

        while not decision:
            response = compatible_input("Overwrite it? [yes/no] ").lower()

            if response in ["yes", "y"]:
                print("Overwriting.")
                break
            elif response in ["no", "n"]:
                print("Preserving the older file.")
                exit(1)
            else:
                pass

    # Write the file
    with open(out_file, "w") as f:
        f.write(module_content)
    # In Python 2, the UTF-8 encoding has to be specified explicitly
    if PYVERSION == 2:
        with io.open(out_file, mode="w", encoding="utf-8") as f:
            f.write(module_content)
    else:
        with open(out_file, "w") as f:
            f.write(module_content)

    print("File successfully generated.")
    print("To include this file from an assembly, use:")
    print("include::<path>/{}[leveloffset=+1]".format(out_file))


# def create_module(title: str, doc_type: str, delete_comments: bool) -> None:
def create_module(title, doc_type, options, delete_comments):
    """
    The main function of the script that integrates the other functions
    """

    # Convert the title to ID
    converted_id = convert_title_to_id(title, doc_type, options)

    # Derive a file name from the ID and the doc type
    prefixes = {
        "assembly": "assembly_",
        "concept": "con_",
        "procedure": "proc_",
        "reference": "ref_"
    }
    filename = prefixes[doc_type] + converted_id + ".adoc"

    # Read the content of the template
    template_file = os.path.expanduser(options[doc_type + "_template"])

    # Make sure the template file exists
    if not os.path.isfile(template_file):
        print("Error: Template file not found: '{}'".format(template_file))
        exit(1)

    # In Python 2, the UTF-8 encoding has to be specified explicitly
    if PYVERSION == 2:
        with io.open(template_file, mode="r", encoding="utf-8") as f:
            template = f.read()
    else:
        with open(template_file, "r") as f:
            template = f.read()

    # Prepare the content of the new module
    module_content = Template(template).substitute(module_title=title,
                                                   module_id=converted_id,
                                                   filename=filename)

    # If the --no-comments option is selected, delete all comments
    if delete_comments:
        module_content = strip_comments(module_content)

    # Write the generated content into a file
    write_file(filename, module_content)


def main():
    """
    Main, executable procedure of the script
    """
    # Build a command-line options parser
    parser = argparse.ArgumentParser()

    parser.add_argument("--version",
                        action="version",
                        version="newdoc {}".format(NEWDOC_VERSION))
    parser.add_argument("-a", "--assembly",
                        help="Create an assembly from a given title.",
                        metavar="title",
                        nargs="+",
                        type=str)
    parser.add_argument("-c", "--concept",
                        help="Create a concept module from a given title.",
                        metavar="title",
                        nargs="+",
                        type=str)
    parser.add_argument("-p", "--procedure",
                        help="Create a procedure module from a given title.",
                        metavar="title",
                        nargs="+",
                        type=str)
    parser.add_argument("-r", "--reference",
                        help="Create a reference module from a given title.",
                        metavar="title",
                        nargs="+",
                        type=str)
    parser.add_argument("-C", "--no-comments",
                        help="Generate the file without any comments.",
                        action="store_true")

    # Doesn't do anything right now
    # parser.add_argument("-d", "--module-dir",
    #                     help="Specify the directory where to save modules.",
    #                     type=str)


    # Get commandline arguments
    args = parser.parse_args()
    options = get_config()
    
    # Transform the args object into something that can be easily iterated
    args_struct = [
        ("assembly", args.assembly),
        ("concept", args.concept),
        ("procedure", args.procedure),
        ("reference", args.reference)
    ]

    # Select all doc types for which a title has been provided
    valid_args = [a for a in args_struct if a[1]]

    # If there are no titles, print help and exit
    if not valid_args:
        parser.print_help()
    # If there are titles, create a new file for each one
    else: 
        for doc_type, title_list in valid_args:
            # Doc type options accept multiple titles to create multiple files
            for title in title_list:
                create_module(title, doc_type, options, args.no_comments)

if __name__ == "__main__":
    main()

