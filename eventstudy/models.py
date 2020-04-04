import numpy as np
import statsmodels.api as sm


class Model:

    """
    This 'Model' Class contains utils to run the modelisation of returns.
    It can be used inside modelisation function.
    A modelisation function takes the data needed to compute the model as parameters
    and additionally must also takes as named parameters:
        estimation_size: int,
        event_window_size: int,
        keep_model:bool = False
    
    A modelisation function must return (in this order):
        residuals of the eventWindow: as an array (vector)
        degree of freedom: as an integer
        variance of the residuals: as an array (vector) of the same size than the residuals vector
    """

    def __init__(
        self, estimation_size: int, event_window_size: int, keep_model: bool = False
    ):

        self.estimation_size = estimation_size
        self.event_window_size = event_window_size
        self.keep_model = keep_model

    def OLS(self, X, Y):

        X = sm.add_constant(X)  # add an intercept
        reg = sm.OLS(Y[: self.estimation_size], X[: self.estimation_size]).fit()
        residuals = np.array(Y) - reg.predict(X)
        df = self.estimation_size - 1
        var = np.var(residuals[: self.estimation_size])
        if self.keep_model:
            return residuals[-self.event_window_size :], df, var, reg

        return residuals[-self.event_window_size :], df, var


def market_model(
    security_returns,
    market_returns,
    *,  # Named arguments only
    estimation_size: int,
    event_window_size: int,
    keep_model: bool = False,
    **kwargs
):
    if keep_model:
        residuals, df, var_res, model = Model(estimation_size, event_window_size, keep_model).OLS(
            market_returns, security_returns
        )
        var = [var_res] * event_window_size

        return residuals, df, var, model
    else:
        residuals, df, var_res = Model(estimation_size, event_window_size, keep_model).OLS(
            market_returns, security_returns
        )
        var = [var_res] * event_window_size

        return residuals, df, var

    # var = var_res + 1/estimation_size * (1 +
    #    ( (np.array(market_returns)[-event_window_size:] - np.mean(market_returns[:estimation_size]) )**2)
    #     /np.var(market_returns[:estimation_size]))


def FamaFrench_3factor(
    security_returns,
    Mkt_RF,
    SMB,
    HML,
    RF,
    *,  # Named arguments only
    estimation_size: int,
    event_window_size: int,
    keep_model: bool = False,
    **kwargs
):

    RF = np.array(RF)
    Mkt_RF = np.array(Mkt_RF)
    security_returns = np.array(security_returns)

    X = np.column_stack((Mkt_RF, SMB, HML))
    Y = np.array(security_returns) - np.array(RF)

    if keep_model:
        residuals, df, var_res, model = Model(estimation_size, event_window_size, keep_model).OLS(
            X, Y
        )

        var = [var_res] * event_window_size

        return residuals, df, var, model
    else:
        residuals, df, var_res = Model(estimation_size, event_window_size, keep_model).OLS(
            X, Y
        )

        var = [var_res] * event_window_size

        return residuals, df, var


def constant_mean(
    security_returns,
    *,  # Named arguments only
    estimation_size: int,
    event_window_size: int,
    keep_model: bool = False,
    **kwargs
):

    mean = np.mean(security_returns[:estimation_size])
    residuals = np.array(security_returns) - mean
    df = estimation_size - 1
    var = [np.var(residuals)] * event_window_size

    if keep_model:
        return residuals[-event_window_size:], df, var, mean
    else:
        return residuals[-event_window_size:], df, var


def FamaFrench_5factor(
    security_returns,
    Mkt_RF,
    SMB,
    HML,
    RMW,
    CMA,
    RF,
    *,  # Named arguments only
    estimation_size: int,
    event_window_size: int,
    keep_model: bool = False,
    **kwargs
):

    RF = np.array(RF)
    Mkt_RF = np.array(Mkt_RF)
    security_returns = np.array(security_returns)

    X = np.column_stack((Mkt_RF, SMB, HML, RMW, CMA))
    Y = np.array(security_returns) - np.array(RF)

    if keep_model:
        residuals, df, var_res, model = Model(estimation_size, event_window_size, keep_model).OLS(
            X, Y
        )

        var = [var_res] * event_window_size

        return residuals, df, var, model
    else:
        residuals, df, var_res = Model(estimation_size, event_window_size, keep_model).OLS(
            X, Y
        )

        var = [var_res] * event_window_size

        return residuals, df, var