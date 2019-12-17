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
from scipy.stats import t, kurtosis
import datetime


class Multiple:
    def __init__(self, sample, errors=None):
        self.errors = errors
        self.__warn_errors()

        # retrieve common parameters from the first occurence in eventStudies:
        self.event_window = sample[0].event_window
        self.event_window_size = sample[0].event_window_size

        self.__compute(sample)
        self.CAR = [event.CAR[-1] for event in sample]

    # def __computeByCAR(self, sample):
    #    # Deprecated, works, gives the same results than __compute but without AAR computation (which can be needed)
    #    # So gives less information
    #    self.CAAR = 1/len(sample) * np.sum([event.CAR for event in sample], axis=0)
    #    self.var_CAAR = (1/(len(sample)**2)) * np.sum([event.var_CAR for event in sample], axis=0)

    def __compute(self, sample):
        self.AAR = 1 / len(sample) * np.sum([event.AR for event in sample], axis=0)
        self.var_AAR = (1 / (len(sample) ** 2)) * np.sum(
            [event.var_AR for event in sample], axis=0
        )
        self.CAAR = np.cumsum(self.AAR)
        self.var_CAAR = [
            np.sum(self.var_AAR[:i]) for i in range(1, self.event_window_size + 1)
        ]

        self.tstat = self.CAAR / np.sqrt(self.var_CAAR)
        self.df = np.sum([event.df for event in sample], axis=0)
        self.pvalue = 1.0 - t.cdf(abs(self.tstat), self.df)

        self.CAR_dist = self.__compute_CAR_dist(sample)

    def __compute_CAR_dist(self, sample):
        CAR = [event.CAR for event in sample]
        CAR_dist = {
            "Mean": np.mean(CAR, axis=0),
            "Variance": np.var(CAR, axis=0),
            "Kurtosis": kurtosis(CAR, axis=0),
            "Min": np.min(CAR, axis=0),
            "Quantile 25%": np.quantile(CAR, q=0.25, axis=0),
            "Quantile 50%": np.quantile(CAR, q=0.5, axis=0),
            "Quantile 75%": np.quantile(CAR, q=0.75, axis=0),
            "Max": np.max(CAR, axis=0),
        }
        return CAR_dist

    def sign_test(self, sign="positive", confidence=0.9):
        # signtest
        # return nonParametricTest(self.CAR).signTest(sign, confidence)
        pass

    def rank_test(self, confidence):
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

        Get results of a market model event study on a 
        sample of events (Apple Inc. 10-K release) imported 
        from a csv, with specific number of decimal for each column:

        >>> events = es.Sample.from_csv(
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
            "Variance AAR": self.var_AAR,
            "CAAR": self.CAAR,
            "Variance CAAR": self.var_CAAR,
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

        >>> events = es.Sample.from_csv(
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

        Get CARs' descriptive statistics  of a market model event study on a 
        sample of events (Apple Inc. 10-K release) imported 
        from a csv, with specific number of decimal for each column:

        >>> events = es.Sample.from_csv(
        ...     'AAPL_10K.csv',
        ...     es.Single.FamaFrench_3factor,
        ...     event_window = (-5,+5),
        ...     date_format = '%d/%m/%Y'
        ... )
        >>> events.get_CAR_dist(decimals = 4)

        ====  ======  ==========  ==========  ======  ==============  ==============  ==============  =====
          ..    Mean    Variance    Kurtosis     Min    Quantile 25%    Quantile 50%    Quantile 75%    Max
        ====  ======  ==========  ==========  ======  ==============  ==============  ==============  =====
          -5  -0           0.001       0.061  -0.052          -0.014           0.001           0.015  0.047
          -4  -0.003       0.001       0.247  -0.091          -0.022           0.003           0.015  0.081
          -3   0.007       0.002       0.532  -0.082          -0.026           0.006           0.027  0.139
          -2   0.01        0.002      -0.025  -0.088          -0.021           0.002           0.033  0.115
          -1   0.018       0.003      -0.065  -0.091          -0.012           0.02            0.041  0.138
           0   0.018       0.003      -0.724  -0.084          -0.012           0.012           0.057  0.128
           1   0.012       0.004      -0.613  -0.076          -0.024           0.003           0.059  0.143
           2   0.017       0.005      -0.55   -0.117          -0.026           0.024           0.057  0.156
           3   0.018       0.005       0.289  -0.162          -0.032           0.027           0.057  0.17
           4   0.011       0.007       2.996  -0.282          -0.039           0.035           0.052  0.178
           5   0.012       0.008       1.629  -0.266          -0.05            0.035           0.064  0.174
        ====  ======  ==========  ==========  ======  ==============  ==============  ==============  =====

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
        text,
        event_study_model,
        event_window: tuple = (-10, +10),
        estimation_size: int = 300,
        buffer_size: int = 30,
        *,
        date_format: str = "%Y-%m-%d",
        keep_model: bool = False,
        ignore_errors: bool = True,
    ):

        # security_ticker, market_ticker, event_date
        # AAPL, SPY, 05/10/2019
        # MSFT, SPY, 05/10/2019
        # GOOG, SPY, 05/10/2019

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
        event_list,
        event_study_model,
        event_window: tuple = (-10, +10),
        estimation_size: int = 300,
        buffer_size: int = 30,
        *,
        keep_model: bool = False,
        ignore_errors: bool = True,
    ):

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
        keep_model: bool = False,
        *,
        date_format: str = "%Y%m%d",
        ignore_errors: bool = True,
    ):

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
                    "\nTips: Get more details on errors by calling EventStudyBatch.error_report() method"
                    " or by exploring EventStudyBatch.errors class variable."
                )
                logging.warning(msg)

    def error_report(self):
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
