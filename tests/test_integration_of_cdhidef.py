#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_integration_of_cdhidef
----------------------------------

Integration tests for `cdhidef` module.
"""

import os
import sys
import unittest
import tempfile
import shutil
import json
import subprocess
import stat
from unittest.mock import MagicMock
from cdhidef import cdhidefcmd


SKIP_REASON = 'CDHIDEF_DOCKER_IMAGE, CDHIDEF_DOCKER, CDHIDEF_TMPDIR environment ' \
              'variable(s) not set to a docker image' \
              ' cannot run integration tests of hidef with Docker'


@unittest.skipUnless(os.getenv('CDHIDEF_DOCKER_IMAGE') is not None and
                     os.getenv('CDHIDEF_DOCKER') is not None and
                     os.getenv('CDHIDEF_TMPDIR') is not None, SKIP_REASON)
class TestCdhidefInDocker(unittest.TestCase):

    TEST_DIR = os.path.dirname(__file__)

    HUNDRED_NODE_DIR = os.path.join(TEST_DIR, 'data',
                                    '100node_example')

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def run_hidef_docker(self, cmdargs, temp_dir=None):
        """
        Runs hidef command as a command line process
        :param cmd_to_run: command to run as list
        :type cmd_to_run: list
        :return: (return code, standard out, standard error)
        :rtype: tuple
        """
        cmd = [os.getenv('CDHIDEF_DOCKER'), 'run', '--rm', '-v',
               temp_dir+':'+temp_dir,
               os.getenv('CDHIDEF_DOCKER_IMAGE')]
        cmd.extend(cmdargs)
        p = subprocess.Popen(cmd,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)

        out, err = p.communicate()

        return p.returncode, out, err

    def test_run_hidef_no_args(self):
        temp_dir = tempfile.mkdtemp(dir=os.getenv('CDHIDEF_TMPDIR'))
        try:
            src_input_file = os.path.join(TestCdhidefInDocker.HUNDRED_NODE_DIR, 'input.txt')
            input_file = os.path.join(temp_dir, 'input.txt')
            shutil.copyfile(src_input_file, input_file)
            ecode, out, err = self.run_hidef_docker([input_file], temp_dir=temp_dir)
            self.assertEqual(0, ecode)
            res = json.loads(out)
            self.assertEqual(2, len(res.keys()))
            self.assertEqual(3778, len(res['communityDetectionResult']))

        finally:
            shutil.rmtree(temp_dir)

    def test_run_hidef_leiden_algorithm(self):
        temp_dir = tempfile.mkdtemp(dir=os.getenv('CDHIDEF_TMPDIR'))
        try:
            src_input_file = os.path.join(TestCdhidefInDocker.HUNDRED_NODE_DIR, 'input.txt')
            input_file = os.path.join(temp_dir, 'input.txt')
            shutil.copyfile(src_input_file, input_file)
            ecode, out, err = self.run_hidef_docker([input_file,
                                                     '--alg',
                                                     'leiden'], temp_dir=temp_dir)
            self.assertEqual(0, ecode)
            res = json.loads(out)
            self.assertEqual(2, len(res.keys()))
            self.assertEqual(3778, len(res['communityDetectionResult']))
        finally:
            shutil.rmtree(temp_dir)


if __name__ == '__main__':
    sys.exit(unittest.main())
