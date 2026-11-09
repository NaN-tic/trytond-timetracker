import unittest
from datetime import datetime, timedelta

from proteus import Model
from trytond.modules.company.tests.tools import create_company, get_company
from trytond.tests.test_tryton import drop_db
from trytond.tests.tools import activate_modules


class TestTimesheetTracking(unittest.TestCase):

    def setUp(self):
        drop_db()
        super().setUp()

    def tearDown(self):
        drop_db()
        super().tearDown()

    def test(self):
        config = activate_modules('timetracker')
        create_company(config=config)
        company = get_company(config=config)
        Party = Model.get('party.party')
        Employee = Model.get('company.employee')
        Line = Model.get('timesheet.line')
        party = Party(name='Employee')
        party.save()
        employee = Employee(party=party, company=company)
        employee.save()
        Module = Model.get('ir.module')
        project, = Module.find([('name', '=', 'project')])
        self.assertEqual(project.state, 'not activated')
        Work = Model.get('timesheet.work')
        work = Work(name='General work', company=company)
        work.save()
        start = datetime.now() - timedelta(hours=1)
        line = Line(work=work, employee=employee, start=start)
        line.save()
        line.click('finish')
        self.assertIsNotNone(line.end)
        # DateTime fields discard microseconds when stored.
        self.assertLess(
            abs(line.duration - (line.end - line.start)),
            timedelta(seconds=1))
        self.assertGreater(line.duration, timedelta(0))
