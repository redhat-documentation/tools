#!/usr/bin/python
# Vladimir Slavik, Red Hat, 2018

# Replace [discrete]\n== subheading with .subheading, including some common variations of that format.
# Usage: python fix-subheadings.py target-directory

# Automatically recurses into subdirectories and changes all *.adoc files; for recursion rules see python os.path.walk docs

# To change "[discrete] == headings" to ".headings" in all files in a target directory, go to the
# directory with the script and use ./fix-subheadings.py target-directory-path (where you replace
# target-directory-path with the path to the target directory)

from __future__ import print_function

from os.path import walk, isfile, join
from sys import argv
import re

re1 = re.compile(r"\[discrete\][ \t]*[\n\r]{1,2}== ")
re2 = re.compile(r"\[discrete\]([^\n\r]+[\n\r]{1,2})== ")
re3 = re.compile(r"\[discrete,([^\]]+)\]([^\n\r]+[\n\r]{1,2})== ")

def proc_file(filename) :
  with open(filename,"r") as f :
    lines = f.read()
  tmp = re1.sub(r".", lines)
  tmp = re2.sub(r"\1.", tmp)
  tmp = re3.sub(r"[\1]\2.", tmp)
  with open(filename, "w") as f :
    f.writelines(tmp)


def func(arg, dirname, fnames) :
  #print("dirname", dirname)
  #print("fnames", fnames)
  for fname in fnames :
    fullpath = join(dirname, fname)
    if isfile(fullpath) and fullpath.endswith(".adoc") :
      #print(fullpath)
      proc_file(fullpath)

arg = None
walk(argv[1], func, arg)
