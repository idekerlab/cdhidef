#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_cdhidef
----------------------------------

Tests for `cdhidef` module.
"""

import os
import sys
import unittest
import tempfile
import shutil


from cdhidef import cdhidefcmd


class TestCdhidef(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_parse_args(self):
        myargs = ['inputarg']
        res = cdhidefcmd._parse_arguments('desc', myargs)
        self.assertEqual('inputarg', res.input)

    def test_run_hidef_no_file(self):
        temp_dir = tempfile.mkdtemp()
        try:
            tfile = os.path.join(temp_dir, 'foo')
            myargs = [tfile]
            theargs = cdhidefcmd._parse_arguments('desc', myargs)
            res = cdhidefcmd.run_hidef(tfile, theargs)
            self.assertEqual(3, res)
        finally:
            shutil.rmtree(temp_dir)

    def test_run_hidef_empty_file(self):
        temp_dir = tempfile.mkdtemp()
        try:
            tfile = os.path.join(temp_dir, 'foo')
            open(tfile, 'a').close()
            myargs = [tfile]
            theargs = cdhidefcmd._parse_arguments('desc', myargs)
            res = cdhidefcmd.run_hidef(tfile, theargs)
            self.assertEqual(4, res)
        finally:
            shutil.rmtree(temp_dir)

    def test_main_invalid_file(self):
        temp_dir = tempfile.mkdtemp()
        try:
            tfile = os.path.join(temp_dir, 'foo')
            myargs = ['prog', tfile]
            res = cdhidefcmd.main(myargs)
            self.assertEqual(3, res)
        finally:
            shutil.rmtree(temp_dir)

    def test_main_empty_file(self):
        temp_dir = tempfile.mkdtemp()
        try:
            tfile = os.path.join(temp_dir, 'foo')
            open(tfile, 'a').close()
            myargs = ['prog', tfile]
            res = cdhidefcmd.main(myargs)
            self.assertEqual(4, res)
        finally:
            shutil.rmtree(temp_dir)


if __name__ == '__main__':
    sys.exit(unittest.main())
