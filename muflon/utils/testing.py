# -*- coding: utf-8 -*-

# Copyright (C) 2017 Martin Řehoř
#
# This file is part of MUFLON.
#
# MUFLON is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# MUFLON is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with MUFLON. If not, see <http://www.gnu.org/licenses/>.

"""
This module contains various utilities designed for testing of MUFLON.
"""

import pickle, os

from muflon.common.boilerplate import prepare_output_directory

class GenericPostprocessorMMS(object):
    """
    This class represents generic interface for postprocessing of the results
    obtained from benchmarks based on the Method of Manufactured Solutions.
    """
    def __init__(self, outdir=""):
        self.plots = {}
        self.results = []
        self.fixvars = []
        if outdir == "":
            self.outdir = outdir
        else:
            self.outdir = prepare_output_directory(outdir)

    def __del__(self):
        self.flush_results("results_flushed_at_destructor")

    def add_result(self, rank, result):
        if rank > 0:
            return
        self.results.append(result)

    def pop_items(self, keys):
        for r in self.results:
            for key in keys:
                r.pop(key, None)

    def register_fixed_variables(self, fixed_variables=None):
        fixed_variables = fixed_variables or ()
        assert isinstance(fixed_variables, tuple)
        assert all(len(var)==2 and isinstance(var[0], str)
                   for var in fixed_variables)
        self.fixvars.append(fixed_variables)

    def create_plots(self, rank):
        if rank > 0:
            return
        for fixed_variables in self.fixvars:
            self.plots[fixed_variables] = self._create_figure()

    def dump_to_file(self, rank, filename):
        if rank > 0:
            return
        datafile = os.path.join(self.outdir, filename)
        with open(datafile, 'wb') as handle:
            pickle.dump(self, handle, protocol=pickle.HIGHEST_PROTOCOL)

    def flush_results(self, filename):
        if not self.results:
            return
        datafile = os.path.join(self.outdir, filename)
        with open(datafile, 'wb') as handle:
            for result in self.results:
                pickle.dump(result, handle, protocol=pickle.HIGHEST_PROTOCOL)

    def read_results(self, rank, datafile):
        if rank > 0:
            return
        if self.results:
            self.results = []
        with open(datafile, 'rb') as handle:
            while True:
                try:
                    self.results.append(pickle.load(handle))
                except EOFError:
                    break

    @staticmethod
    def _create_figure():
        msg = "You need to implement a method '%s' of class '%s'." \
          % ("_create_figure", str(GenericPostprocessorMMS))
        raise NotImplementedError(msg)


def read_postprocessor(datafile):
    with open(datafile, 'rb') as handle:
        proc = pickle.load(handle)
    return proc
