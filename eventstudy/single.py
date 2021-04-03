from .utils import to_table, plot, read_csv, get_index_of_date
from .exception import (
    ParameterMissingError,
    DateMissingError,
    DataMissingError,
    ColumnMissingError,
)

import numpy as np
import statsmodels.api as sm
from scipy.stats import t

from .models import market_model, FamaFrench_3factor, FamaFrench_5factor, constant_mean


class Single:
    """
    Event Study package's core object. Implement the classical event study methodology [1]_ for a single event.
    This implementation heavily relies on the work of MacKinlay [2]_.

    References
    ----------

    .. [1] Fama, E. F., L. Fisher, M. C. Jensen, and R. Roll (1969). 
        “The Adjustment of Stock Prices to New Information”.
        In: International Economic Review 10.1, pp. 1–21.
    .. [2] Mackinlay, A. (1997). “Event Studies in Economics and Finance”.
        In: Journal of Economic Literature 35.1, p. 13.
    """

    _parameters = {
        "max_iteration": 4,
    }

    def __init__(
        self,
        model_func,
        model_data: dict,
        event_date: np.datetime64 = None,
        event_window: tuple = (-10, +10),
        estimation_size: int = 300,
        buffer_size: int = 30,
        keep_model: bool = False,
        description: str = None
    ):
        """
        Low-level (complex) way of runing an event study. Prefer the simpler use of model methods.

        Parameters
        ----------
        model_func
            Function computing the modelisation of returns.
        model_data : dict
            Dictionary containing all parameters needed by `model_func`.
        event_date : np.datetime64
            Date of the event in numpy.datetime64 format.
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
            If true the model used to compute the event study will be stored in memory.
            It will be accessible through the class attributes eventstudy.Single.model, by default False

        See also
        -------

        market_model, FamaFrench_3factor, constant_mean

        Example
        -------

        Run an event study based on :
        .. the `market_model` function defined in the `models` submodule,
        .. given values for security and market returns,
        .. and default parameters

        >>> from eventstudy import Single, models
        >>> event = Single(
        ...     models.market_model, 
        ...     {'security_returns':[0.032,-0.043,...], 'market_returns':[0.012,-0.04,...]}
        ... )
        """
        self.event_date = event_date
        self.event_window = event_window
        self.event_window_size = -event_window[0] + event_window[1] + 1
        self.estimation_size = estimation_size
        self.buffer_size = buffer_size
        self.description = description

        model = model_func(
            **model_data,
            estimation_size=self.estimation_size,
            event_window_size=self.event_window_size,
            keep_model=keep_model
        )

        if keep_model:
            self.AR, self.df, self.var_AR, self.model = model
        else:
            self.AR, self.df, self.var_AR = model

        self.__compute()

    def __compute(self):
        self.CAR = np.cumsum(self.AR)
        self.var_CAR = [(i * var) for i, var in enumerate(self.var_AR, 1)]
        self.tstat = self.CAR / np.sqrt(self.var_CAR)
        self.pvalue = 1.0 - t.cdf(abs(self.tstat), self.df)

    def results(self, asterisks: bool = True, decimals=3):
        """
        Return event study's results in a table format.
        
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
            AR and AR's variance, CAR and CAR's variance, T-stat and P-value, 
            for each T in the event window.

        Note
        ----
        
        The function return a fully working pandas DataFrame.
        All pandas method can be used on it, especially exporting method (to_csv, to_excel,...)

        Example
        -------

        Get results of a market model event study, with specific number of decimal for each column:

        >>> event = EventStudy.market_model(
        ...     security_ticker = 'AAPL',
        ...     market_ticker = 'SPY',
        ...     event_date = np.datetime64('2007-01-09'),
        ...     event_window = (-5,+5)
        ... )
        >>> event.results(decimals = [3,5,3,5,2,2])

        ====  ======  =============  =============  ==============  ========  =========
          ..      AR    Variance AR  CAR              Variance CAR    T-stat    P-value
        ====  ======  =============  =============  ==============  ========  =========
          -5  -0.053        0.00048  -0.053 \*\*           0.00048     -2.42       0.01
          -4   0.012        0.00048  -0.041 \*             0.00096     -1.33       0.09
          -3  -0.013        0.00048  -0.055 \*             0.00144     -1.43       0.08
          -2   0.004        0.00048  -0.051                0.00192     -1.15       0.13
          -1   0            0.00048  -0.051                0.00241     -1.03       0.15
           0  -0.077        0.00048  -0.128 \*\*           0.00289     -2.37       0.01
           1  -0.039        0.00048  -0.167 \*\*\*         0.00337     -2.88       0
           2   0.027        0.00048  -0.14 \*\*            0.00385     -2.26       0.01
           3   0.024        0.00048  -0.116 \*\*           0.00433     -1.77       0.04
           4  -0.024        0.00048  -0.14 \*\*            0.00481     -2.02       0.02
           5   0.023        0.00048  -0.117 \*             0.00529     -1.61       0.05
        ====  ======  =============  =============  ==============  ========  =========

        Note
        ----
        
        Significance level: \*\*\* at 99%, \*\* at 95%, \* at 90%
        """

        columns = {
            "AR": self.AR,
            "Std. E. AR": np.sqrt(self.var_AR),
            "CAR": self.CAR,
            "Std. E. CAR": np.sqrt(self.var_CAR),
            "T-stat": self.tstat,
            "P-value": self.pvalue,
        }

        asterisks_dict = {"pvalue": "P-value", "where": "CAR"} if asterisks else None

        return to_table(
            columns,
            asterisks_dict=asterisks_dict,
            decimals=decimals,
            index_start=self.event_window[0],
        )

    def plot(self, *, AR=False, CI=True, confidence=0.90):
        """
        Plot the event study result.
        
        Parameters
        ----------
        AR : bool, optional
            Add to the figure a bar plot of AR, by default False
        CI : bool, optional
            Display the confidence interval, by default True
        confidence : float, optional
            Set the confidence level, by default 0.90
        
        Returns
        -------
        matplotlib.figure
            Plot of CAR and AR (if specified).

        Note
        ----
        The function return a fully working matplotlib function.
        You can extend the figure and apply new set-up with matplolib's method (e.g. savefig).
        
        Example
        -------

        Plot CAR (in blue) and AR (in black), with a confidence interval of 95% (in grey).

        >>> event = EventStudy.market_model(
        ...     security_ticker = 'AAPL',
        ...     market_ticker = 'SPY',
        ...     event_date = np.datetime64('2007-01-09'),
        ...     event_window = (-5,+20)
        ... )
        >>> event.plot(AR = True, confidence = .95)

        .. image:: /_static/single_event_plot.png
        """

        return plot(
            time=range(self.event_window[0], self.event_window[1] + 1),
            CAR=self.CAR,
            AR=self.AR if AR else None,
            CI=CI,
            var=self.var_CAR,
            df=self.df,
            confidence=confidence,
        )

    @classmethod
    def _save_parameter(cls, param_name: str, data):
        cls._parameters[param_name] = data

    @classmethod
    def _get_parameters(
        cls,
        param_name: str,
        columns: tuple,
        event_date: np.datetime64,
        event_window: tuple = (-10, +10),
        estimation_size: int = 300,
        buffer_size: int = 30,
    ) -> tuple:

        # Find index of returns
        try:
            event_i = get_index_of_date(
                cls._parameters[param_name]["date"],
                event_date,
                cls._parameters["max_iteration"],
            )
        except KeyError:
            raise ParameterMissingError(param_name)

        if event_i is None:
            raise DateMissingError(event_date, param_name)

        start = event_i - (-event_window[0] + buffer_size + estimation_size)
        end = event_i + event_window[1] + 1
        size = -event_window[0] + buffer_size + estimation_size + event_window[1] + 1

        results = list()
        for column in columns:
            try:
                result = cls._parameters[param_name][column][start:end]
            except KeyError:
                raise ColumnMissingError(param_name, column)

            # test if all data has been retrieved
            if len(result) != size:
                raise DataMissingError(param_name, column, len(result), start + end)

            results.append(result)

        return tuple(results)

    @classmethod
    def import_returns(
        cls,
        path: str,
        *,
        is_price: bool = False,
        log_return: bool = True,  # if False, percentage change will be computed
        date_format: str = "%Y-%m-%d"
    ):
        """
        Import returns from a csv file to the `Single` Class parameters.
        Once imported, the returns are shared among all `Single` instances.
        
        Parameters
        ----------
        path : str
            Path to the returns' csv file
        is_price : bool, optional
            Specify if the file contains price (True) or returns (False), by default False. 
            If set at True, the function will convert prices to returns.
        log_return : bool, optional
            Specify if returns must be computed as log returns (True) 
            or percentage change (False), by default True.
            Only used if `is_price`is set to True.
        date_format : str, optional
            Format of the date provided in the csv file, by default "%Y-%m-%d".
            Refer to datetime standard library for more details date_format: 
            https://docs.python.org/2/library/datetime.html#strftime-strptime-behavior
        """
        data = read_csv(path, format_date=True, date_format=date_format)

        if is_price:
            for key in data.keys():
                if key != "date":
                    if log_return:
                        data[key] = np.diff(np.log(data[key]))
                    else:
                        data[key] = np.diff(data[key]) / data[key][1:]
                else:
                    data[key] = data[key][1:] #remove the first date

        cls._save_parameter("returns", data)

    @classmethod
    def import_returns_from_API(cls):
        pass

    @classmethod
    def import_FamaFrench(
        cls, path: str, *, rescale_factor: bool = True, date_format: str = "%Y%m%d"
    ):
        """
        Import Fama-French factors from a csv file to the `Single` Class parameters.
        Once imported, the factors are shared among all `Single` instances.
        
        Parameters
        ----------
        path : str
            Path to the factors' csv file
        rescale_factor : bool, optional
            Divide by 100 the factor provided, by default True,
            Fama-French factors are given in percent on Kenneth R. French website.
        date_format : str, optional
            Format of the date provided in the csv file, by default "%Y-%m-%d".
            Refer to datetime standard library for more details date_format: 
            https://docs.python.org/2/library/datetime.html#strftime-strptime-behavior
        """

        data = read_csv(path, format_date=True, date_format=date_format)

        if rescale_factor:
            for key in data.keys():
                if key != "date":
                    data[key] = np.array(data[key]) / 100

        cls._save_parameter("FamaFrench", data)

    @classmethod
    def market_model(
        cls,
        security_ticker: str,
        market_ticker: str,
        event_date: np.datetime64,
        event_window: tuple = (-10, +10),
        estimation_size: int = 300,
        buffer_size: int = 30,
        keep_model: bool = False,
        **kwargs
    ):
        """
        Modelise returns with the market model.
        
        Parameters
        ----------
        security_ticker : str
            Ticker of the security (e.g. company stock) as given in the returns imported.
        market_ticker : str
            Ticker of the market (e.g. market index) as given in the returns imported.
        event_date : np.datetime64
            Date of the event in numpy.datetime64 format.
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
            If true the model used to compute the event study will be stored in memory.
            It will be accessible through the class attributes eventstudy.Single.model, by default False
        **kwargs
            Additional keywords have no effect but might be accepted to avoid freezing 
            if there are not needed parameters specified.
        
        See also
        -------
        
        FamaFrench_3factor, constant_mean

        Example
        -------

        Run an event study for the Apple company for the announcement of the first iphone,
        based on the market model with the S&P500 index as a market proxy.

        >>> event = EventStudy.market_model(
        ...     security_ticker = 'AAPL',
        ...     market_security = 'SPY',
        ...     event_date = np.datetime64('2007-01-09'),
        ...     event_window = (-5,+20)
        ... )
        """
        security_returns, market_returns = cls._get_parameters(
            "returns",
            (security_ticker, market_ticker),
            event_date,
            event_window,
            estimation_size,
            buffer_size,
        )
        description = f"Market model estimation, Security: {security_ticker}, Market: {market_ticker}"

        return cls(
            market_model,
            {"security_returns": security_returns, "market_returns": market_returns},
            event_window=event_window,
            estimation_size=estimation_size,
            buffer_size=buffer_size,
            keep_model=keep_model,
            description= description,
            event_date=event_date
        )

    @classmethod
    def constant_mean(
        cls,
        security_ticker,
        event_date: np.datetime64,
        event_window: tuple = (-10, +10),
        estimation_size: int = 300,
        buffer_size: int = 30,
        keep_model: bool = False,
        **kwargs
    ):
        """
        Modelise returns with the constant mean model.
        
        Parameters
        ----------
        security_ticker : str
            Ticker of the security (e.g. company stock) as given in the returns imported.
        event_date : np.datetime64
            Date of the event in numpy.datetime64 format.
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
            If true the model used to compute the event study will be stored in memory.
            It will be accessible through the class attributes eventstudy.Single.model, by default False
        **kwargs
            Additional keywords have no effect but might be accepted to avoid freezing 
            if there are not needed parameters specified.
            For example, if market_ticker is specified.
        
        See also
        -------
        market_model, Single.FamaFrench_3factor

        Example
        -------

        Run an event study for the Apple company for the announcement of the first iphone,
        based on the constant mean model.

        >>> event = EventStudy.constant_mean(
        ...     security_ticker = 'AAPL',
        ...     event_date = np.datetime64('2007-01-09'),
        ...     event_window = (-5,+20)
        ... )
        """
        # the comma after 'security_returns' unpack the one-value tuple returned by the function _get_parameters
        (security_returns,) = cls._get_parameters(
            "returns",
            (security_ticker,),
            event_date,
            event_window,
            estimation_size,
            buffer_size,
        )
        
        description = f"Constant mean estimation, Security: {security_ticker}"
        
        return cls(
            constant_mean,
            {"security_returns": security_returns},
            event_window=event_window,
            estimation_size=estimation_size,
            buffer_size=buffer_size,
            keep_model=keep_model,
            description=description,
            event_date=event_date 
        )

    @classmethod
    def FamaFrench_3factor(
        cls,
        security_ticker,
        event_date: np.datetime64,
        event_window: tuple = (-10, +10),
        estimation_size: int = 300,
        buffer_size: int = 30,
        keep_model: bool = False,
        **kwargs
    ):
        """
        Modelise returns with the Fama-French 3-factor model.
        The model used is the one developped in Fama and French (1992) [1]_.
        
        Parameters
        ----------
        security_ticker : str
            Ticker of the security (e.g. company stock) as given in the returns imported.
        event_date : np.datetime64
            Date of the event in numpy.datetime64 format.
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
            If true the model used to compute the event study will be stored in memory.
            It will be accessible through the class attributes eventstudy.Single.model, by default False
        **kwargs
            Additional keywords have no effect but might be accepted to avoid freezing 
            if there are not needed parameters specified.
            For example, if market_ticker is specified.
        
        See also
        -------
        market_model, constant_mean

        Example
        -------

        Run an event study for the Apple company for the announcement of the first iphone,
        based on the Fama-French 3-factor model.

        >>> event = EventStudy.FamaFrench_3factor(
        ...     security_ticker = 'AAPL',
        ...     event_date = np.datetime64('2007-01-09'),
        ...     event_window = (-5,+20)
        ... )

        References
        ----------
        .. [1] Fama, E. F. and K. R. French (1992). 
            “The Cross-Section of Expected Stock Returns”.
            In: The Journal of Finance 47.2, pp. 427–465.
        """

        (security_returns,) = cls._get_parameters(
            "returns",
            (security_ticker,),
            event_date,
            event_window,
            estimation_size,
            buffer_size,
        )
        Mkt_RF, SMB, HML, RF = cls._get_parameters(
            "FamaFrench",
            ("Mkt-RF", "SMB", "HML", "RF"),
            event_date,
            event_window,
            estimation_size,
            buffer_size,
        )
        
        description = f"Fama-French 3-factor model estimation, Security: {security_ticker}"
        
        return cls(
            FamaFrench_3factor,
            {
                "security_returns": security_returns,
                "Mkt_RF": Mkt_RF,
                "SMB": SMB,
                "HML": HML,
                "RF": RF,
            },
            event_window=event_window,
            estimation_size=estimation_size,
            buffer_size=buffer_size,
            keep_model=keep_model,
            description=description,
            event_date=event_date
        )

    @classmethod
    def FamaFrench_5factor(
        cls,
        security_ticker,
        event_date: np.datetime64,
        event_window: tuple = (-10, +10),
        estimation_size: int = 300,
        buffer_size: int = 30,
        keep_model: bool = False,
        **kwargs
    ):
        """
        Modelise returns with the Fama-French 5-factor model.
        The model used is the one developped in Fama and French (1992) [1]_.
        
        Parameters
        ----------
        security_ticker : str
            Ticker of the security (e.g. company stock) as given in the returns imported.
        event_date : np.datetime64
            Date of the event in numpy.datetime64 format.
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
            If true the model used to compute the event study will be stored in memory.
            It will be accessible through the class attributes eventstudy.Single.model, by default False
        **kwargs
            Additional keywords have no effect but might be accepted to avoid freezing 
            if there are not needed parameters specified.
            For example, if market_ticker is specified.
        
        See also
        -------
        market_model, constant_mean

        Example
        -------

        Run an event study for the Apple company for the announcement of the first iphone,
        based on the Fama-French 5-factor model.

        >>> event = EventStudy.FamaFrench_5factor(
        ...     security_ticker = 'AAPL',
        ...     event_date = np.datetime64('2007-01-09'),
        ...     event_window = (-5,+20)
        ... )

        References
        ----------
        .. [1] Fama, E. F. and K. R. French (1992). 
            “The Cross-Section of Expected Stock Returns”.
            In: The Journal of Finance 47.2, pp. 427–465.
        """

        (security_returns,) = cls._get_parameters(
            "returns",
            (security_ticker,),
            event_date,
            event_window,
            estimation_size,
            buffer_size,
        )
        Mkt_RF, SMB, HML, RMW, CMA, RF = cls._get_parameters(
            "FamaFrench",
            ("Mkt-RF", "SMB", "HML", "RMW", "CMA", "RF"),
            event_date,
            event_window,
            estimation_size,
            buffer_size,
        )
        
        description = f"Fama-French 5-factor model estimation, Security: {security_ticker}"
        
        return cls(
            FamaFrench_5factor,
            {
                "security_returns": security_returns,
                "Mkt_RF": Mkt_RF,
                "SMB": SMB,
                "HML": HML,
                "RMW": RMW,
                "CMA": CMA,
                "RF": RF,
            },
            event_window=event_window,
            estimation_size=estimation_size,
            buffer_size=buffer_size,
            keep_model=keep_model,
            description=description,
            event_date=event_date
        )
