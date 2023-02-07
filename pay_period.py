import datetime
from typing import List, Tuple


class PayPeriod:
    """Holder for information about a pay period"""

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
    """Class to use for information about a vacation"""

    def __init__(self, start_date: datetime.date, hours_length: float) -> None:
        self.start_date = start_date
        self.length = hours_length

    def __lt__(self, other):
        if isinstance(other, Vacation):
            return self.start_date < other.start_date
        if isinstance(other, datetime.date):
            return self.start_date < other
        raise TypeError(
            f"'<' not supported between instances of Vacation and {type(other)}")


class AccruementPeriod:
    """Type for PTOAccruement to hold the information of each period"""

    def __init__(self, period_length: int,
                 start_date: datetime.date,
                 end_date: datetime.date,
                 accruement: float,) -> None:
        self.period_length = period_length
        self.start_date = start_date
        self.end_date = end_date
        self.accruement = accruement


class PTOAccruement:
    """Class used to handle PTO accruing"""

    def __init__(self, periods: List[AccruementPeriod],
                 starting_pto: float = 0,
                 starting_day: datetime.date = datetime.date.today()) -> None:
        """PTO accrual handler.

        Args:
            period_length (List[int]): A list of the lengths of each period
            start_date (List[datetime.date]): The start date of each period.
            end_date (List[datetime.date]): _description_
            accruement (List[float]): _description_
            starting_pto (float, optional): _description_. Defaults to 0.
            starting_day (datetime.date, optional): _description_. Defaults to date.today().

        Raises:
            ValueError: _description_
        """
        self.periods = periods
        self.pto = starting_pto
        self.today = starting_day

    class PastDateException(Exception):
        """Raised when the current date is further than the end date."""

    def next_period(self, pto_use: float = 0) -> float:
        """Calculate the gain/loss for this period,
        then remove it from the stack to move on to the next stack

        Args:
            pto_use (float, optional): How much PTO is used in this period.. Defaults to 0.

        Raises:
            PastDateException: If the current date is already past the end date of the pay period.

        Returns:
            float: the amount of PTO remaining after this period
        """
        period = self.periods[0]
        end, pay_period = (period.end_date, PayPeriod(
            period.accruement, period.period_length))
        # Add a buffer at the end to let it go 1 period past
        # So we don't lose PTO used on the last week.
        if self.today > (end + datetime.timedelta(days=pay_period.period_length)):
            if len(self.periods) == 1:
                raise self.PastDateException
            self.periods.pop(0)
            return self.next_period(pto_use)
        self.pto, self.today = pay_period.add_pto(self.pto, self.today)
        self.pto -= pto_use
        return self.pto

    def get_final_pto(self, vacations: List[Vacation]) -> Tuple[float, List[float]]:
        """Iterates until self.end_date.

        Args:
            vacations (List[Vacation]): The list of Vacations to use to calculate PTO usage

        Returns:
            Tuple[float, List[float]]: 
                float: the PTO at the end
                List[float]: The pto at the end of each pay period 
        """
        intermediate_ptos = []
        vacations = sorted(vacations)
        print(f'Start date is {self.today}')
        while True:
            used_pto: float = 0
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
        print(f'End date is {self.today}')
        return self.pto, intermediate_ptos


# Example use:
# sd = datetime.date(2023, 1, 27)
# ed = datetime.date(2023, 12, 31)
# p_len = [14, 14]
# start_dates = [sd, datetime.date(2023, 4, 4)]
# end_dates = [datetime.date(2023, 4, 4), ed]
# acc = [5.85, 7.40]
# b: List[AccruementPeriod] = []
# for i, p in enumerate(p_len):
#     b.append(AccruementPeriod(p, start_dates[i], end_dates[i], acc[i]))
# a = PTOAccruement(b, 33.42)
# vacation_weeks = [Vacation(datetime.date(2023, 3, 6), 40),
#                   Vacation(datetime.date(2023, 5, 1), 40),
#                   Vacation(datetime.date(2023, 7, 3), 32),
#                   Vacation(datetime.date(2023, 9, 4), 32),
#                   Vacation(datetime.date(2023, 11, 24), 24),
#                   Vacation(datetime.date(2023, 12, 25), 24),]
# print('starting PTO 33.42')
# for v in vacation_weeks:
#     print(f'{v.length} hours on week of {v.start_date}')
# print(f'Final PTO: {a.get_final_pto(vacation_weeks)[0]:0.2f} hours')
