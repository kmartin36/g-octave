#!/usr/bin/env python
# -*- coding: utf-8 -*-

__all__ = ['Ebuild']

from config import Config
conf = Config()

from description import *
from description_tree import *
from exception import EbuildException

import os
import portage
import re
import shutil

class Ebuild:
    
    def __init__(self, pkg_atom, force=False):
        
        self.__force = force
        self.__dbtree = DescriptionTree()
        
        atom = re_pkg_atom.match(pkg_atom)
        if atom == None:
            self.pkgname = pkg_atom
            self.version = self.__dbtree.latest_version(self.pkgname)
        else:
            self.pkgname = atom.group(1)
            self.version = atom.group(2)
        
        self.__desc = self.__dbtree['%s-%s' % (self.pkgname, self.version)]
        
        if self.__desc == None:
            raise EbuildException('Package not found: %s' % pkg_atom)
        

    def description(self):
        
        return self.__desc


    def create(self):
        
        ebuild_path = os.path.join(conf.overlay, 'g-octave', self.pkgname)
        ebuild_file = os.path.join(ebuild_path, '%s-%s.ebuild' % (self.pkgname, self.version))
        
        my_atom = '=g-octave/%s-%s' % (self.pkgname, self.version)
        
        if os.path.exists(ebuild_file) and not self.__force:
            return my_atom
        
        if not os.path.exists(ebuild_path):
            os.makedirs(ebuild_path, 0755)
        
        ebuild = """\
# Copyright 1999-2009 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
# This ebuild was generated by g-octave

EAPI="2"

inherit octave-forge%(eutils)s

DESCRIPTION="%(description)s"
HOMEPAGE="%(url)s"
SRC_URI="mirror://sourceforge/octave/${OCT_P}.tar.gz"

LICENSE="|| ( GPL-2 GPL-3 LGPL BSD GFDL )"
SLOT="0"
KEYWORDS="%(keywords)s"
IUSE=""

DEPEND="%(depend)s"
RDEPEND="${DEPEND}
\t%(rdepend)s"
"""
        
        description = self.__desc.description > 70 and \
            self.__desc.description[:70]+'...' or self.__desc.description
        
        vars = {
            'eutils': '',
            'description': description,
            'url': self.__desc.url,
            'keywords': portage.settings['ACCEPT_KEYWORDS'],
            'depend': '',
            'rdepend': '',
        }
        
        vars['depend']   = self.__depends(self.__desc.buildrequires)
        
        systemrequirements = self.__depends(self.__desc.systemrequirements)
        if systemrequirements != '':
            vars['depend']  += "\n\t"+systemrequirements
        
        vars['rdepend']  = self.__depends(self.__desc.depends)
        
        patches = self.__search_patches()
        
        if len(patches) > 0:
            
            # WOW, we have patches :(
            
            patchesdir = os.path.join(conf.db, 'patches')
            filesdir = os.path.join(conf.overlay, 'g-octave', self.pkgname, 'files')
            if not os.path.exists(filesdir):
                os.makedirs(filesdir, 0755)
            
            patch_string = ''
            for patch in patches:
                patch_string += "\n\tepatch \"${FILESDIR}/%s\"" % patch
                shutil.copy2(os.path.join(patchesdir, patch), filesdir)
            
            ebuild += "\nsrc_prepare() {%s\n}\n" % patch_string
            vars['eutils'] = ' eutils'
            
        fp = open(ebuild_file, 'w', 0644)
        fp.write(ebuild % vars)
        fp.close()
        
        portage.doebuild(
            ebuild_file,
            "manifest",
            portage.root,
            portage.config(clone=portage.settings),
            tree="porttree"
        )
        
        self.__resolve_dependencies()
        
        return my_atom
        
    
    def __depends(self, mylist):
        
        if mylist != None:
            return "\n\t".join(mylist)
        
        return ''


    def __search_patches(self):
        
        tmp = []
        
        for patch in os.listdir(conf.db+'/patches'):
            if re.match(r'^([0-9]{3})_%s-%s' % (self.pkgname, self.version), patch):
                tmp.append(patch)
        
        tmp.sort()
        
        return tmp
        


    def __resolve_dependencies(self):
        
        to_install = []
        
        for pkg, comp, version in self.__desc.self_depends:
            
            # no version required, get the latest available
            if version == None:
                to_install.append('%s-%s' % (pkg, self.__dbtree.latest_version(pkg)))
                continue
            
            # here we need to calculate the better version to install
            versions = self.__dbtree.package_versions(pkg)
            
            allowed_versions = []
            
            for _version in versions:
                _tp_version = tuple(_version.split('.'))
                tp_version = tuple(version.split('.'))
                
                if eval('%s %s %s' % (_tp_version, comp, tp_version)):
                    allowed_versions.append(_version)
                
            to_install.append('%s-%s' % (pkg, self.__dbtree.version_compare(allowed_versions)))
        
            if len(to_install) == 0:
                raise EbuildException('Can\'t resolve a dependency: %s' % pkg)
        
        # creating the ebuilds for the dependencies, recursivelly
        for ebuild in to_install:
            Ebuild(ebuild).create()


if __name__ == '__main__':
    a = Ebuild('vrml', True)
    a.create()
