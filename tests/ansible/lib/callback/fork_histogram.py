
# Monkey-patch os.fork() to produce a latency histogram on run completion.
# Requires 'hdrhsitograms' PyPI module.

from __future__ import print_function

import os
import sys
import time

import ansible.plugins.callback
import hdrh.histogram


class CallbackModule(ansible.plugins.callback.CallbackBase):
    hist = None

    def set_play_context(self, _):
        if self.hist is not None:
            return

        self.hist = hdrh.histogram.HdrHistogram(1, int(1e6*60), 3)
        self.install()

    def install(self):
        self.real_fork = os.fork
        os.fork = self.my_fork

    def my_fork(self):
        t0 = time.time()
        try:
            return self.real_fork()
        finally:
            self.hist.record_value(1e6 * (time.time() - t0))

    def playbook_on_stats(self, stats):
        print('--- Fork statistics ---')
        print('99th percentile fork latency: %.03f msec' % (
              self.hist.get_value_at_percentile(99) / 1000.0,
          ),
        )
        self.hist.output_percentile_distribution(sys.stdout, 10)
        print('--- End fork statistics ---')
        print()
