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
import json
from unittest.mock import MagicMock
from cdhidef import cdhidefcmd
from ndex2.cx2 import CX2Network


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
        self.assertEqual(25.0, res.maxres)
        self.assertEqual(75, res.p)
        self.assertEqual('leiden', res.alg)
        self.assertEqual('hidef_finder.py', res.hidefcmd)
        self.assertEqual('/tmp', res.tempdir)

    def test_parse_args_custom_params(self):
        myargs = ['i2',
                  '--n', '1',
                  '--k', '3',
                  '--maxres', '0.6',
                  '--p', '8',
                  '--alg', 'leiden',
                  '--hidefcmd', 'foo',
                  '--tempdir', 'yo']
        res = cdhidefcmd._parse_arguments('desc', myargs)
        self.assertEqual('i2', res.input)
        self.assertEqual(1, res.n)
        self.assertEqual(3, res.k)
        self.assertEqual(0.6, res.maxres)
        self.assertEqual(8, res.p)
        self.assertEqual('leiden', res.alg)
        self.assertEqual('foo', res.hidefcmd)
        self.assertEqual('yo', res.tempdir)

    def test_build_optional_arguments_with_n(self):
        myargs = ['i2',
                  '--n', '1',
                  '--k', '3',
                  '--maxres', '0.6',
                  '--p', '8',
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

        self.assertEqual('--p', optargs[6])
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
        self.assertEqual('25.0', optargs[3])

        self.assertEqual('--p', optargs[4])
        self.assertEqual('75', optargs[5])

        self.assertEqual('--alg', optargs[6])
        self.assertEqual('leiden', optargs[7])

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

            self.assertTrue("'--skipgml', "
                            "'--k', '5', "
                            "'--maxres', "
                            "'25.0', '--p', '75', "
                            "'--alg', 'leiden'" in err_data)

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
                      '--p', '8',
                      '--alg', 'leiden',
                      '--hidefcmd', fakecmd,
                      '--tempdir', temp_dir]
            theargs = cdhidefcmd._parse_arguments('desc', myargs)

            res = cdhidefcmd.run_hidef(theargs, out_stream=f_out,
                                       err_stream=f_err)

            err_data = f_err.getvalue()

            self.assertTrue("'--skipgml', '--n', '1', "
                            "'--k', '3', "
                            "'--maxres', "
                            "'0.6', '--p', '8', "
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

    def test_convertresult_flag_set_with_nodes_file(self):
        f_out = io.StringIO()
        f_err = io.StringIO()
        input_file = os.path.join(TestCdhidef.HUNDRED_NODE_DIR, 'x.nodes')
        myargs = [input_file, '--convertresult']
        theargs = cdhidefcmd._parse_arguments('desc', myargs)

        res = cdhidefcmd.run_hidef(theargs, out_stream=f_out,
                                   err_stream=f_err)

        err_data = f_err.getvalue()

        out_data = f_out.getvalue()
        self.assertEqual(4087, len(out_data))
        heir_res = json.loads(out_data)
        with open(os.path.join(TestCdhidef.HUNDRED_NODE_DIR, 'x.expectedresult'), 'r') as f:
            expected_heir = json.load(f)
        self.assertEqual(expected_heir, heir_res)
        self.assertEqual('', err_data)
        self.assertEqual(0, res)

    def test_convertresult_flag_set_with_edges_file(self):
        f_out = io.StringIO()
        f_err = io.StringIO()
        input_file = os.path.join(TestCdhidef.HUNDRED_NODE_DIR, 'x.edges')
        myargs = [input_file, '--convertresult']
        theargs = cdhidefcmd._parse_arguments('desc', myargs)

        res = cdhidefcmd.run_hidef(theargs, out_stream=f_out,
                                   err_stream=f_err)

        err_data = f_err.getvalue()

        out_data = f_out.getvalue()
        self.assertEqual(4087, len(out_data))
        heir_res = json.loads(out_data)
        with open(os.path.join(TestCdhidef.HUNDRED_NODE_DIR, 'x.expectedresult'), 'r') as f:
            expected_heir = json.load(f)
        self.assertEqual(expected_heir, heir_res)
        self.assertEqual('', err_data)
        self.assertEqual(0, res)

    def test_convertresult_flag_set_with_invalid_suffix_file(self):
        f_out = io.StringIO()
        f_err = io.StringIO()
        input_file = os.path.join(TestCdhidef.HUNDRED_NODE_DIR, 'x.expectedresult')
        myargs = [input_file, '--convertresult']
        theargs = cdhidefcmd._parse_arguments('desc', myargs)

        res = cdhidefcmd.run_hidef(theargs, out_stream=f_out,
                                   err_stream=f_err)

        err_data = f_err.getvalue()

        out_data = f_out.getvalue()
        self.assertEqual(0, len(out_data))

        self.assertTrue('--convertresult expects input to be ' in err_data)
        self.assertEqual(6, res)

    def test_convertresult_flag_set_with_edges_file_missing(self):
        temp_dir = tempfile.mkdtemp()
        try:
            f_out = io.StringIO()
            f_err = io.StringIO()
            shutil.copy(os.path.join(TestCdhidef.HUNDRED_NODE_DIR, 'x.nodes'),
                        os.path.join(temp_dir, 'x.nodes'))
            input_file = os.path.join(temp_dir, 'x.nodes')
            myargs = [input_file, '--convertresult']
            theargs = cdhidefcmd._parse_arguments('desc', myargs)

            res = cdhidefcmd.run_hidef(theargs, out_stream=f_out,
                                       err_stream=f_err)

            err_data = f_err.getvalue()

            out_data = f_out.getvalue()
            self.assertEqual(3540, len(out_data))

            self.assertTrue('No such file' in err_data)
            self.assertEqual(5, res)
        finally:
            shutil.rmtree(temp_dir)

    def test_is_file_cx2_when_given_edgelist(self):
        temp_dir = tempfile.mkdtemp()
        try:
            input_file = os.path.join(temp_dir, 'test_input')
            shutil.copy(os.path.join(TestCdhidef.HUNDRED_NODE_DIR,
                                     'input.txt'), input_file)
            self.assertFalse(cdhidefcmd.is_file_cx2(input_file))
        finally:
            shutil.rmtree(temp_dir)

    def test_is_file_cx2_when_given_cx2_with_empty_lines(self):
        temp_dir = tempfile.mkdtemp()
        try:
            input_file = os.path.join(temp_dir, 'test_input.cx2')
            with open(input_file, 'w') as f:
                f.write(' \n\n\t\n[{"CXVersion": "2.0", "hasFragments": false},'
                        '{"metaData": [{"elementCount": 1, '
                        '"name": "attributeDeclarations"}, '
                        '{"elementCount": 3, "name": "nodes"}, '
                        '{"elementCount": 1, "name": "edges"}]}, '
                        '{"attributeDeclarations": '
                        '[{"nodes": {"size": {"d": "integer"}}, '
                        '"edges": {"weight": {"d": "double"}}}]}, '
                        '{"nodes": [{"id": 1, "v": {"size": 5}}, '
                        '{"id": 2, "v": {"size": 6}}, {"id": 3, "v": {"size": 7}}]}, '
                        '{"edges": [{"id": 0, "s": 2, "t": 3, "v": {"weight": 0.9}}]}, '
                        '{"status": [{"error": "", "success": true}]}]')

            self.assertTrue(cdhidefcmd.is_file_cx2(input_file))
        finally:
            shutil.rmtree(temp_dir)

    def test_is_file_cx2_when_given_valid_cx2(self):
        temp_dir = tempfile.mkdtemp()
        try:
            input_file = os.path.join(temp_dir, 'test_input.cx2')
            with open(input_file, 'w') as f:
                f.write('[{"CXVersion": "2.0", "hasFragments": false},'
                        '{"metaData": [{"elementCount": 1, '
                        '"name": "attributeDeclarations"}, '
                        '{"elementCount": 3, "name": "nodes"}, '
                        '{"elementCount": 1, "name": "edges"}]}, '
                        '{"attributeDeclarations": '
                        '[{"nodes": {"size": {"d": "integer"}}, '
                        '"edges": {"weight": {"d": "double"}}}]}, '
                        '{"nodes": [{"id": 1, "v": {"size": 5}}, '
                        '{"id": 2, "v": {"size": 6}}, {"id": 3, "v": {"size": 7}}]}, '
                        '{"edges": [{"id": 0, "s": 2, "t": 3, "v": {"weight": 0.9}}]}, '
                        '{"status": [{"error": "", "success": true}]}]')

            self.assertTrue(cdhidefcmd.is_file_cx2(input_file))
        finally:
            shutil.rmtree(temp_dir)

    def test_get_cx2_network(self):
        net_cx = cdhidefcmd.get_cx2_network(os.path.join(TestCdhidef.HUNDRED_NODE_DIR,
                                                         'input.cx2'))
        self.assertEqual('103node example', net_cx.get_name())
        self.assertEqual(103, len(net_cx.get_nodes()))

    def test_create_edgelist_from_cx2_network(self):
        temp_dir = tempfile.mkdtemp()
        try:
            net_cx = cdhidefcmd.get_cx2_network(os.path.join(TestCdhidef.HUNDRED_NODE_DIR,
                                                             'input.cx2'))

            edge_tuple_set = set()
            for edge_id, edge_obj in net_cx.get_edges().items():
                print(edge_obj)
                edge_tuple_set.add((edge_obj['s'], edge_obj['t']))
            print(edge_tuple_set)

            edgelist = os.path.join(temp_dir, 'edgelist.txt')
            cdhidefcmd.create_edgelist_from_cx2_network(net_cx, edgelist)

            with open(edgelist, 'r') as f:
                for line in f:
                    row = line.rstrip().split('\t')
                    self.assertTrue((int(row[0]), int(row[1])) in edge_tuple_set, row)

                print('xxxxxxxxxxx\n\n\n\n\n\n')
                print(f.read())
                print('\n\n\n\n\n')
        finally:
            shutil.rmtree(temp_dir)


    """
    # keeping around cause it is nice to have
    def _create_100node_cx2(self):
        with open(os.path.join(TestCdhidef.HUNDRED_NODE_DIR,
                                     'input.txt'), 'r') as f:
            net_cx = CX2Network()
            net_attrs = net_cx.get_network_attributes()
            net_attrs['name'] = '103node example'
            net_attrs['description'] = '103node example CX2 network'
            node_set = set()
            for line in f:
                row = line.split('\t')
                src_node_id = int(row[0])
                target_node_id = int(row[1])
                if src_node_id not in node_set:
                    net_cx.add_node(node_id=src_node_id,
                                    attributes={'name': 'Node ' +
                                                        str(src_node_id)})
                    node_set.add(src_node_id)
                if target_node_id not in node_set:
                    net_cx.add_node(node_id=target_node_id,
                                    attributes={'name': 'Node ' +
                                                        str(target_node_id)})
                    node_set.add(target_node_id)
                net_cx.add_edge(source=src_node_id, target=target_node_id,
                                attributes={'interaction': 'interacts'})
        with open(os.path.join(TestCdhidef.HUNDRED_NODE_DIR,
                               'input.cx2'), 'w') as f:
            json.dump(net_cx.to_cx2(), f, indent=2)
    """