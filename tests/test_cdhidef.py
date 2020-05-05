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
import io
import stat
from unittest.mock import MagicMock
from cdhidef import cdhidefcmd


def write_fake_hidef(fakecmd, stdout, stderr, srcdatadir,
                     exitcode):
    """Fake hidef command script
    """
    f = open(fakecmd, 'w')
    f.write('#!/usr/bin/env python\n\n')
    f.write('import sys\n')
    f.write('import os\n')
    f.write('import shutil\n')
    f.write('import argparse\n\n')
    f.write('parser = argparse.ArgumentParser()\n')
    f.write('parser.add_argument(\'--o\')\n')
    f.write('theargs = parser.parse_known_args(sys.argv[1:])\n')
    f.write('sys.stdout.write(str(theargs) + \':::' +
            stdout + '\')\n')
    f.write('sys.stderr.write(\'' + stderr + '\')\n')

    f.write('try:\n')
    nodes_filename = cdhidefcmd.X_PREFIX + '.nodes'
    src_nodes_file = os.path.join(srcdatadir, nodes_filename)

    f.write('    shutil.copy(\'' + src_nodes_file +
            '\', theargs[0].o + \'.nodes\')\n')
    f.write('except Exception as e:\n')
    f.write('    sys.stderr.write(str(e))\n')

    f.write('try:\n')
    edges_filename = cdhidefcmd.X_PREFIX + '.edges'
    src_edges_file = os.path.join(srcdatadir, edges_filename)

    f.write('    shutil.copy(\'' + src_edges_file +
            '\', theargs[0].o + \'.edges\')\n')
    f.write('except Exception as e:\n')
    f.write('    sys.stderr.write(str(e))\n')
    f.write('sys.exit(' + str(exitcode) + ')\n')
    f.flush()
    f.close()
    os.chmod(fakecmd, stat.S_IRWXU)


class TestCdhidef(unittest.TestCase):

    TEST_DIR = os.path.dirname(__file__)

    HUNDRED_NODE_DIR = os.path.join(TEST_DIR, 'data',
                                    '100node_example')

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_parse_args_all_defaults(self):
        myargs = ['inputarg']
        res = cdhidefcmd._parse_arguments('desc', myargs)
        self.assertEqual('inputarg', res.input)
        self.assertEqual(None, res.n)
        self.assertEqual(5, res.k)
        self.assertEqual(50.0, res.maxres)
        self.assertEqual(75, res.ct)
        self.assertEqual('louvain', res.alg)
        self.assertEqual('hidef_finder.py', res.hidefcmd)
        self.assertEqual('/tmp', res.tempdir)

    def test_parse_args_custom_params(self):
        myargs = ['i2',
                  '--n', '1',
                  '--k', '3',
                  '--maxres', '0.6',
                  '--ct', '8',
                  '--alg', 'leiden',
                  '--hidefcmd', 'foo',
                  '--tempdir', 'yo']
        res = cdhidefcmd._parse_arguments('desc', myargs)
        self.assertEqual('i2', res.input)
        self.assertEqual(1, res.n)
        self.assertEqual(3, res.k)
        self.assertEqual(0.6, res.maxres)
        self.assertEqual(8, res.ct)
        self.assertEqual('leiden', res.alg)
        self.assertEqual('foo', res.hidefcmd)
        self.assertEqual('yo', res.tempdir)

    def test_build_optional_arguments_with_n(self):
        myargs = ['i2',
                  '--n', '1',
                  '--k', '3',
                  '--maxres', '0.6',
                  '--ct', '8',
                  '--alg', 'leiden',
                  '--hidefcmd', 'foo',
                  '--tempdir', 'yo']
        res = cdhidefcmd._parse_arguments('desc', myargs)
        optargs = cdhidefcmd.build_optional_arguments(res)

        self.assertEqual('--n', optargs[0])
        self.assertEqual('1', optargs[1])

        self.assertEqual('--k', optargs[2])
        self.assertEqual('3', optargs[3])

        self.assertEqual('--maxres', optargs[4])
        self.assertEqual('0.6', optargs[5])

        self.assertEqual('--ct', optargs[6])
        self.assertEqual('8', optargs[7])

        self.assertEqual('--alg', optargs[8])
        self.assertEqual('leiden', optargs[9])

    def test_build_optional_arguments(self):
        myargs = ['i2']
        res = cdhidefcmd._parse_arguments('desc', myargs)
        optargs = cdhidefcmd.build_optional_arguments(res)

        self.assertEqual('--k', optargs[0])
        self.assertEqual('5', optargs[1])

        self.assertEqual('--maxres', optargs[2])
        self.assertEqual('50.0', optargs[3])

        self.assertEqual('--ct', optargs[4])
        self.assertEqual('75', optargs[5])

        self.assertEqual('--alg', optargs[6])
        self.assertEqual('louvain', optargs[7])

    def test_run_hidef_no_file(self):
        temp_dir = tempfile.mkdtemp()
        try:
            tfile = os.path.join(temp_dir, 'foo')
            myargs = [tfile]
            f_out = io.StringIO()
            f_err = io.StringIO()
            theargs = cdhidefcmd._parse_arguments('desc', myargs)
            res = cdhidefcmd.run_hidef(theargs, out_stream=f_out,
                                       err_stream=f_err)
            self.assertEqual(3, res)
            self.assertEqual(tfile + ' is not a file',
                             f_err.getvalue())
            self.assertEqual('', f_out.getvalue())
        finally:
            shutil.rmtree(temp_dir)

    def test_run_hidef_empty_file(self):
        temp_dir = tempfile.mkdtemp()
        try:
            tfile = os.path.join(temp_dir, 'foo')
            open(tfile, 'a').close()
            myargs = [tfile]
            f_out = io.StringIO()
            f_err = io.StringIO()
            theargs = cdhidefcmd._parse_arguments('desc', myargs)
            res = cdhidefcmd.run_hidef(theargs, out_stream=f_out,
                                       err_stream=f_err)
            self.assertEqual(4, res)
            self.assertEqual(tfile + ' is an empty file',
                             f_err.getvalue())
            self.assertEqual('', f_out.getvalue())
        finally:
            shutil.rmtree(temp_dir)

    def test_run_hidef_success(self):
        temp_dir = tempfile.mkdtemp()
        try:
            input_file = os.path.join(TestCdhidef.HUNDRED_NODE_DIR,
                                      'input.txt')

            f_out = io.StringIO()
            f_err = io.StringIO()
            fakecmd = os.path.join(temp_dir, 'foo.py')
            write_fake_hidef(fakecmd, 'stdout',
                             'stderr',
                             TestCdhidef.HUNDRED_NODE_DIR, 0)
            myargs = [input_file, '--tempdir', temp_dir,
                      '--hidefcmd', fakecmd]
            theargs = cdhidefcmd._parse_arguments('desc', myargs)

            res = cdhidefcmd.run_hidef(theargs, out_stream=f_out,
                                       err_stream=f_err)

            err_data = f_err.getvalue()

            self.assertTrue("'--skipclug', '--skipgml', "
                            "'--k', '5', "
                            "'--maxres', "
                            "'50.0', '--ct', '75', "
                            "'--alg', 'louvain'" in err_data)

            out_data = f_out.getvalue()
            self.assertEqual(4087, len(out_data))
            self.assertEqual(0, res)
        finally:
            shutil.rmtree(temp_dir)

    def test_run_hidef_success_altparams(self):
        temp_dir = tempfile.mkdtemp()
        try:
            input_file = os.path.join(TestCdhidef.HUNDRED_NODE_DIR,
                                      'input.txt')

            f_out = io.StringIO()
            f_err = io.StringIO()
            fakecmd = os.path.join(temp_dir, 'foo.py')
            write_fake_hidef(fakecmd, 'stdout',
                             'stderr',
                             TestCdhidef.HUNDRED_NODE_DIR, 0)
            myargs = [input_file,
                      '--n', '1',
                      '--k', '3',
                      '--maxres', '0.6',
                      '--ct', '8',
                      '--alg', 'leiden',
                      '--hidefcmd', fakecmd,
                      '--tempdir', temp_dir]
            theargs = cdhidefcmd._parse_arguments('desc', myargs)

            res = cdhidefcmd.run_hidef(theargs, out_stream=f_out,
                                       err_stream=f_err)

            err_data = f_err.getvalue()
            self.assertTrue("'--skipclug', '--skipgml', '--n', '1', "
                            "'--k', '3', "
                            "'--maxres', "
                            "'0.6', '--ct', '8', "
                            "'--alg', 'leiden'" in err_data)

            out_data = f_out.getvalue()
            self.assertEqual(4087, len(out_data))
            self.assertEqual(0, res)
        finally:
            shutil.rmtree(temp_dir)

    def test_run_hidef_error(self):
        temp_dir = tempfile.mkdtemp()
        try:
            input_file = os.path.join(TestCdhidef.HUNDRED_NODE_DIR,
                                      'input.txt')

            f_out = io.StringIO()
            f_err = io.StringIO()
            fakecmd = os.path.join(temp_dir, 'foo.py')
            write_fake_hidef(fakecmd, 'stdout',
                             'stderr',
                             TestCdhidef.HUNDRED_NODE_DIR, 1)
            myargs = [input_file, '--tempdir', temp_dir,
                      '--hidefcmd', fakecmd]
            theargs = cdhidefcmd._parse_arguments('desc', myargs)

            res = cdhidefcmd.run_hidef(theargs, out_stream=f_out,
                                       err_stream=f_err)

            err_data = f_err.getvalue()

            self.assertTrue('Command failed with '
                            'non-zero exit code: 1 : ' in err_data)
            out_data = f_out.getvalue()
            self.assertEqual(0, len(out_data))
            self.assertEqual(1, res)
        finally:
            shutil.rmtree(temp_dir)

    def test_run_no_files_from_hidef(self):
        temp_dir = tempfile.mkdtemp()
        try:
            input_file = os.path.join(TestCdhidef.HUNDRED_NODE_DIR,
                                      'input.txt')

            f_out = io.StringIO()
            f_err = io.StringIO()
            fakecmd = os.path.join(temp_dir, 'foo.py')
            write_fake_hidef(fakecmd, 'stdout',
                             'stderr',
                             temp_dir, 0)
            myargs = [input_file, '--tempdir', temp_dir,
                      '--hidefcmd', fakecmd]
            theargs = cdhidefcmd._parse_arguments('desc', myargs)

            res = cdhidefcmd.run_hidef(theargs, out_stream=f_out,
                                       err_stream=f_err)

            err_data = f_err.getvalue()

            out_data = f_out.getvalue()
            self.assertEqual(0, len(out_data))
            self.assertTrue('Output from cmd: ' in err_data)
            self.assertEqual(5, res)
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

    def test_createtmpdir(self):
        temp_dir = tempfile.mkdtemp()
        try:
            params = MagicMock()
            params.tempdir = temp_dir
            foo = cdhidefcmd.create_tmpdir(params)
            self.assertTrue(os.path.isdir(foo))
            self.assertEqual(temp_dir, os.path.dirname(foo))
        finally:
            shutil.rmtree(temp_dir)

    def test_convert_hidef_output_to_cdaps_with_hundred(self):
        f_out = io.StringIO()
        res = cdhidefcmd.convert_hidef_output_to_cdaps(f_out,
                                                       TestCdhidef.HUNDRED_NODE_DIR)
        self.assertEqual(None, res)
        self.assertEqual(4087, len(f_out.getvalue()))




if __name__ == '__main__':
    sys.exit(unittest.main())
