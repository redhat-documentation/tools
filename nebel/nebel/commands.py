'''
Created on January 2, 2019

@author fbolton
'''

import os
import re
import sys
import tempfile
import shutil
import argparse
import nebel.context
import nebel.factory
import datetime
import glob

class Tasks:
    def __init__(self, context):
        self.context = context

    def _create(self, args, metadata):
        metadata['Category'] = args.CATEGORY
        metadata['ModuleID'] = args.MODULE_ID
        if args.user_story:
            metadata['UserStory'] = args.user_story
        if args.title:
            metadata['Title'] = args.title
        if args.jira:
            metadata['Jira'] = args.jira
        if args.parent_assemblies:
            metadata['ParentAssemblies'] = args.parent_assemblies
        modulefile = self.context.moduleFactory.create(metadata)
        if args.parent_assemblies:
            for assemblyfile in args.parent_assemblies.split():
                self.add_include_to_assembly(assemblyfile, modulefile)

    def create_assembly(self,args):
        metadata = {'Type':'assembly'}
        self._create(args, metadata)

    def create_procedure(self,args):
        metadata = {'Type':'procedure'}
        self._create(args, metadata)

    def create_concept(self,args):
        metadata = {'Type':'concept'}
        self._create(args, metadata)

    def create_reference(self,args):
        metadata = {'Type':'reference'}
        self._create(args, metadata)

    def add_include_to_assembly(self, assemblyfile, includedfile, leveloffset=1):
        if not os.path.exists(assemblyfile):
            print 'WARN: Referenced assembly file does not exist:' + assemblyfile
            return
        # Create temp file
        fh, abs_path = tempfile.mkstemp()
        with os.fdopen(fh, 'w') as new_file:
            with open(assemblyfile) as old_file:
                # Find the position in the file to add the include directive
                position_of_new_include = -1
                len_old_file = 0
                for k, line in enumerate(old_file):
                    len_old_file += 1
                    if line.lstrip().startswith('include::'):
                        position_of_new_include = k
                    if line.lstrip().startswith('//INCLUDES'):
                        position_of_new_include = k
                if position_of_new_include == -1:
                    # Default to end of the file
                    position_of_new_include = len_old_file - 1
                # Reset the file stream to the beginning
                old_file.seek(0)
                # Write the new file, with added include
                for k, line in enumerate(old_file):
                    new_file.write(line)
                    if k == position_of_new_include:
                        relpath = os.path.relpath(includedfile, os.path.dirname(assemblyfile))
                        new_file.write('\n')
                        new_file.write('include::' + relpath + '[leveloffset=+' + str(leveloffset) + ']\n\n')
        # Remove original file
        os.remove(assemblyfile)
        # Move new file
        shutil.move(abs_path, assemblyfile)


    def create_from(self,args):
        fromfile = args.FROM_FILE
        if not os.path.exists(fromfile):
            print 'ERROR: Cannot find file: ' + fromfile
            sys.exit()
        if fromfile.endswith('.csv'):
            self._create_from_csv(args)
            return
        elif fromfile.startswith(self.context.ASSEMBLIES_DIR)\
                and fromfile.endswith('.adoc')\
                and os.path.basename(fromfile).startswith(self.context.ASSEMBLY_PREFIX):
            self._create_from_assembly(args)
            return
        elif fromfile.endswith('.adoc'):
            self._create_from_legacy(args)
            return
        else:
            print 'ERROR: Unknown file type [' + fromfile + ']: must end either in .csv or .adoc'
            sys.exit()

    def type_of_file(self, basename):
        # ToDo: Should be more flexible at recognizing file types
        if basename.startswith(self.context.ASSEMBLY_PREFIX + '_'):
            return 'assembly'
        elif basename.startswith(self.context.PROCEDURE_PREFIX + '_'):
            return 'procedure'
        elif basename.startswith(self.context.CONCEPT_PREFIX + '_'):
            return 'concept'
        elif basename.startswith(self.context.REFERENCE_PREFIX + '_'):
            return 'reference'
        else:
            return 'module'

    def moduleid_of_file(self, basename):
        base, ext = os.path.splitext(basename)
        if base.startswith(self.context.ASSEMBLY_PREFIX + '_') or \
            base.startswith(self.context.PROCEDURE_PREFIX + '_') or \
            base.startswith(self.context.CONCEPT_PREFIX + '_') or \
            base.startswith(self.context.REFERENCE_PREFIX + '_'):
            return base.split('_', 1)[1]
        else:
            return base

    def title_to_id(self, title):
        title = title.strip()
        # Remove any character which is not a dash, underscore, alphanumeric, or whitespace
        title = re.sub(r'[^0-9a-zA-Z_\-\s]+', '', title)
        # Replace one or more contiguous whitespaces with a dash
        title = re.sub(r'\s+', '-', title)
        return title

    def _create_from_assembly(self,args):
        asfile = args.FROM_FILE
        regexp = re.compile(r'^\s*include::[\./]*modules/([^\[]+)\[[^\]]*\]')
        with open(asfile, 'r') as f:
            for line in f:
                result = regexp.search(line)
                if result is not None:
                    modulefile = result.group(1)
                    category, basename = os.path.split(modulefile)
                    type = self.type_of_file(basename)
                    if type is not None and basename.endswith('.adoc'):
                        print modulefile
                        metadata = {}
                        metadata['Type'] = type
                        metadata['Category'] = category
                        metadata['ModuleID'] = self.moduleid_of_file(basename)
                        metadata['ParentAssemblies'] = asfile
                        self.context.moduleFactory.create(metadata)


    def _create_from_legacy(self, args):
        fromfile = args.FROM_FILE
        metadata = {}
        metadata['Category'] = 'default'
        equalssigncount = 0
        with open(fromfile, 'r') as f:
            lines = f.readlines()
        indexofnextline = 0
        self._parse_from_legacy(metadata, fromfile, lines, indexofnextline, equalssigncount)

    def _parse_from_legacy(
            self,
            metadata,
            fromfilepath,
            lines,
            indexofnextline,
            equalssigncount
    ):
        # Define some enums for state machine
        REGULAR_LINES = 0
        TENTATIVE_PARSING = 1

        # Define action enums
        NO_ACTION = 0
        CREATE_SUBSECTION = 1
        CREATE_MODULE_OR_ASSEMBLY = 2
        END_CURRENT_MODULE = 3

        # Initialize Boolean state variables
        parsing_state = REGULAR_LINES
        expecting_title_line = False
        module_complete = False

        # Define regular expressions
        regexp_metadata = re.compile(r'^\s*//\s*(\w+)\s*:\s*(.*)')
        regexp_id_line1 = re.compile(r'^\s*\[\[\s*(\S+)\s*\]\]\s*$')
        regexp_id_line2 = re.compile(r'^\s*\[id\s*=\s*[\'"]\s*(\S+)\s*[\'"]\]\s*$')
        regexp_title = re.compile(r'^(=+)\s+(\S.*)')

        childmetadata = {}
        parsedcontentlines = []

        while not module_complete:
            # Check for end of file
            if indexofnextline >= len(lines):
                if ('Type' in metadata) and (metadata['Type'].lower() == 'skip'):
                    # Don't save current content
                    return ('', len(lines))
                elif 'Type' in metadata:
                    generated_file = self.context.moduleFactory.create(metadata, parsedcontentlines)
                    return (generated_file, len(lines))
                else:
                    return ('', len(lines))

            if parsing_state == REGULAR_LINES:
                line = lines[indexofnextline]
                if (regexp_metadata.search(line) is None) and (regexp_id_line1.search(line) is None) and (regexp_id_line2.search(line) is None) and (regexp_title.search(line) is None):
                    # Regular line
                    parsedcontentlines.append(line)
                    indexofnextline += 1
                else:
                    # Switch state
                    parsing_state = TENTATIVE_PARSING
                    expecting_title_line = False
                    index_of_tentative_block = indexofnextline
                    tentativecontentlines = []
            elif parsing_state == TENTATIVE_PARSING:
                line = lines[indexofnextline]
                tentativecontentlines.append(line)
                indexofnextline += 1
                # Skip blank lines
                if line.strip() == '':
                    continue
                # Parse title line
                result = regexp_title.search(line)
                if result is not None:
                    childequalssigncount = len(result.group(1))
                    title = result.group(2)
                    if 'Title' not in childmetadata:
                        childmetadata['Title'] = title
                    else:
                        childmetadata['ConvertedFromTitle'] = title
                    if ('Type' in metadata) and (metadata['Type'].lower() == 'skip'):
                        childmetadata['Type'] = 'skip'
                    action = NO_ACTION
                    # Decide how to proceed based on level of new heading
                    if childequalssigncount > equalssigncount:
                        if 'Type' not in childmetadata:
                            action = CREATE_SUBSECTION
                        else:
                            action = CREATE_MODULE_OR_ASSEMBLY
                    elif childequalssigncount == equalssigncount:
                        if ('Type' in childmetadata) and (childmetadata['Type'].lower() == 'continue'):
                            action = CREATE_SUBSECTION
                        else:
                            action = END_CURRENT_MODULE
                    else:
                        # childequalssigncount < equalssigncount
                        action = END_CURRENT_MODULE
                    # Perform action
                    if action == CREATE_SUBSECTION:
                        # It's a simple subsection, not a module or assembly
                        # Reformat heading as a simple heading (starts with .)
                        lastline = tentativecontentlines.pop()
                        lastline = '.' + lastline.replace('=', '').lstrip()
                        # Put back tentative lines
                        for tentativeline in tentativecontentlines:
                            parsedcontentlines.append(tentativeline)
                        parsedcontentlines.append(lastline)
                    elif action == CREATE_MODULE_OR_ASSEMBLY:
                        if ('ModuleID' not in childmetadata):
                            print 'ERROR: Heading ' + title + ' must have a module ID.'
                            sys.exit()
                        if ('Category' not in childmetadata):
                            childmetadata['Category'] = metadata['Category']
                        childmetadata['ConversionStatus'] = 'raw'
                        childmetadata['ConversionDate'] = str(datetime.datetime.now())
                        childmetadata['ConvertedFromFile'] = fromfilepath
                        (generated_file, indexofnextline) = self._parse_from_legacy(
                            childmetadata,
                            fromfilepath,
                            lines,
                            indexofnextline,
                            childequalssigncount
                        )
                        childmetadata = {}
                        parsedcontentlines.append('\n')
                        if generated_file:
                            parsedcontentlines.append('include::../../' + generated_file + '[leveloffset=+1]\n\n')
                    elif action == END_CURRENT_MODULE:
                        if metadata['Type'].lower() == 'skip':
                            # Don't save current content and back up to the start of the tentative block
                            return ('', index_of_tentative_block)
                        # Save the current content
                        generated_file = self.context.moduleFactory.create(metadata, parsedcontentlines)
                        return (generated_file, index_of_tentative_block)
                    # Switch state
                    parsing_state = REGULAR_LINES
                    expecting_title_line = False
                    childmetadata = {}
                    continue
                # Parse metadata line
                result = regexp_metadata.search(line)
                if (result is not None) and not expecting_title_line:
                    metadata_name = result.group(1)
                    metadata_value = result.group(2)
                    if metadata_name in self.context.allMetadataFields:
                        childmetadata[metadata_name] = metadata_value
                    #print 'Metadata: ' + metadata_name + ' = ' + metadata_value
                    continue
                # Parse ID line
                original_id = ''
                result = regexp_id_line1.search(line)
                if result is not None:
                    original_id = result.group(1)
                result = regexp_id_line2.search(line)
                if result is not None:
                    original_id = result.group(1)
                if original_id and not expecting_title_line:
                    if 'ModuleID' not in childmetadata:
                        childmetadata['ModuleID'] = original_id
                    else:
                        childmetadata['ConvertedFromID'] = original_id
                    # An ID line should be followed by a title line
                    expecting_title_line = True
                    continue
                else:
                    # Failed to match any of the tentative block line types!
                    # Abort the tentative block parsing
                    # Put back tentative lines
                    for tentativeline in tentativecontentlines:
                        parsedcontentlines.append(tentativeline)
                    # Switch state
                    parsing_state = REGULAR_LINES
                    expecting_title_line = False
                    childmetadata = {}



    def _scan_file_for_includes(self, asfile):
        includedfilelist = []
        regexp = re.compile(r'^\s*include::([^\[]+)\[[^\]]*\]')
        with open(asfile, 'r') as f:
            for line in f:
                result = regexp.search(line)
                if result is not None:
                    includedfile = result.group(1)
                    directory = os.path.dirname(asfile)
                    path_to_included_file = os.path.relpath(os.path.realpath(os.path.normpath(os.path.join(directory, includedfile))))
                    if includedfile.endswith('.adoc'):
                        includedfilelist.append(path_to_included_file)
        return includedfilelist


    def _create_from_csv(self,args):
        csvfile = args.FROM_FILE
        USING_LEVELS = False
        with open(csvfile, 'r') as filehandle:
            # First line should be the column headings
            headings = filehandle.readline().strip().replace(' ','')
            headinglist = headings.split(',')
            # Check plausibility of headinglist
            if ('Category' not in headinglist) or ('ModuleID' not in headinglist):
                print 'ERROR: CSV file does not have correct format'
                sys.exit()
            if 'Level' in headinglist:
                USING_LEVELS = True
            # Create initial copy of the generated-master.adoc file
            MASTERDOC_FILENAME = 'generated-master.adoc'
            templatefile = os.path.join(self.context.templatePath, 'master.adoc')
            shutil.copyfile(templatefile, MASTERDOC_FILENAME)
            # Initialize variables to track level nesting
            nestedfilestack = []
            nestedlevelstack = []
            currentfile = MASTERDOC_FILENAME
            currentlevel = 0
            # Read and parse the CSV file
            completefile = filehandle.read()
            lines = self.smart_split(completefile, '\n', preserveQuotes=True)
            for line in lines:
                if line.strip() != '':
                    fieldlist = self.smart_split(line.strip())
                    metadata = dict(zip(headinglist, fieldlist))
                    # Skip rows with Implement field set to 'no'
                    if ('Implement' in metadata) and (metadata['Implement'].lower() == 'no'):
                        print 'INFO: Skipping unimplemented module/assembly: ' + metadata['ModuleID']
                        continue
                    # Weed out irrelevant metadata entries
                    for field,value in metadata.items():
                        if field not in self.context.allMetadataFields:
                            del(metadata[field])
                    if metadata['Type'] == '':
                        # Assume it's an empty row (i.e. fields are empty, row is just commas)
                        if (not USING_LEVELS) and (currentlevel == 1):
                            # Pop back to level 0
                            currentfile = nestedfilestack.pop()
                            currentlevel = nestedlevelstack.pop()
                        # Skip empty row
                        continue
                    # Process modules and assemblies
                    if USING_LEVELS:
                        level = int(metadata['Level'])
                    else:
                        if (metadata['Type'] == 'assembly'):
                            # For sheets without levels, assemblies are always level 1
                            level = 1
                        else:
                            # Calculate module level, for a sheet without levels
                            level = currentlevel + 1
                    while level <= currentlevel:
                        # Dig back through the stack to find the parent of this module or assembly
                        currentfile = nestedfilestack.pop()
                        currentlevel = nestedlevelstack.pop()
                    metadata['ParentAssemblies'] = currentfile
                    newfile = self.context.moduleFactory.create(metadata)
                    self.add_include_to_assembly(currentfile, newfile, level - currentlevel)
                    if (metadata['Type'] == 'assembly'):
                        # Push the assembly onto the level stack
                        nestedfilestack.append(currentfile)
                        nestedlevelstack.append(currentlevel)
                        currentfile = newfile
                        currentlevel = level


    def smart_split(self, line, splitchar=',', preserveQuotes=False):
        list = []
        isInQuotes = False
        currfield = ''
        for ch in line:
            if not isInQuotes:
                if ch == splitchar:
                    list.append(currfield)
                    currfield = ''
                    continue
                if ch == '"':
                    isInQuotes = True
                    if not preserveQuotes:
                        continue
                currfield += ch
            else:
                if ch == '\r' or ch == '\n':
                    # Eliminate newlines from quoted fields
                    continue
                if ch == '"':
                    isInQuotes = False
                    if not preserveQuotes:
                        continue
                currfield += ch
        # Don't forget to append the last field (if any)!
        if currfield:
            list.append(currfield)
        return list


    def book(self,args):
        if self.context.ASSEMBLIES_DIR == '.' or self.context.MODULES_DIR == '.':
            print 'ERROR: book command is only usable for a standard directory layout, with defined assemblies and modules directories'
            sys.exit()
        if args.create:
            # Create book and (optionally) add categories
            self._book_create(args)
        elif args.category_list:
            # Add categories
            self._book_categories(args)
        else:
            print 'ERROR: No options specified'


    def _book_create(self,args):
        bookdir = args.BOOK_DIR
        if os.path.exists(bookdir):
            print 'ERROR: Book directory already exists: ' + bookdir
            sys.exit()
        os.mkdir(bookdir)
        os.mkdir(os.path.join(bookdir, self.context.ASSEMBLIES_DIR))
        os.mkdir(os.path.join(bookdir, self.context.MODULES_DIR))
        os.mkdir(os.path.join(bookdir, self.context.IMAGES_DIR))
        os.symlink(os.path.join('..', 'shared', 'attributes.adoc'), os.path.join(bookdir, 'attributes.adoc'))
        os.symlink(
            os.path.join('..', 'shared', 'attributes-links.adoc'),
            os.path.join(bookdir, 'attributes-links.adoc')
        )
        templatefile = os.path.join(self.context.templatePath, 'master.adoc')
        shutil.copyfile(templatefile, os.path.join(bookdir, 'master.adoc'))
        templatefile = os.path.join(self.context.templatePath, 'master-docinfo.xml')
        shutil.copyfile(templatefile, os.path.join(bookdir, 'master-docinfo.xml'))
        # Add categories (if specified)
        if args.category_list:
            self._book_categories(args)


    def _book_categories(self, args):
        bookdir = args.BOOK_DIR
        if not os.path.exists(bookdir):
            print 'ERROR: Book directory does not exist: ' + bookdir
            sys.exit()
        imagesdir = os.path.join(bookdir, self.context.IMAGES_DIR)
        modulesdir = os.path.join(bookdir, self.context.MODULES_DIR)
        assembliesdir = os.path.join(bookdir, self.context.ASSEMBLIES_DIR)
        if not os.path.exists(imagesdir):
            os.mkdir(imagesdir)
        if not os.path.exists(modulesdir):
            os.mkdir(modulesdir)
        if not os.path.exists(assembliesdir):
            os.mkdir(assembliesdir)
        categorylist = args.category_list.split(',')
        map(str.strip, categorylist)
        for category in categorylist:
            if not os.path.islink(os.path.join(imagesdir, category)):
                os.symlink(
                    os.path.join('..', '..', self.context.IMAGES_DIR, category),
                    os.path.join(imagesdir, category)
                )
            if not os.path.islink(os.path.join(modulesdir, category)):
                os.symlink(
                    os.path.join('..', '..', self.context.MODULES_DIR, category),
                    os.path.join(modulesdir, category)
                )
            if not os.path.islink(os.path.join(assembliesdir, category)):
                os.symlink(
                    os.path.join('..', '..', self.context.ASSEMBLIES_DIR, category),
                    os.path.join(assembliesdir, category)
                )


    def update(self,args):
        if (not args.fix_includes) and (not args.parent_assemblies) and (not args.fix_links) and (not args.generate_ids):
            print 'ERROR: Missing required option(s)'
            sys.exit()
        # Determine the set of categories to update
        categoryset = set()
        if args.category_list:
            categoryset = set(args.category_list.split(','))
            map(str.strip, categoryset)
        elif args.book:
            if not os.path.exists(args.book):
                print 'ERROR: ' + args.book + ' directory does not exist.'
                sys.exit()
            categoryset = self.scan_for_categories(os.path.join(args.book, self.context.MODULES_DIR))\
                          | self.scan_for_categories(os.path.join(args.book, self.context.ASSEMBLIES_DIR))
        else:
            categoryset = self.scan_for_categories(self.context.MODULES_DIR) | self.scan_for_categories(self.context.ASSEMBLIES_DIR)
        if args.attribute_files:
            attrfilelist = args.attribute_files.strip().split(',')
        else:
            attrfilelist = None
        assemblyfiles = self.scan_for_categorised_files(self.context.ASSEMBLIES_DIR, categoryset, filefilter='assembly')
        modulefiles = self.scan_for_categorised_files(self.context.MODULES_DIR, categoryset, filefilter='module')
        imagefiles = self.scan_for_categorised_files(self.context.IMAGES_DIR, categoryset)
        # Select the kind of update to implement
        if args.fix_includes:
            self._update_fix_includes(assemblyfiles, modulefiles)
        if args.fix_links:
            self._update_fix_links(assemblyfiles, modulefiles, attrfilelist)
        if args.parent_assemblies:
            self._update_parent_assemblies(assemblyfiles)
        if args.generate_ids:
            self._update_generate_ids(assemblyfiles, modulefiles)


    def scan_for_categories(self, rootdir):
        categoryset = set()
        cwd = os.getcwd()
        os.chdir(rootdir)
        for root, dirs, files in os.walk(os.curdir, followlinks=True):
            for dir in dirs:
                categoryset.add(os.path.normpath(os.path.join(root, dir)))
        os.chdir(cwd)
        # Add the empty category to the category set
        categoryset.add('')
        return categoryset


    def scan_for_categorised_files(self, rootdir, categoryset, filefilter=None):
        filelist = []
        for category in categoryset:
            categorydir = os.path.join(rootdir, category)
            if os.path.exists(categorydir):
                for entry in os.listdir(categorydir):
                    pathname = os.path.join(rootdir, category, entry)
                    if os.path.isfile(pathname):
                        if filefilter is None:
                            filelist.append(pathname)
                        elif filefilter == 'assembly' and self.type_of_file(entry) == 'assembly':
                            filelist.append(pathname)
                        elif filefilter == 'module' and self.type_of_file(entry) in ['module', 'concept', 'procedure', 'reference']:
                            filelist.append(pathname)
        return filelist


    def _update_fix_includes(self, assemblyfiles, modulefiles):
        # Create dictionaries mapping norm(filename) -> [pathname, pathname, ...]
        assemblyfiledict = {}
        for filepath in assemblyfiles:
            head, tail = os.path.split(filepath)
            normfilename = self.context.moduleFactory.normalize_filename(tail)
            if normfilename not in assemblyfiledict:
                assemblyfiledict[normfilename] = [filepath]
            else:
                assemblyfiledict[normfilename].append(filepath)
        modulefiledict = {}
        for filepath in modulefiles:
            head, tail = os.path.split(filepath)
            normfilename = self.context.moduleFactory.normalize_filename(tail)
            if normfilename not in modulefiledict:
                modulefiledict[normfilename] = [filepath]
            else:
                modulefiledict[normfilename].append(filepath)
        # Scan and update include directives in assembly files
        for assemblyfile in assemblyfiles:
            self._update_include_directives(assemblyfile, assemblyfiledict, modulefiledict)


    def _update_include_directives(self, file, assemblyfiledict, modulefiledict):
        print 'Updating include directives for file: ' + file
        regexp = re.compile(r'^\s*include::([^\[\{]+)\[([^\]]*)\]')
        dirname = os.path.dirname(file)
        # Create temp file
        fh, abs_path = tempfile.mkstemp()
        with os.fdopen(fh, 'w') as new_file:
            with open(file) as old_file:
                for line in old_file:
                    if line.lstrip().startswith('include::'):
                        #print '\t' + line.strip()
                        result = regexp.search(line)
                        if result is not None:
                            includepath = result.group(1)
                            testpath = os.path.normpath(os.path.join(dirname, includepath))
                            if not os.path.exists(testpath):
                                includedir, includefile = os.path.split(includepath)
                                normincludefile = self.context.moduleFactory.normalize_filename(includefile)
                                if self.type_of_file(normincludefile) == 'assembly':
                                    # Assembly case
                                    if normincludefile in assemblyfiledict:
                                        pathlist = assemblyfiledict[normincludefile]
                                        new_includepath = self.choose_includepath(dirname, pathlist)
                                        if new_includepath is not None:
                                            new_file.write('include::' + new_includepath + '[' + result.group(2) + ']\n')
                                            print 'Replacing: ' + includepath + ' with ' + new_includepath
                                            continue
                                else:
                                    # Module case
                                    if normincludefile in modulefiledict:
                                        pathlist = modulefiledict[normincludefile]
                                        new_includepath = self.choose_includepath(dirname, pathlist)
                                        if new_includepath is not None:
                                            new_file.write('include::' + new_includepath + '[' + result.group(2) + ']\n')
                                            print 'Replacing: ' + includepath + ' with ' + new_includepath
                                            continue
                        else:
                            print 'WARN: Unparsable include:' + line.strip()
                    new_file.write(line)
        # Remove original file
        os.remove(file)
        # Move new file
        shutil.move(abs_path, file)


    def choose_includepath(self, basedir, pathlist):
        if len(pathlist) == 1:
            return os.path.relpath(pathlist[0], basedir)
        else:
            print '\tChoose the correct path for the included file or S to skip:'
            for k, path in enumerate(pathlist):
                print '\t' + str(k) + ') ' + path
            print '\tS) Skip and leave this include unchanged'
            response = ''
            while response.strip() == '':
                response = raw_input('\tEnter selection [S]: ')
                response = response.strip()
                if (response == '') or (response.lower() == 's'):
                    # Skip
                    return None
                elif (0 <= int(response)) and (int(response) < len(pathlist)):
                    return os.path.relpath(pathlist[int(response)], basedir)
                else:
                    response = ''
            return None


    def _scan_for_parent_assemblies(self, assemblylist):
        # Create dictionary of modules included by assemblies
        assemblyincludes = {}
        for assemblyfile in assemblylist:
            assemblyincludes[assemblyfile] = self._scan_file_for_includes(assemblyfile)
        # print assemblyincludes
        # Invert dictionary
        parentassemblies = {}
        for assemblyfile in assemblyincludes:
            for modulefile in assemblyincludes[assemblyfile]:
                if modulefile not in parentassemblies:
                    parentassemblies[modulefile] = [assemblyfile]
                else:
                    parentassemblies[modulefile].append(assemblyfile)
        return parentassemblies


    def _update_parent_assemblies(self, assemblylist):
        parentassemblies = self._scan_for_parent_assemblies(assemblylist)
        # Update the ParentAssemblies metadata in each of the module files
        metadata = {}
        for modulefile in parentassemblies:
            metadata['ParentAssemblies'] = ','.join(parentassemblies[modulefile])
            self.update_metadata(modulefile, metadata)


    def _update_fix_links(self, assemblyfiles, modulefiles, attrfilelist = None):
        # Set of files whose links should be fixed
        fixfileset = set(assemblyfiles) | set(modulefiles)
        # Parse the specified attributes files
        if attrfilelist is not None:
            self.context.parse_attribute_files(attrfilelist)
        else:
            print 'ERROR: No attribute files specified'
        # Identify top-level book files to scan
        booklist = []
        for root, dirs, files in os.walk(os.curdir):
            for dir in dirs:
                # Test for existence of master.adoc file
                bookdir = os.path.normpath(os.path.join(root, dir))
                bookfile = os.path.join(bookdir, 'master.adoc')
                if os.path.exists(bookfile):
                    booklist.append(bookfile)
        # Initialize anchor ID dictionary, context stack, and legacy ID lookup
        anchorid_dict = {}
        contextstack = []
        legacyid_dict = {}
        # Process each book in the list
        for bookfile in booklist:
            booktitle = self._scan_for_title(bookfile)
            booktitle_slug = self._convert_title_to_slug(booktitle)
            #print 'Title URL slug: ' + booktitle_slug
            print 'Title: ' + booktitle
            anchorid_dict, contextstack, legacyid_dict = self._parse_file_for_anchorids(anchorid_dict, contextstack, legacyid_dict, booktitle_slug, bookfile)
            #print anchorid_dict.keys()
        #print anchorid_dict
        self.anchorid_dict = anchorid_dict
        self.legacyid_dict = legacyid_dict

        for fixfile in fixfileset:
            print 'Updating links for file: ' + fixfile
            dirname = os.path.dirname(fixfile)
            # Create temp file
            fh, abs_path = tempfile.mkstemp()
            with os.fdopen(fh, 'w') as new_file:
                with open(fixfile) as old_file:
                    for line in old_file:
                        line = self._regexp_replace_angles(line)
                        line = self._regexp_replace_xref(line)
                        new_file.write(line)
            # Remove original file
            os.remove(fixfile)
            # Move new file
            shutil.move(abs_path, fixfile)


    def _regexp_replace_angles(self, value):
        regexp = re.compile(r'<<([\w\-]+),?([^>]*)>>')
        new_value = regexp.sub(self._on_match_xref, value)
        return new_value


    def _regexp_replace_xref(self, value):
        regexp = re.compile(r'xref:([\w\-]+)\[([^]]*)\]')
        new_value = regexp.sub(self._on_match_xref, value)
        return new_value


    def _on_match_xref(self, match_obj):
        anchorid = match_obj.group(1)
        optionaltext = match_obj.group(2)
        if anchorid in self.anchorid_dict:
            new_anchorid = anchorid
        elif anchorid in self.legacyid_dict:
            new_anchorid = self.legacyid_dict[anchorid]
        else:
            print 'WARNING: link to unknown ID: ' + anchorid
            new_anchorid = anchorid
        if optionaltext:
            return '<<' + new_anchorid + ',' + optionaltext + '>>'
        else:
            return '<<' + new_anchorid + '>>'


    def _scan_for_title(self, filepath):
        if not os.path.exists(filepath):
            print 'ERROR: _scan_for_title: No such file: ' + filepath
            sys.exit()
        rawtitle = ''
        regexp = re.compile(r'^=\s+(\S.*)')
        with open(filepath, 'r') as f:
            for line in f:
                result = regexp.search(line)
                if result is not None:
                    rawtitle = result.group(1)
                    break
            if rawtitle == '':
                print 'ERROR: _scan_for_title: No title found in file: ' + filepath
                sys.exit()
        return self.context.resolve_raw_attribute_value(rawtitle)


    def _convert_title_to_slug(self, title):
        return title.strip().lower().replace(' ', '_').replace('-', '_')


    def _parse_file_for_anchorids(self, anchorid_dict, contextstack, legacyid_dict, booktitle_slug, filepath):
        # Define action enums
        NO_ACTION = 0
        ORDINARY_LINE = 1
        METADATA_LINE = 2
        ID_LINE = 3
        TITLE_LINE = 4
        CONTEXT_LINE = 5
        INCLUDE_LINE = 6
        BLANK_LINE = 7

        # Initialize Boolean state variables
        REMEMBER_TO_POP_CONTEXT = False

        # Define regular expressions
        regexp_metadata = re.compile(r'^\s*//\s*(\w+)\s*:\s*(.+)')
        regexp_id_line1 = re.compile(r'^\s*\[\[\s*(\S+)\s*\]\]\s*$')
        regexp_id_line2 = re.compile(r'^\s*\[id\s*=\s*[\'"]\s*(\S+)\s*[\'"]\]\s*$')
        regexp_title = re.compile(r'^(=+)\s+(\S.*)')
        regexp_context = re.compile(r'^:context:\s+([^\{\}]*)$')
        regexp_include = re.compile(r'^\s*include::([^\[]+)\[([^\]]*)\]')
        regexp_blank = re.compile(r'^\s*$')

        if not os.path.exists(filepath):
            print 'ERROR: _parse_file_for_anchorids: File does not exist: ' + filepath
            sys.exit()
        with open(filepath, 'r') as filehandle:
            tentative_metadata = {}
            tentative_anchor_id = ''
            for line in filehandle:
                action = NO_ACTION
                # Parse the current line
                while action == NO_ACTION:
                    result = regexp_metadata.search(line)
                    if result is not None:
                        property = result.group(1)
                        value = result.group(2)
                        action = METADATA_LINE
                        continue
                    result = regexp_id_line1.search(line)
                    if result is not None:
                        rawanchorid = result.group(1)
                        action = ID_LINE
                        continue
                    result = regexp_id_line2.search(line)
                    if result is not None:
                        rawanchorid = result.group(1).strip()
                        action = ID_LINE
                        continue
                    result = regexp_title.search(line)
                    if result is not None:
                        rawtitle = result.group(2)
                        title = self.context.resolve_raw_attribute_value(rawtitle)
                        action = TITLE_LINE
                        continue
                    result = regexp_context.search(line)
                    if result is not None:
                        newcontext = result.group(1).strip()
                        action = CONTEXT_LINE
                        continue
                    result = regexp_include.search(line)
                    if result is not None:
                        rawincludefile = result.group(1)
                        includefile = self.context.resolve_raw_attribute_value(rawincludefile)
                        action = INCLUDE_LINE
                        continue
                    result = regexp_blank.search(line)
                    if result is not None:
                        action = BLANK_LINE
                        continue
                    # Default action is ordinary line
                    action = ORDINARY_LINE
                # Take action
                if action == BLANK_LINE:
                    # It's a noop
                    pass
                elif (action == ORDINARY_LINE) and tentative_anchor_id:
                    # Define an anchor ID that is not associated with a heading
                    if tentative_anchor_id not in anchorid_dict:
                        # Initialize the sub-dictionary
                        anchorid_dict[tentative_anchor_id] = {}
                    if booktitle_slug in anchorid_dict[tentative_anchor_id]:
                        print 'WARNING: Anchor ID: ' + tentative_anchor_id + 'appears more than once in book: ' + booktitle_slug
                    else:
                        anchorid_dict[tentative_anchor_id][booktitle_slug] = { 'FilePath': filepath }
                    tentative_anchor_id = ''
                    tentative_metadata = {}
                elif action == ORDINARY_LINE:
                    # After hitting an ordinary line, preceding metadata is no longer current
                    tentative_metadata = {}
                elif action == METADATA_LINE:
                    if property in self.context.optionalMetadataFields:
                        tentative_metadata[property] = value
                elif action == ID_LINE:
                    if rawanchorid.endswith('}'):
                        if contextstack:
                            currentcontext = contextstack[-1]
                            anchorid = rawanchorid.replace('{context}', currentcontext)
                        else:
                            print 'ERROR: Found ID with embedded {context}, but no context attribute defined'
                            sys.exit()
                    else:
                        anchorid = rawanchorid
                    tentative_anchor_id = anchorid
                elif (action == TITLE_LINE) and tentative_anchor_id:
                    # Define an anchor ID that is associated with a heading
                    if tentative_anchor_id not in anchorid_dict:
                        # Initialize the sub-dictionary
                        anchorid_dict[tentative_anchor_id] = {}
                    if booktitle_slug in anchorid_dict[tentative_anchor_id]:
                        print 'WARNING: Anchor ID: ' + tentative_anchor_id + 'appears more than once in book: ' + booktitle_slug
                    else:
                        anchorid_dict[tentative_anchor_id][booktitle_slug] = { 'FilePath': filepath, 'Title': title }
                        if 'ConvertedFromID' in tentative_metadata:
                            anchorid_dict[tentative_anchor_id][booktitle_slug]['ConvertedFromID'] = tentative_metadata['ConvertedFromID']
                            legacyid_dict[tentative_metadata['ConvertedFromID']] = tentative_anchor_id
                    tentative_anchor_id = ''
                    tentative_metadata = {}
                elif (action == TITLE_LINE) and not tentative_anchor_id:
                    tentative_anchor_id = ''
                    tentative_metadata = {}
                elif action == CONTEXT_LINE:
                    if not REMEMBER_TO_POP_CONTEXT:
                        # First context definition in the current file
                        contextstack.append(newcontext)
                    else:
                        # Context already defined, overwrite current value
                        contextstack[-1] = newcontext
                    REMEMBER_TO_POP_CONTEXT = True
                elif action == INCLUDE_LINE:
                    currentdir, basename = os.path.split(filepath)
                    includefile = os.path.normpath(os.path.join(currentdir, includefile))
                    if not os.path.exists(includefile):
                        print 'ERROR: Included file does not exist: ' + includefile
                        sys.exit()
                    anchorid_dict, contextstack, legacyid_dict = self._parse_file_for_anchorids(anchorid_dict, contextstack, legacyid_dict, booktitle_slug, includefile)
                    tentative_anchor_id = ''
                    tentative_metadata = {}
        if REMEMBER_TO_POP_CONTEXT:
            contextstack.pop()
        return anchorid_dict, contextstack, legacyid_dict

    def _update_generate_ids(self, assemblyfiles, modulefiles):
        # Set of files for which IDs should be generated
        fixfileset = set(assemblyfiles) | set(modulefiles)

        # Define regular expressions
        regexp_id_line1 = re.compile(r'^\s*\[\[\s*(\S+)\s*\]\]\s*$')
        regexp_id_line2 = re.compile(r'^\s*\[id\s*=\s*[\'"]\s*(\S+)\s*[\'"]\]\s*$')
        regexp_title = re.compile(r'^(=+)\s+(\S.*)')

        for fixfile in fixfileset:
            print 'Adding missing IDs to file: ' + fixfile
            dirname, basename = os.path.split(os.path.normpath(fixfile))
            idprefix = dirname.replace(os.sep, '-').replace('_', '-') + '-' + self.moduleid_of_file(basename)
            # Create temp file
            fh, abs_path = tempfile.mkstemp()
            with os.fdopen(fh, 'w') as new_file:
                with open(fixfile) as old_file:
                    prevline = ''
                    newidlist = []
                    disambig_suffix = 1
                    for line in old_file:
                        if (regexp_title.search(line) is not None)\
                                and (regexp_id_line1.search(prevline) is None)\
                                and (regexp_id_line2.search(prevline) is None):
                            # Parse title line
                            result = regexp_title.search(line)
                            title = result.group(2)
                            # Insert module ID
                            newid = idprefix + '-' + self.title_to_id(title)
                            if newid in newidlist:
                                newid = newid + '-' + '{0:0>3}'.format(disambig_suffix)
                                disambig_suffix += 1
                            newidlist.append(newid)
                            new_file.write('[id="' + newid + '"]\n')
                        new_file.write(line)
                        prevline = line
            # Remove original file
            os.remove(fixfile)
            # Move new file
            shutil.move(abs_path, fixfile)


    def update_metadata(self, file, metadata):
        print 'Updating metadata for file: ' + file
        regexp = re.compile(r'^\s*//\s*(\w+)\s*:.*')
        # Scan file for pre-existing metadata settings
        preexisting = set()
        with open(file) as scan_file:
            for line in scan_file:
                # Detect end of metadata section
                if line.startswith('='):
                    break
                result = regexp.search(line)
                if result is not None:
                    metaname = result.group(1)
                    if metaname in self.context.optionalMetadataFields:
                        preexisting.add(metaname)
        properties2add = (set(metadata.keys()) & self.context.optionalMetadataFields) - preexisting
        properties2update = set(metadata.keys()) & self.context.optionalMetadataFields & preexisting
        # Create temp file
        fh, abs_path = tempfile.mkstemp()
        with os.fdopen(fh, 'w') as new_file:
            with open(file) as old_file:
                START_OF_METADATA = False
                END_OF_METADATA = False
                NEW_PROPERTIES_ADDED = False
                for line in old_file:
                    # Detect start of metadata section
                    if line.startswith('// Metadata'):
                        new_file.write(line)
                        START_OF_METADATA = True
                        continue
                    # Detect end of metadata section
                    if line.startswith('='):
                        END_OF_METADATA = True
                    if START_OF_METADATA and not END_OF_METADATA:
                        if not NEW_PROPERTIES_ADDED:
                            for metaname in properties2add:
                                new_file.write('// ' + metaname + ': ' + metadata[metaname] + '\n')
                            NEW_PROPERTIES_ADDED = True
                        result = regexp.search(line)
                        if result is not None:
                            metaname = result.group(1)
                            if metaname in properties2update:
                                new_file.write('// ' + metaname + ': ' + metadata[metaname] + '\n')
                                continue
                    new_file.write(line)
        # Remove original file
        os.remove(file)
        # Move new file
        shutil.move(abs_path, file)


    def mv(self, args):
        frompattern = os.path.normpath(args.FROM_FILE)
        topattern = os.path.normpath(args.TO_FILE)
        # Generate a database of parent assemblies
        categoryset = self.scan_for_categories(self.context.ASSEMBLIES_DIR)
        assemblyfiles = self.scan_for_categorised_files(self.context.ASSEMBLIES_DIR, categoryset)
        bookfiles = glob.glob('*/master.adoc')
        parentassemblies = self._scan_for_parent_assemblies(assemblyfiles + bookfiles)
        # print parentassemblies[fromfile]
        # Move each file
        if frompattern.find('{}') == -1:
            # No glob patterns => move a single file
            self._mv_single_file(parentassemblies, fromfile=frompattern, tofile=topattern)
        elif frompattern.count('{}') != 1:
            print 'ERROR: More than one glob pattern {} is not allowed in FROM_FILE'
            sys.exit()
        elif topattern.count('{}') != 1:
            print 'ERROR: TO_FILE must contain a {} substitution pattern'
            sys.exit()
        else:
            fromprefix, fromsuffix = frompattern.split('{}')
            fromprefixlen = len(fromprefix)
            fromsuffixlen = len(fromsuffix)
            fromfiles = glob.glob(frompattern.replace('{}', '*'))
            for fromfile in fromfiles:
                fromfilling = fromfile[fromprefixlen : -fromsuffixlen]
                toprefix, tosuffix = topattern.split('{}')
                tofile = toprefix + fromfilling + tosuffix
                self._mv_single_file(parentassemblies, fromfile, tofile)


    def _mv_single_file(self, parentassemblies, fromfile, tofile):
        # Perform basic sanity checks
        if not os.path.exists(fromfile):
            print 'WARN: Origin file does not exist (skipping): ' + fromfile
            return
        if os.path.exists(tofile):
            print 'WARN: File already exists at destination (skipping)' + tofile
            return
        # Make sure that the destination directory exists
        destination_dir, basename = os.path.split(tofile)
        if not os.path.exists(destination_dir):
            os.makedirs(destination_dir)
        # Move the file
        os.rename(fromfile, tofile)
        # Update the affected 'include' directives in other files
        if parentassemblies.has_key(fromfile):
            for parentassembly in parentassemblies[fromfile]:
                self._rename_included_file(parentassembly, fromfile, tofile)


    def _rename_included_file(self, file, fromfile, tofile):
        # Ignore include paths with attribute substitutions
        regexp = re.compile(r'^\s*include::([^\[\{]+)\[([^\]]*)\]')
        dirname, basename = os.path.split(file)
        # Create temp file
        fh, abs_path = tempfile.mkstemp()
        with os.fdopen(fh, 'w') as new_file:
            with open(file) as old_file:
                for line in old_file:
                    if line.lstrip().startswith('include::'):
                        result = regexp.search(line)
                        if result is not None:
                            includepath = result.group(1)
                            # Compute unique relative path, factoring out any symbolic links
                            testpath = os.path.relpath(os.path.realpath(os.path.normpath(os.path.join(dirname, includepath))))
                            if testpath == os.path.normpath(fromfile):
                                if basename == 'master.adoc':
                                    newincludepath = tofile
                                else:
                                    newincludepath = os.path.relpath(tofile, dirname)
                                new_file.write('include::' + newincludepath + '[' + result.group(2) + ']\n')
                                continue
                    new_file.write(line)
        # Remove original file
        os.remove(file)
        # Move new file
        shutil.move(abs_path, file)


def add_module_arguments(parser):
    parser.add_argument('CATEGORY', help='Category in which to store this module. Can use / as a separator to define sub-categories')
    parser.add_argument('MODULE_ID', help='Unique ID to identify this module')
    parser.add_argument('-u', '--user-story', help='Text of a user story (enclose in quotes)')
    parser.add_argument('-t', '--title', help='Title of the module (enclose in quotes)')
    parser.add_argument('-j', '--jira', help='Reference to a Jira issue related to the creation of this module')
    parser.add_argument('-p', '--parent-assemblies', help='List of assemblies that include this module, specified as a space-separated list (enclose in quotes)')


# MAIN CODE - PROGRAM STARTS HERE!
# --------------------------------

# Basic initialization
if not os.path.exists('nebel.cfg'):
  print 'WARN: No nebel.cfg file found in this directory.'
  sys.exit()
context = nebel.context.NebelContext()
context.initializeFromFile('nebel.cfg')
this_script_path = os.path.dirname(os.path.abspath(__file__))
context.templatePath = os.path.abspath(os.path.join(this_script_path, '..', 'template'))
context.moduleFactory = nebel.factory.ModuleFactory(context)
tasks = Tasks(context)

# Create the top-level parser
parser = argparse.ArgumentParser(prog='nebel')
subparsers = parser.add_subparsers()

# Create the sub-parser for the 'assembly' command
assembly_parser = subparsers.add_parser('assembly', help='Generate an assembly')
add_module_arguments(assembly_parser)
assembly_parser.set_defaults(func=tasks.create_assembly)

# Create the sub-parser for the 'procedure' command
procedure_parser = subparsers.add_parser('procedure', help='Generate a procedure module')
add_module_arguments(procedure_parser)
procedure_parser.set_defaults(func=tasks.create_procedure)

# Create the sub-parser for the 'concept' command
concept_parser = subparsers.add_parser('concept', help='Generate a concept module')
add_module_arguments(concept_parser)
concept_parser.set_defaults(func=tasks.create_concept)

# Create the sub-parser for the 'reference' command
reference_parser = subparsers.add_parser('reference', help='Generate a reference module')
add_module_arguments(reference_parser)
reference_parser.set_defaults(func=tasks.create_reference)

# Create the sub-parser for the 'create-from' command
create_parser = subparsers.add_parser('create-from', help='Create multiple {}/modules from a CSV file, an assembly file, or a legacy AsciiDoc file'.format(context.ASSEMBLIES_DIR))
create_parser.add_argument('FROM_FILE', help='Can be either a comma-separated values (CSV) file (ending with .csv), an assembly file (starting with {}/ and ending with .adoc), or a legacy AsciiDoc file (ending with .adoc)'.format(context.ASSEMBLIES_DIR))
create_parser.set_defaults(func=tasks.create_from)

# Create the sub-parser for the 'book' command
book_parser = subparsers.add_parser('book', help='Create and manage book directories')
book_parser.add_argument('BOOK_DIR', help='The book directory')
book_parser.add_argument('--create', help='Create a new book directory', action='store_true')
book_parser.add_argument('-c', '--category-list', help='Comma-separated list of categories to add to book (enclose in quotes)')
book_parser.set_defaults(func=tasks.book)

# Create the sub-parser for the 'mv' command
book_parser = subparsers.add_parser('mv', help='Move (or rename) module or assembly files. You can optionally use a single instance of braces for globbing/substituting. For example, to change a file prefix from p_ to proc_ you could enter: nebel mv p_{}.adoc proc_{}.adoc')
book_parser.add_argument('FROM_FILE', help='File origin. Optionally use {} for globbing.')
book_parser.add_argument('TO_FILE', help='File destination. Optionally use {} to substitute captured glob content')
book_parser.set_defaults(func=tasks.mv)

# Create the sub-parser for the 'update' command
update_parser = subparsers.add_parser('update', help='Update metadata in modules and assemblies')
update_parser.add_argument('--fix-includes', help='Fix erroneous include directives in assemblies', action='store_true')
update_parser.add_argument('--fix-links', help='Fix erroneous cross-reference links (NOT FULLY IMPLEMENTED)', action='store_true')
update_parser.add_argument('-p','--parent-assemblies', help='Update ParentAssemblies property in modules and assemblies', action='store_true')
update_parser.add_argument('-c', '--category-list', help='Apply update only to this comma-separated list of categories (enclose in quotes)')
update_parser.add_argument('-b', '--book', help='Apply update only to the specified book')
update_parser.add_argument('-a', '--attribute-files', help='Specify a comma-separated list of attribute files')
update_parser.add_argument('--generate-ids', help='Generate missing IDs for headings', action='store_true')
update_parser.set_defaults(func=tasks.update)


# Now, parse the args and call the relevant sub-command
args = parser.parse_args()
args.func(args)
