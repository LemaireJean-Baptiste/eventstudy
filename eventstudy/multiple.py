from .utils import to_table, plot, read_csv
from .exception import (
    CustomException,
    DateMissingError,
    DataMissingError,
    ColumnMissingError,
)
import logging

import numpy as np
import statsmodels.api as sm
from scipy.stats import t, kurtosis, skew
import datetime


class Multiple:
    """
    Implement computations on an aggregate of event studies.
    Among which cumulative average abnormal returns (CAAR) and its significance tests.
    This implementation heavily relies on the work of MacKinlay [1]_.

    Basically, this class takes in input a list of single event studies (`eventstudy.Single`),
    aggregate them and gives access to aggregate statistics and tests.

    Note
    ----

    All single event studies must have the same specifications (event, estimation and buffer windows).
    However, the model used for each event study can be different (if needed).

    References
    ----------

    .. [1] Mackinlay, A. (1997). “Event Studies in Economics and Finance”.
        In: Journal of Economic Literature 35.1, p. 13.
    """
    def __init__(self, sample: list, errors=None, description: str = None):
        """
        Low-level (complex) way of runing an aggregate of event studies.

        Parameters
        ----------
        sample : list
            List containing `eventstudy.Single` objects. 
            You can run independently each eventstudy, aggregate 
            them in a dictionary and compute their aggregate statistics.
        errors : list, optional
            A list containing errors encountered during the computation of single event studies, by default None.

        See also
        -------

        from_csv, from_list, from_text

        Example
        -------

        Run an aggregate of event studies for Apple Inc. 10-K form releases. 
        We loop into a list of dates (in string format). 
        We first convert dates to a numpy.datetie64 format, 
        then run each event study, store them in an `events` list.
        Finally, we run the aggregate event study.
        
        1. Import packages:
        >>> import numpy as np
        >>> import datetime
        >>> import eventstudy as es

        2. import datas and initialize an empty list to store events:
        >>> es.Single.import_returns('returns.csv')
        >>> dates = ['05/11/2018', '03/11/2017', '26/10/2016', 
        ...     '28/10/2015', '27/10/2014', '30/10/2013',
        ...     '31/10/2012', '26/10/2011', '27/10/2010']
        >>> events = list()

        3. Run each single event:
        >>> for date in dates:
        ...     formated_date = np.datetime64(
        ...         datetime.datetime.strptime(date, '%d/%m/%Y')   
        ...     )
        ...     event = es.Single.market_model(
        ...         security_ticker = 'AAPL',
        ...         market_ticker = 'SPY',
        ...         event_date = formated_date
        ...     )
        ...     events.append(event)

        4. Run the aggregate event study
        >>> agg = es.Multiple(events)
        """
        self.errors = errors
        self.__warn_errors()

        # retrieve common parameters from the first occurence in eventStudies:
        self.event_window = sample[0].event_window
        self.event_window_size = sample[0].event_window_size
        self.sample = sample
        self.CAR = [event.CAR[-1] for event in sample]
        self.description = description
        self.__compute()
        

    # def __computeByCAR(self, sample):
    #    # Deprecated, works, gives the same results than __compute but without AAR computation (which can be needed)
    #    # So gives less information
    #    self.CAAR = 1/len(sample) * np.sum([event.CAR for event in sample], axis=0)
    #    self.var_CAAR = (1/(len(sample)**2)) * np.sum([event.var_CAR for event in sample], axis=0)

    def __compute(self):
        self.AAR = 1 / len(self.sample) * np.sum([event.AR for event in self.sample], axis=0)
        self.var_AAR = (1 / (len(self.sample) ** 2)) * np.sum(
            [event.var_AR for event in self.sample], axis=0
        )
        self.CAAR = np.cumsum(self.AAR)
        self.var_CAAR = [
            np.sum(self.var_AAR[:i]) for i in range(1, self.event_window_size + 1)
        ]

        self.tstat = self.CAAR / np.sqrt(self.var_CAAR)
        self.df = np.sum([event.df for event in self.sample], axis=0)
        self.pvalue = 1.0 - t.cdf(abs(self.tstat), self.df)

        self.CAR_dist = self.__compute_CAR_dist()

    def __compute_CAR_dist(self):
        CAR = [event.CAR for event in self.sample]
        CAR_dist = {
            "Mean": np.mean(CAR, axis=0),
            "Variance": np.var(CAR, axis=0),
            "Kurtosis": kurtosis(CAR, axis=0),
            "Skewness": skew(CAR, axis=0),
            "Min": np.min(CAR, axis=0),
            "Quantile 25%": np.quantile(CAR, q=0.25, axis=0),
            "Quantile 50%": np.quantile(CAR, q=0.5, axis=0),
            "Quantile 75%": np.quantile(CAR, q=0.75, axis=0),
            "Max": np.max(CAR, axis=0),
        }
        return CAR_dist

    def sign_test(self, sign="positive", confidence=0.9):
        """ Not implemented yet """
        # signtest
        # return nonParametricTest(self.CAR).signTest(sign, confidence)
        pass

    def rank_test(self, confidence):
        """ Not implemented yet """
        pass

    def results(self, asterisks: bool = True, decimals=3):
        """
        Give event study result in a table format.
        
        Parameters
        ----------
        asterisks : bool, optional
            Add asterisks to CAR value based on significance of p-value, by default True
        decimals : int or list, optional
            Round the value with the number of decimal specified, by default 3.
            `decimals` can either be an integer, in this case all value will be 
            round at the same decimals, or a list of 6 decimals, in this case each 
            columns will be round based on its respective number of decimal.
        
        Note
        ----

        When `asterisks` is set as True, CAR's are converted to string type.
        To make further computation on CARs possible set `asterisks` to False.

        Returns
        -------
        pandas.DataFrame
            AAR and AAR's variance, CAAR and CAAR's variance, T-stat and P-value, 
            for each T in the event window.

        Note
        ----
        
        The function return a fully working pandas DataFrame.
        All pandas method can be used on it, especially exporting method (to_csv, to_excel,...)

        Example
        -------

        Get results of a market model event study on an 
        aggregate of events (Apple Inc. 10-K form releases) imported 
        from a csv, with specific number of decimal for each column:

        >>> events = es.Multiple.from_csv(
        ...     'AAPL_10K.csv',
        ...     es.Single.FamaFrench_3factor,
        ...     event_window = (-5,+5),
        ...     date_format = '%d/%m/%Y'
        ... )
        >>> events.results(decimals = [3,5,3,5,2,2])

        ====  ======  ==============  =======  ===============  ========  =========
          ..     AAR    Variance AAR  CAAR       Variance CAAR    T-stat    P-value
        ====  ======  ==============  =======  ===============  ========  =========
          -5  -0               3e-05  -0.0             3e-05       -0.09       0.47
          -4  -0.002           3e-05  -0.003           5e-05       -0.35       0.36
          -3   0.009           3e-05  0.007            8e-05        0.79       0.22
          -2   0.003           3e-05  0.01             0.0001       1.03       0.15
          -1   0.008           3e-05  0.018 *          0.00013      1.61       0.05
           0  -0               3e-05  0.018 *          0.00015      1.46       0.07
           1  -0.006           3e-05  0.012            0.00018      0.88       0.19
           2   0.006           3e-05  0.017            0.0002       1.22       0.11
           3   0               3e-05  0.018            0.00023      1.17       0.12
           4  -0.007           3e-05  0.011            0.00025      0.69       0.24
           5   0.001           3e-05  0.012            0.00028      0.72       0.24
        ====  ======  ==============  =======  ===============  ========  =========

        Note
        ----
        
        Significance level: \*\*\* at 99%, \*\* at 95%, \* at 90%
        """
        columns = {
            "AAR": self.AAR,
            "Std. E. AAR": np.sqrt(self.var_AAR),
            "CAAR": self.CAAR,
            "Std. E. CAAR": np.sqrt(self.var_CAAR),
            "T-stat": self.tstat,
            "P-value": self.pvalue,
        }
        
        asterisks_dict = {"pvalue": "P-value", "where": "CAAR"} if asterisks else None

        return to_table(
            columns,
            asterisks_dict=asterisks_dict,
            decimals=decimals,
            index_start=self.event_window[0],
        )

    def plot(self, *, AAR=False, CI=True, confidence=0.90):
        """
        Plot the event study result.
        
        Parameters
        ----------
        AAR : bool, optional
            Add to the figure a bar plot of AAR, by default False
        CI : bool, optional
            Display the confidence interval, by default True
        confidence : float, optional
            Set the confidence level, by default 0.90
        
        Returns
        -------
        matplotlib.figure
            Plot of CAAR and AAR (if specified).

        Note
        ----
        The function return a fully working matplotlib function.
        You can extend the figure and apply new set-up with matplolib's method (e.g. savefig).
        
        Example
        -------

        Plot CAR (in blue) and AR (in black), with a confidence interval of 95% (in grey).

        >>> events = es.Multiple.from_csv(
        ...     'AAPL_10K.csv',
        ...     es.Single.FamaFrench_3factor,
        ...     event_window = (-5,+5),
        ...     date_format = '%d/%m/%Y'
        ... )
        >>> events.plot(AR = True, confidence = .95)

        .. image:: /_static/single_event_plot.png
        """
        return plot(
            time=range(self.event_window[0], self.event_window[1] + 1),
            CAR=self.CAAR,
            AR=self.AAR if AAR else None,
            CI=CI,
            var=self.var_CAAR,
            df=self.df,
            confidence=confidence,
        )

    def get_CAR_dist(self, decimals=3):
        """
        Give CARs' distribution descriptive statistics in a table format.
        
        Parameters
        ----------
        decimals : int or list, optional
            Round the value with the number of decimal specified, by default 3.
            `decimals` can either be an integer, in this case all value will be 
            round at the same decimals, or a list of 6 decimals, in this case each 
            columns will be round based on its respective number of decimal.

        Returns
        -------
        pandas.DataFrame
            CARs' descriptive statistics 

        Note
        ----
        
        The function return a fully working pandas DataFrame.
        All pandas method can be used on it, especially exporting method (to_csv, to_excel,...)

        Example
        -------

        Get CARs' descriptive statistics  of a market model event study on an
        aggregate of events (Apple Inc. 10-K release) imported 
        from a csv, with specific number of decimal for each column:

        >>> events = es.Multiple.from_csv(
        ...     'AAPL_10K.csv',
        ...     es.Single.FamaFrench_3factor,
        ...     event_window = (-5,+5),
        ...     date_format = '%d/%m/%Y'
        ... )
        >>> events.get_CAR_dist(decimals = 4)

        ====  ======  ==========  ========== ==========  ======  ==============  ==============  ==============  =====
          ..    Mean    Variance    Kurtosis Skewness       Min    Quantile 25%    Quantile 50%    Quantile 75%    Max
        ====  ======  ==========  ========== ==========  ======  ==============  ==============  ==============  =====
          -5  -0           0.001       0.061      0.301  -0.052          -0.014           0.001           0.015  0.047
          -4  -0.003       0.001       0.247      0.447  -0.091          -0.022           0.003           0.015  0.081
          -3   0.007       0.002       0.532      0.982  -0.082          -0.026           0.006           0.027  0.139
          -2   0.01        0.002      -0.025     -0.235  -0.088          -0.021           0.002           0.033  0.115
          -1   0.018       0.003      -0.065     -0.545  -0.091          -0.012           0.02            0.041  0.138
           0   0.018       0.003      -0.724     -0.344  -0.084          -0.012           0.012           0.057  0.128
           1   0.012       0.004      -0.613     -0.233  -0.076          -0.024           0.003           0.059  0.143
           2   0.017       0.005      -0.55      -0.345   -0.117          -0.026           0.024           0.057  0.156
           3   0.018       0.005       0.289      0.223  -0.162          -0.032           0.027           0.057  0.17
           4   0.011       0.007       2.996      0.243  -0.282          -0.039           0.035           0.052  0.178
           5   0.012       0.008       1.629      0.543  -0.266          -0.05            0.035           0.064  0.174
        ====  ======  ==========  ========== ==========  ======  ==============  ==============  ==============  =====

        Note
        ----
        
        Significance level: \*\*\* at 99%, \*\* at 95%, \* at 90%
        """
        return to_table(
            self.CAR_dist, decimals=decimals, index_start=self.event_window[0]
        )

    @classmethod
    def from_text(
        cls,
        text: str,
        event_study_model,
        event_window: tuple = (-10, +10),
        estimation_size: int = 300,
        buffer_size: int = 30,
        *,
        date_format: str = "%Y-%m-%d",
        keep_model: bool = False,
        ignore_errors: bool = True,
    ):
        """
        Compute an aggregate of event studies from a multi-line string containing each event's parameters.
        
        Parameters
        ----------
        text : str
            List of events in a multi-line string format. The first line must contains 
            the name of each parameter needed to compute the event_study_model.
            All value must be separated by a comma (see example for more details).
        event_study_model
            Function returning an eventstudy.Single class instance.
            For example, eventstudy.Single.market_model() (a custom functions can be created).
        event_window : tuple, optional
            Event window specification (T2,T3), by default (-10, +10).
            A tuple of two integers, representing the start and the end of the event window. 
            Classically, the event-window starts before the event and ends after the event.
            For example, `event_window = (-2,+20)` means that the event-period starts
            2 periods before the event and ends 20 periods after.
        estimation_size : int, optional
            Size of the estimation for the modelisation of returns [T0,T1], by default 300
        buffer_size : int, optional
            Size of the buffer window [T1,T2], by default 30
        date_format : str, optional
            Format of the date provided in the event_date column, by default "%Y-%m-%d".
            Refer to datetime standard library for more details date_format: 
            https://docs.python.org/2/library/datetime.html#strftime-strptime-behavior
        keep_model : bool, optional
            If true the model used to compute each single event study will be stored in memory.
            They will be accessible through the class attributes eventStudy.Multiple.singles[n].model, by default False
        ignore_errors : bool, optional
            If true, errors during the computation of single event studies will be ignored. 
            In this case, these events will be removed from the computation.
            However, a warning message will be displayed after the computation to warn for errors. 
            Errors can also be accessed using `print(eventstudy.Multiple.error_report())`.
            If false, the computation will be stopped by any error encounter 
            during the computation of single event studies, by default True
            
        See also
        --------
        
        from_list, from_csv

        Example
        -------

        >>> text = \"\"\"security_ticker, market_ticker, event_date
        ...     AAPL, SPY, 05/11/2018
        ...     AAPL, SPY, 03/11/2017
        ...     AAPL, SPY, 26/10/2016
        ...     AAPL, SPY, 28/10/2015
        ... \"\"\"
        >>> agg = eventstudy.Multiple.from_text(
        ...     text = text,
        ...     event_study_model = eventstudy.Single.market_model,
        ...     event_window = (-5,+10),
        ...     date_format = "%d/%m/%Y"
        ... ) 
        """

        rows = list(map(lambda x: list(map(str.strip, x.split(","))), text.split("\n")))
        headers = rows.pop(0)
        event_list = [{headers[i]: v for i, v in enumerate(row)} for row in rows]

        for event in event_list:
            event["event_date"] = np.datetime64(
                datetime.datetime.strptime(event["event_date"], date_format)
            )

        return cls.from_list(
            event_list,
            event_study_model,
            event_window,
            estimation_size,
            buffer_size,
            keep_model=keep_model,
            ignore_errors=ignore_errors,
        )

    @classmethod
    def from_list(
        cls,
        event_list: list,
        event_study_model,
        event_window: tuple = (-10, +10),
        estimation_size: int = 300,
        buffer_size: int = 30,
        *,
        keep_model: bool = False,
        ignore_errors: bool = True,
    ):
        """
        Compute an aggregate of event studies from a list containing each event's parameters.
        
        Parameters
        ----------
        event_list : list
            List containing dictionaries specifing each event's parameters (see example for more details).
        event_study_model
            Function returning an eventstudy.Single class instance.
            For example, eventstudy.Single.market_model() (a custom functions can be created).
        event_window : tuple, optional
            Event window specification (T2,T3), by default (-10, +10).
            A tuple of two integers, representing the start and the end of the event window. 
            Classically, the event-window starts before the event and ends after the event.
            For example, `event_window = (-2,+20)` means that the event-period starts
            2 periods before the event and ends 20 periods after.
        estimation_size : int, optional
            Size of the estimation for the modelisation of returns [T0,T1], by default 300
        buffer_size : int, optional
            Size of the buffer window [T1,T2], by default 30
        keep_model : bool, optional
            If true the model used to compute each single event study will be stored in memory.
            They will be accessible through the class attributes eventStudy.Multiple.singles[n].model, by default False
        ignore_errors : bool, optional
            If true, errors during the computation of single event studies will be ignored. 
            In this case, these events will be removed from the computation.
            However, a warning message will be displayed after the computation to warn for errors. 
            Errors can also be accessed using `print(eventstudy.Multiple.error_report())`.
            If false, the computation will be stopped by any error encounter 
            during the computation of single event studies, by default True
            
        See also
        --------
        
        from_text, from_csv

        Example
        -------

        >>> list = [
        ...     {'event_date': np.datetime64("2018-11-05"), 'security_ticker': 'AAPL'},
        ...     {'event_date': np.datetime64("2017-11-03"), 'security_ticker': 'AAPL'},
        ...     {'event_date': np.datetime64("2016-10-26"), 'security_ticker': 'AAPL'},
        ...     {'event_date': np.datetime64("2015-10-28"), 'security_ticker': 'AAPL'},
        ... ]
        >>> agg = eventstudy.Multiple.from_list(
        ...     text = list,
        ...     event_study_model = eventstudy.Single.FamaFrench_3factor,
        ...     event_window = (-5,+10),
        ... ) 
        """

        # event_list = [
        #   {'event_date': np.datetime64, models_data},
        #   {'event_date': np.datetime64, models_data}
        # ]
        sample = list()
        errors = list()
        for event_params in event_list:
            try:
                event = event_study_model(
                    **event_params,
                    event_window=event_window,
                    estimation_size=estimation_size,
                    buffer_size=buffer_size,
                    keep_model=keep_model,
                )
            except (DateMissingError, DataMissingError, ColumnMissingError) as e:
                if ignore_errors:
                    event_params["error_type"] = e.__class__.__name__
                    event_params["error_msg"] = e.helper
                    errors.append(event_params)
                else:
                    raise e
            else:
                sample.append(event)

        return cls(sample, errors)

    @classmethod
    def from_csv(
        cls,
        path,
        event_study_model,
        event_window: tuple = (-10, +10),
        estimation_size: int = 300,
        buffer_size: int = 30,
        *,
        date_format: str = "%Y%m%d",
        keep_model: bool = False,
        ignore_errors: bool = True,
    ):
        """
        Compute an aggregate of event studies from a csv file containing each event's parameters.
        
        Parameters
        ----------
        path : str
            Path to the csv file containing events' parameters.
            The first line must contains the name of each parameter needed to compute the event_study_model.
            All value must be separated by a comma.
        event_study_model
            Function returning an eventstudy.Single class instance.
            For example, eventstudy.Single.market_model() (a custom functions can be created).
        event_window : tuple, optional
            Event window specification (T2,T3), by default (-10, +10).
            A tuple of two integers, representing the start and the end of the event window. 
            Classically, the event-window starts before the event and ends after the event.
            For example, `event_window = (-2,+20)` means that the event-period starts
            2 periods before the event and ends 20 periods after.
        estimation_size : int, optional
            Size of the estimation for the modelisation of returns [T0,T1], by default 300
        buffer_size : int, optional
            Size of the buffer window [T1,T2], by default 30
        date_format : str, optional
            Format of the date provided in the event_date column, by default "%Y-%m-%d".
            Refer to datetime standard library for more details date_format: 
            https://docs.python.org/2/library/datetime.html#strftime-strptime-behavior
        keep_model : bool, optional
            If true the model used to compute each single event study will be stored in memory.
            They will be accessible through the class attributes eventStudy.Multiple.singles[n].model, by default False
        ignore_errors : bool, optional
            If true, errors during the computation of single event studies will be ignored. 
            In this case, these events will be removed from the computation.
            However, a warning message will be displayed after the computation to warn for errors. 
            Errors can also be accessed using `print(eventstudy.Multiple.error_report())`.
            If false, the computation will be stopped by any error encounter 
            during the computation of single event studies, by default True
            
        See also
        --------
        
        from_text, from_list

        Example
        -------

        >>> agg = eventstudy.Multiple.from_csv(
        ...     path = 'events.csv',
        ...     event_study_model = eventstudy.Single.market_model,
        ...     event_window = (-5,+10),
        ...     date_format = "%d/%m/%Y"
        ... ) 
        """

        event_list = read_csv(
            path,
            format_date=True,
            date_format=date_format,
            date_column="event_date",
            row_wise=True,
        )

        return cls.from_list(
            event_list,
            event_study_model,
            event_window,
            estimation_size,
            buffer_size,
            keep_model=keep_model,
            ignore_errors=ignore_errors,
        )

    def __warn_errors(self):
        if self.errors is not None:
            nb = len(self.errors)
            if nb > 0:
                if nb > 1:
                    msg = (
                        f" {str(nb)} events have not been processed due to data issues."
                    )
                else:
                    msg = f"One event has not been processed due to data issues."

                msg += (
                    "\nTips: Get more details on errors by calling Multiple.error_report() method"
                    " or by exploring Multiple.errors class variable."
                )
                logging.warning(msg)

    def error_report(self):
        """
        Return a report of errors faced during the computation of event studies.

        Example
        -------
        
        >>> agg = eventstudy.Multiple.from_csv(
        ...     path = 'events.csv',
        ...     event_study_model = eventstudy.Single.market_model
        ... )
        >>> print(agg.error_report())
        """

        if self.errors is not None and len(self.errors) > 0:
            nb = (
                f"One error"
                if len(self.errors) == 1
                else f"{str(len(self.errors))} errors"
            )
            report = f"""Error Report
============

{nb} due to data unavailability.
The respective events was not processed and thus removed from the sample.
It does not affect the computation of other events.

Help 1: Check if the company was quoted at this date, 
Help 2: For event study modelised used Fama-French models,
        check if the Fama-French dataset imported is up-to-date.
Tips:   Re-import all parameters and re-run the event study analysis.

Details
=======
(You can find more details on errors in the documentation.)

"""

            table = list()
            lengths = {"error_type": 5, "date": 5, "error_msg": 0, "parameters": 11}

            for error in self.errors:
                # to preserve the instance errors variable from being modified
                error = error.copy()
                cells = {
                    "error_type": str(error.pop("error_type")),
                    "date": str(error.pop("event_date")),
                    "error_msg": str(error.pop("error_msg")),
                    "parameters": "; ".join(
                        [f"{str(key)}: {str(value)}" for key, value in error.items()]
                    ),
                }
                table.append(cells)

                for key, cell in cells.items():
                    if len(cell) > lengths[key]:
                        lengths[key] = len(cell)

            header = (
                "Error".ljust(lengths["error_type"])
                + " Date".ljust(lengths["date"])
                + "  Parameters".ljust(lengths["parameters"])
                + "\n"
            )
            mid_rule = (
                "-" * lengths["error_type"]
                + " "
                + "-" * lengths["date"]
                + " "
                + "-" * lengths["parameters"]
            )
            table_str = ""
            for cells in table:
                table_str += (
                    "\n"
                    + f"{cells['error_type']}".ljust(lengths["error_type"])
                    + " "
                    + f"{cells['date']}".ljust(lengths["date"])
                    + " "
                    + f"{cells['parameters']}".ljust(lengths["parameters"])
                    + "\nDescription: "
                    + cells["error_msg"]
                    + "\n"
                )

            report += header + mid_rule + table_str + mid_rule

            return report

        else:
            return "No error."
