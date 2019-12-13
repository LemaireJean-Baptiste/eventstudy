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


class EventStudyBatch:
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

    def results(self, stars: bool = True, decimals=3):
        columns = {
            "AAR": self.AAR,
            "Variance AAR": self.var_AAR,
            "CAAR": self.CAAR,
            "Variance CAAR": self.var_CAAR,
            "T-stat": self.tstat,
            "P-value": self.pvalue,
        }

        star_dict = {"pvalue": "P-value", "where": "CAR"} if stars else None

        return to_table(
            columns,
            star=star_dict,
            decimals=decimals,
            index_start=self.event_window[0],
        )

    def plot(self, *, AR=False, CI=True, confidence=0.90):
        return plot(
            time=range(self.event_window[0], self.event_window[1] + 1),
            CAR=self.CAAR,
            AR=self.AAR if AR else None,
            CI=CI,
            var=self.var_CAAR,
            df=self.df,
            confidence=confidence,
        )

    def get_CAR_dist(self, decimals=3):
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
