# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.model import ModelView, fields
from trytond.pool import Pool, PoolMeta
from trytond.pyson import Eval, Bool
from trytond.transaction import Transaction
from trytond.wizard import Wizard, StateTransition, StateView, Button

__all__ = ['Work', 'Employee', 'StartWorkChooseAction', 'StartWork']


class Employee:
    __metaclass__ = PoolMeta
    __name__ = 'company.employee'

    @property
    def tasks_working_on(self):
        Task = Pool().get('project.work')
        lines = self.opened_timesheet_lines
        return Task.search([
                ('id', 'in', [x.work.id for x in lines]),
                ])

    @property
    def opened_timesheet_lines(self):
        Line = Pool().get('timesheet.line')
        lines = Line.search([
                ('start', '!=', None),
                ('end', '=', None),
                ('employee', '=', self.id),
                ])
        return lines


class StartWorkChooseAction(ModelView):
    'Start Work - Choose Action'
    __name__ = "timesheet.line.start_work.choose_action"

    opened_lines = fields.Many2Many('timesheet.line', None, None,
        'Opened Lines', readonly=True)
    opened_tasks = fields.Many2Many('project.work', None, None, 'Opened Tasks',
        readonly=True)


class StartWork(Wizard):
    'Start Work'
    __name__ = 'timesheet.line.start_work'

    start = StateTransition()
    choose_action = StateView('timesheet.line.start_work.choose_action',
        'timetracker.start_work_choose_action_view_form', [
            Button('Cancel', 'end', 'tryton-cancel'),
            Button('Discard & Start', 'discard_and_start_work'),
            Button('Close & Start', 'close_and_start_work', default=True)
            ])
    close_and_start_work = StateTransition()
    discard_and_start_work = StateTransition()

    def default_choose_action(self, fields):
        User = Pool().get('res.user')
        user = User(Transaction().user)
        if not user.employee:
            return {
                'opened_lines': [],
                'opened_tasks': [],
                }
        return {
            'opened_lines': [x.id
                for x in user.employee.opened_timesheet_lines],
            'opened_tasks': [x.id for x in user.employee.tasks_working_on],
            }

    def transition_start(self):
        User = Pool().get('res.user')
        user = User(Transaction().user)
        if user.employee and not user.employee.opened_timesheet_lines:
            return self._start_current_work()
        return 'choose_action'

    def transition_close_and_start_work(self):
        Task = Pool().get('project.work')
        Task.stop_work(self.choose_action.opened_tasks)
        return self._start_current_work()

    def transition_discard_and_start_work(self):
        Task = Pool().get('project.work')
        Task.cancel_work(self.choose_action.opened_tasks)
        return self._start_current_work()

    def _start_current_work(self):
        Task = Pool().get('project.work')
        task = Task(Transaction().context['active_id'])
        task.start_work()
        return 'end'


class Work:
    __metaclass__ = PoolMeta
    __name__ = 'project.work'

    working_employees = fields.Function(fields.Many2Many('company.employee',
            None, None, 'Emloyee Working',
            help='Employees working on this work'), 'get_working_employees')

    @classmethod
    def __setup__(cls):
        super(Work, cls).__setup__()
        cls._buttons.update({
                'start_work_wizard': {
                    'readonly': Eval('working_employees',
                        []).contains(Eval('context', {}).get('employee', 0)),
                    },
                'stop_work': {
                    'readonly': ~Eval('working_employees',
                        []).contains(Eval('context', {}).get('employee', 0)),
                    },
                'cancel_work': {
                    'readonly': ~Eval('working_employees',
                        []).contains(Eval('context', {}).get('employee', 0)),
                    },
                })

    def get_working_employees(self, name=None):
        Line = Pool().get('timesheet.line')
        if not self.timesheet_available:
            return []
        lines = Line.search([
                ('start', '!=', None),
                ('work', 'in', [t.id for t in self.timesheet_works]),
                ('end', '=', None)])
        if not lines:
            return []
        return list(set([x.employee.id for x in lines if x.employee]))

    @classmethod
    @ModelView.button_action('timetracker.act_start_work')
    def start_work_wizard(cls, tasks):
        pass

    def start_work(self):
        if not self.timesheet_available:
            return
        Line = Pool().get('timesheet.line')
        User = Pool().get('res.user')
        user = User(Transaction().user)
        line = Line()
        line.work, = self.timesheet_works
        line.start = Line.default_start()
        line.duration = Line.default_duration()
        line.employee = user.employee.id
        line.save()

    @classmethod
    @ModelView.button
    def cancel_work(cls, tasks):
        Line = Pool().get('timesheet.line')
        Line = Pool().get('timesheet.line')
        User = Pool().get('res.user')
        user = User(Transaction().user)

        tworks = [t.id for x in tasks for t in x.timesheet_works]
        lines = Line.search([
                ('work', 'in', tworks),
                ('employee', '=', user.employee.id),
                ('start', '!=', None),
                ('end', '=', None),
                ])
        Line.delete(lines)
        return

    @classmethod
    @ModelView.button
    def stop_work(cls, tasks):
        Line = Pool().get('timesheet.line')
        User = Pool().get('res.user')
        user = User(Transaction().user)

        tworks = [t.id for x in tasks for t in x.timesheet_works]
        lines = Line.search([
                ('work', 'in', tworks),
                ('employee', '=', user.employee.id),
                ('start', '!=', None),
                ('end', '=', None),
                ])
        for line in lines:
            line.stop()
