import datetime
from typing import Tuple, List, Dict

class PayPeriod:
    def __init__(self, hours_per_period: float, period_length: int = 14) -> None:
        """Generates a pay period.

        Args:
            hours_per_period (float): the amount of hours you get in PTO per period
            period_length (int, Optional): the length in days a payperiod is. Default 14 for every other week.
        """
        self.pto_accruement = hours_per_period
        self.period_length = period_length

    def add_pto(self, current_pto: float, current_date: datetime.date) -> Tuple[float, datetime.date]:
        """Adds the accruement of PTO for a pay period

        Args:
            current_pto (float): the amount of pto you currently have
            current_date (date): the date the payperiod stops on
        Returns:
            tuple[float, date]:
                float: the pto added
                date: the end date of the pay period
        """
        current_pto += self.pto_accruement
        current_date += datetime.timedelta(days=self.period_length)
        return (current_pto, current_date)
class Vacation:
    def __init__(self, start_date: datetime.date, hours_length: float) -> None:
        self.start_date = start_date
        self.length = hours_length
    
    def __lt__(self, other):
        if isinstance(other, Vacation):
            return self.start_date < other.start_date
        if isinstance(other, datetime.date):
            return self.start_date < other
        raise TypeError(f"'<' not supported between instances of Vacation and {type(other)}")
class PTOAccruement:
    def __init__(self, period_length: List[int],
                       start_date: List[datetime.date],
                       end_date: List[datetime.date],
                       accruement: List[float],
                       starting_pto:float = 0,
                       starting_day: datetime.date = datetime.date.today()) -> None:
        if not self._check_lens(period_length, start_date, end_date, accruement):
            raise ValueError("All lists must be the same length")
        self.periods: Tuple[datetime.date, datetime.date, PayPeriod] = []
        for i, period in enumerate(period_length):
            self.periods.append((start_date[i], end_date[i], PayPeriod(accruement[i], period)))
        self.pto = starting_pto
        self.today = starting_day

    def _check_lens(self, *iterables):
        return (len(set(map(len, iterables))) == 1)

    class PastDateException(Exception):
        pass

    def next_period(self, pto_use:float = 0):
        _, end, pay_period = self.periods[0]
        # Add a buffer at the end to let it go 1 period past
        # So we don't lose PTO used on the last week.
        if self.today > (end + datetime.timedelta(days=pay_period.period_length)):
            if len(self.periods) == 1:
                raise self.PastDateException
            else:
                self.periods.pop(0)
                return self.next_period(pto_use)
        self.pto, self.today = pay_period.add_pto(self.pto, self.today)
        self.pto -= pto_use
        return self.pto

    def get_final_pto(self, vacations: List[Vacation]) -> Tuple[float, List[float]]:
        intermediate_ptos = []
        vacations = sorted(vacations)
        while True:
            used_pto = 0
            try:
                for date in vacations:
                    if date < self.today:
                        used_pto += date.length
                        vacations.remove(date)
                    else:
                        break
                intermediate_ptos.append(self.next_period(used_pto))
            except self.PastDateException:
                break
        return self.pto, intermediate_ptos

# Example use:
# start_date = datetime.date(2023, 1, 27)
# end_date = datetime.date(2023, 12, 31)
# p_len = [14, 14]
# start_dates = [start_date, datetime.date(2023, 4, 4)]
# end_dates = [datetime.date(2023,4,4), end_date]
# accruement = [5.85,7.40]
# a = PTOAccruement(p_len, start_dates, end_dates, accruement, 33.42)
# vacation_weeks = [Vacation(datetime.date(2023, 3, 6), 40),
#                   Vacation(datetime.date(2023, 5, 1), 40),
#                   Vacation(datetime.date(2023, 7, 3), 32),
#                   Vacation(datetime.date(2023, 9, 4), 32),
#                   Vacation(datetime.date(2023, 11, 24), 24),
#                   Vacation(datetime.date(2023, 12, 25), 24),]
# ptos = []
# print('starting PTO 33.42')
# for v in vacation_weeks:
#     print(f'{v.length} hours on week of {v.start_date}')
# print(f'Final PTO: {a.get_final_pto(vacation_weeks)[0]:0.2f} hours')