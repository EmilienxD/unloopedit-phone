from typing import Callable
from importlib import import_module
from datetime import datetime, timedelta
from atexit import register

from lib.modules.display import Logger
from lib.modules.basics.UList import UList

from lib.config import Paths
from lib import utils
from lib.helpers import Counter
from lib.exceptions import InvalidFileStructure, PlanError


logger = Logger('[Planner]')


class Planning:

    path = Paths('lib/planning/planning.json')

    def __init__(self, expired_plan_timeout: int | None = None):
        self.plans: UList[Plan] = UList()
        if expired_plan_timeout is not None:
            assert expired_plan_timeout >= 0, f"Expried plan timeout can't be negativ ({expired_plan_timeout})"
        self.expired_plan_timeout = expired_plan_timeout
        self._read_planning()
        register(self._write_planning)

    def _read_planning(self, as_dict: bool = False) -> list['Plan'] | dict[str, dict]:
        planning_dict: dict[str, dict[str, dict]] = self.path.read(default={})
        try:
            for plan_date, plan_attrs in planning_dict.items():
                if self.expired_plan_timeout is not None and (utils.str_to_date(plan_date) + timedelta(days=self.expired_plan_timeout) < datetime.now()):
                    continue    # Expired plans will be removed when the planning will be updated
                day_plan = Plan(
                    account_name=plan_attrs['account_name'],
                    task_name=plan_attrs['task_name'],
                    exec_func_name=plan_attrs['exec_func_name'],
                    date=plan_date,
                    goal_value=plan_attrs['goal_value'],
                    count=plan_attrs['count'],
                    last_captured_error=plan_attrs['last_captured_error']
                )
                self.plans.append(day_plan)
            self.sort_plans()
        except KeyError as e:
            raise InvalidFileStructure(self.path, additional_message=e)
        return planning_dict if as_dict else self.plans
    
    def _write_planning(self) -> None:
        planning_dict = {
            day_plan.date: day_plan.as_dict
            for day_plan in self.plans
        }
        self.path.write(planning_dict, send_to_trash=False)

    def sort_plans(self) -> None:
        self.plans.sort(key=lambda plan: utils.str_to_date(plan.date))

    def add_plan(self, account_name: str, task_name: str, goal_value: int, date: str | int = 'today', exec_func_name: str = 'main') -> 'Plan':
        plan = Plan(
            task_name=task_name,
            account_name=account_name,
            date=utils.create_unique_date() if date == 'today' else (datetime.now() + timedelta(days=date) if isinstance(date, int) else date),
            goal_value=goal_value,
            exec_func_name=exec_func_name
        )
        self.plans.append(plan)
        self.sort_plans()
        return plan
    
    def get_plan(self, date: str) -> None:
        for plan in self.plans:
            if plan.date == date:
                return plan
        logger.warn(f'Plan with date: {date} not found')
    
    def remove_plan(self, date: str) -> None:
        for plan in self.plans:
            if plan.date == date:
                self.plans.remove(plan)
                return
        logger.warn(f'Plan with date: {date} not found')
            
    def clear_plans(self) -> None:
        self.plans = UList()

    def __str__(self) -> str:
        text = "Planning:\n"
        text += '#' * 100 + '\n'
        text += '\n'.join(map(str, self.plans))
        text += '\n' + '#' * 100
        return text
    
    def __repr__(self) -> str:
        return self.__str__()
    
    def execute(self) -> None:
        [plan.execute() for plan in self.plans]

class Plan:
    def __init__(self,
            account_name: str,
            task_name: str,
            date: str,
            goal_value: int,
            count: Counter | int | None = None,
            last_captured_error: str | None = None,
            exec_func_name: str = 'run'
        ) -> None:
        self.account_name = account_name
        self.task_name = task_name
        self.date = date
        self.goal_value = goal_value
        self.count = Counter(count or 0)
        self.last_captured_error = last_captured_error
        self.func: Callable[[int, Counter], None] = getattr(
            import_module(f"sm_accounts.{self.account_name}.tasks.{self.task_name}", package=Paths.BASE_PATH.fs),
            exec_func_name
        )

    @property
    def progression(self) -> str:
        return f"{min(100, round(self.count/self.goal_value*100))}%" if self.goal_value else "100%"

    @property
    def status(self) -> str:
        """pending, started or completed"""
        return ("pending" if self.count == 0 else ("completed" if self.count >= self.goal_value else "started")) if self.goal_value else "completed"

    @property
    def as_dict(self) -> dict:
        return {
            'account_name': self.account_name,
            'task_name': self.task_name,
            'exec_func_name': self.func.__name__,
            'progression': self.progression,
            'status': self.status,
            'count': self.count.get(),
            'goal_value': self.goal_value,
            'last_captured_error': self.last_captured_error
        }

    def execute(self) -> None:
        if self.status == "completed":
            return
        try:
            self.func(self.goal_value, self.count)
            if self.count < 0:
                raise ValueError(f"Current count can not be negativ ({self.count})")
        except Exception as e:
            self.last_captured_error = str(e)
            raise PlanError(acc_name=self.account_name, task_name=self.task_name, plan_date=self.date, base_error=e) from e

    def __eq__(self, other: 'Plan') -> bool:
        return self.date == other.date
    
    def __hash__(self) -> int:
        return hash(self.date)
    
    def __str__(self) -> str:
        return (f"Plan(account_name={self.account_name}, task_name={self.task_name}, execute_func_name={self.func.__name__}, date={self.date}, "
                f"count={self.count}, goal_value={self.goal_value}, "
                f"progression={self.progression}, status={self.status}, "
                f"last_captured_error={self.last_captured_error})")

    def __repr__(self) -> str:
        return self.__str__()