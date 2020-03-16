'''
Created on January 2, 2019

@author fbolton
'''

import re
import ConfigParser


class NebelContext:
    def __init__(self):
        self.mandatoryMetadataFields = {
            'Type',
            'Category',
            'ModuleID'
        }
        self.optionalMetadataFields = {
            'ParentAssemblies',
            'UserStory',
            'VerifiedInVersion',
            'QuickstartID',
            'Jira',
            'Title',
            'IncludeFiles',
            'ConversionStatus',
            'ConversionDate',
            'ConvertedFromFile',
            'ConvertedFromID',
            'ConvertedFromTitle',
            'Level'
        }
        self.allMetadataFields = self.mandatoryMetadataFields | self.optionalMetadataFields
        self.templatePath = ''
        self.moduleFactory = None
        self.attributeDict = {}
        self.bookUrlAttributes = {}
        self.ASSEMBLIES_DIR = 'assemblies'
        self.MODULES_DIR = 'modules'
        self.IMAGES_DIR = 'images'
        self.ASSEMBLY_PREFIX = 'as'
        self.PROCEDURE_PREFIX = 'p'
        self.CONCEPT_PREFIX = 'c'
        self.REFERENCE_PREFIX = 'r'

    def initializeFromFile(self, configfile):
        # print 'Initializing from file: ' + configfile
        config = ConfigParser.RawConfigParser(
            {'dir.assemblies': self.ASSEMBLIES_DIR,
             'dir.modules': self.MODULES_DIR,
             'dir.images': self.IMAGES_DIR,
             'prefix.assembly': self.ASSEMBLY_PREFIX,
             'prefix.procedure': self.PROCEDURE_PREFIX,
             'prefix.concept': self.CONCEPT_PREFIX,
             'prefix.reference': self.REFERENCE_PREFIX}
        )
        config.read(configfile)
        if config.has_section('Nebel'):
            self.ASSEMBLIES_DIR   = config.get('Nebel', 'dir.assemblies')
            self.MODULES_DIR      = config.get('Nebel', 'dir.modules')
            self.IMAGES_DIR       = config.get('Nebel', 'dir.images')
            self.ASSEMBLY_PREFIX  = config.get('Nebel', 'prefix.assembly')
            self.PROCEDURE_PREFIX = config.get('Nebel', 'prefix.procedure')
            self.CONCEPT_PREFIX   = config.get('Nebel', 'prefix.concept')
            self.REFERENCE_PREFIX = config.get('Nebel', 'prefix.reference')

    def parse_attribute_files(self, filelist):
        regexp = re.compile(r'^:([\w\-]+):\s+(.*)')
        for file in filelist:
            with open(file, 'r') as f:
                for line in f:
                    result = regexp.search(line)
                    if result is not None:
                        name = result.group(1)
                        value = result.group(2).strip()
                        self.attributeDict[name] = [value, None]
        for name in self.attributeDict:
            self.attributeDict[name][1] = self.resolve_raw_attribute_value(self.attributeDict[name][0])
        #for (name,duple) in self.attributeDict.items():
        #    print name + ': ' + duple[0] + ', ' + duple[1]
        self.scan_attributes_for_book_urls()
        # print self.bookUrlAttributes


    def resolve_raw_attribute_value(self, value):
        regexp = re.compile(r'\{([\w\-]+)\}')
        new_value = regexp.sub(self.replace_matching_attribute, value)
        return new_value


    def replace_matching_attribute(self, match_obj):
        name = match_obj.group(1)
        duple = self.attributeDict[name]
        if duple[1] is None:
            duple[1] = self.resolve_raw_attribute_value(duple[0])
        return duple[1]


    def scan_attributes_for_book_urls(self):
        regexp = re.compile(r'https://access.redhat.com/documentation/en-us/([^/]+)/([^/]+)/html-single/([^/]+)/?')
        for name in self.attributeDict:
            resolved_value = self.attributeDict[name][1]
            result = regexp.search(resolved_value)
            if result is not None:
                productpkg = result.group(1)
                version = result.group(2)
                bookslug = result.group(3)
                if productpkg not in self.bookUrlAttributes:
                    self.bookUrlAttributes[productpkg] = {}
                self.bookUrlAttributes[productpkg][bookslug] = name
