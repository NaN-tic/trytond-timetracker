# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.pool import Pool
from . import work
from . import line


def register():
    Pool.register(
        work.Work,
        line.Line,
        work.Employee,
        work.StartWorkChooseAction,
        module='timetracker', type_='model')
    Pool.register(
        work.StartWork,
        module='timetracker', type_='wizard')
