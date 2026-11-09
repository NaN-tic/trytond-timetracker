import unittest
from datetime import timedelta

from proteus import Model
from trytond.modules.company.tests.tools import create_company, get_company
from trytond.tests.test_tryton import drop_db
from trytond.tests.tools import activate_modules


class TestProjectTracking(unittest.TestCase):

    def setUp(self):
        drop_db()
        super().setUp()

    def tearDown(self):
        drop_db()
        super().tearDown()

    def test(self):
        config = activate_modules(['timetracker', 'project'])
        create_company(config=config)
        company = get_company(config=config)
        Party = Model.get('party.party')
        Employee = Model.get('company.employee')
        Line = Model.get('timesheet.line')
        party = Party(name='Employee')
        party.save()
        employee = Employee(party=party, company=company)
        employee.save()
        User = Model.get('res.user')
        user = User(config.user)
        user.employees.append(employee)
        user.employee = employee
        user.save()
        config._context = User.get_preferences(True, {})
        Work = Model.get('project.work')
        work = Work(name='Project', timesheet_available=True)
        work.save()
        work.click('start_work_wizard')
        line, = Line.find([('work', '=', work.timesheet_works[0].id)])
        self.assertEqual(line.employee, employee)
        self.assertIsNotNone(line.start)
        self.assertIsNone(line.end)
        work.click('stop_work')
        line.reload()
        self.assertIsNotNone(line.end)
        # DateTime fields discard microseconds when stored.
        self.assertLess(
            abs(line.duration - (line.end - line.start)),
            timedelta(seconds=1))
        self.assertGreaterEqual(line.duration, timedelta(0))
