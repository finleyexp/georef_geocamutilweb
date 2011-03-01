#!/usr/bin/env python
# __BEGIN_LICENSE__
# Copyright (C) 2008-2010 United States Government as represented by
# the Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
# __END_LICENSE__

import os
import logging
import stat
from glob import glob
import shutil
import itertools

from geocamUtil.Builder import Builder

USE_SYMLINKS = True

class Installer(object):
    def __init__(self, builder=None, logger=None):
        if builder == None:
            builder = Builder()
        if logger == None:
            logger = logging
        self.builder = builder
        self.logger = logger

    @staticmethod
    def joinNoTrailingSlash(a, b):
        if b == '':
            return a
        else:
            return a + os.path.sep + b

    def dosys(self, cmd):
        self.logger.info('running:', cmd)
        ret = os.system(cmd)
        if ret != 0:
            self.logger.warning('[command exited with non-zero return value %d]' % ret)

    def getFiles(self, src, suffix=''):
        path = self.joinNoTrailingSlash(src, suffix)
        pathMode = os.stat(path)[stat.ST_MODE]
        if stat.S_ISREG(pathMode):
            return [suffix]
        elif stat.S_ISDIR(pathMode):
            return itertools.chain([suffix],
                                   *[self.getFiles(src, os.path.join(suffix, f))
                                     for f in os.listdir(path)])
        else:
            return [] # not a dir or regular file, ignore

    def installFile(self, src, dst):
        if os.path.isdir(src):
            if os.path.exists(dst):
                if not os.path.isdir(dst):
                    # replace plain file with directory
                    os.unlink(dst)
                    os.makedirs(dst)
            else:
                # make directory
                os.makedirs(dst)
        else:
            # install plain file
            if not os.path.exists(os.path.dirname(dst)):
                os.makedirs(os.path.dirname(dst))
            if USE_SYMLINKS:
                if os.path.isdir(dst):
                    dst = os.path.join(dst, os.path.basename(src))
                if os.path.lexists(dst):
                    os.unlink(dst)
                os.symlink(os.path.realpath(src), dst)
            else:
                shutil.copy(src, dst)

    def installDir0(self, src, dst):
        for f in self.getFiles(src):
            dst1 = self.joinNoTrailingSlash(dst, f)
            src1 = self.joinNoTrailingSlash(src, f)
            self.builder.applyRule(dst1, [src1],
                                   lambda: self.installFile(src1, dst1))

    def installDir(self, src, dst):
        logging.info('installDir %s %s' % (src, dst))
        self.installDir0(src, dst)

    def installDirs0(self, srcs, dst):
        logging.debug('installDirs0 srcs=%s dst=%s' % (srcs, dst))
        for src in srcs:
            self.installDir0(src, os.path.join(dst, os.path.basename(src)))

    def installDirs(self, pat, dst):
        logging.info('installDirs %s %s' % (pat, dst))
        self.installDirs0(glob(pat), dst)
