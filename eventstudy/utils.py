import numpy as np
import pandas as pd
from scipy.stats import t

import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator

from collections import defaultdict
from csv import DictReader

# All model must returns : (residuals: list, df: int, var: float)

# TODO: sortir la computation des résiduals des fonctions de modélisation. Juste leur faire calculer les prédictions. Sortir aussi windowsize estimation size et tout le reste, et aussi le secReturns qui doit être rataché à l'event study pas la fonction de modélisation.

def to_table(columns, asterisks_dict=None, decimals=None, index_start=0):

    if decimals:
        if type(decimals) is int:
            decimals = [decimals] * len(columns)

        for key, decimal in zip(columns.keys(), decimals):
            if decimal:
                columns[key] = np.round(columns[key], decimal)

    if asterisks_dict:
        columns[asterisks_dict["where"]] = map(
            add_asterisks, columns[asterisks_dict["pvalue"]], columns[asterisks_dict["where"]]
        )

    df = pd.DataFrame.from_dict(columns)
    df.index += index_start
    return df


def add_asterisks(pvalue, value=None):
    if value == None:
        value = pvalue

    if pvalue < 0.01:
        asterisks = f"{str(value)} ***"
    elif pvalue < 0.05:
        asterisks = f"{str(value)} **"
    elif pvalue < 0.1:
        asterisks = f"{str(value)} *"
    else:
        asterisks = f"{str(value)}"
    return asterisks


def plot(time, CAR, *, AR=None, CI=False, var=None, df=None, confidence=0.90):

    fig, ax = plt.subplots()
    ax.plot(time, CAR)
    ax.axvline(
        x=0, color="black", linewidth=0.5,
    )
    ax.xaxis.set_major_locator(MaxNLocator(integer=True))

    if CI:
        delta = np.sqrt(var) * t.ppf(confidence, df)
        upper = CAR + delta
        lower = CAR - delta
        ax.fill_between(time, lower, upper, color="black", alpha=0.1)

    if AR is not None:
        ax.vlines(time, ymin=0, ymax=AR)

    if ax.get_ylim()[0] * ax.get_ylim()[1] < 0:
        # if the y axis contains 0
        ax.axhline(y=0, color="black", linewidth=0.5, linestyle="--")

    return fig


def get_index_of_date(data, date: np.datetime64, n: int = 4):
    # assume the date exist and there is only one of it in the dataset
    # assume date are in index

    for i in range(n + 1):
        index = np.where(data == date)[0]
        if len(index) > 0:
            return index[0]
        else:
            date = date + np.timedelta64(1, "D")

    # return None if there is no row corresponding to this date or n days after.
    return None


def OLD_read_csv(path):
    data = defaultdict(list)
    with open("./returns.csv", "r") as f:
        reader = DictReader(f)
        for row in reader:
            for col, value in row.items():
                data[col].append(value)

    return data


def read_csv(
    path,
    format_date: bool = False,
    date_format: str = "%Y-%m-%d",
    date_column: str = "date",
    row_wise: bool = False,
):

    df = pd.read_csv(path, skipinitialspace=True)

    if format_date:
        df[date_column] = pd.to_datetime(df[date_column], format=date_format)

    if row_wise:
        data = list()
        for row in df.itertuples(index=False):
            row = dict(row._asdict())
            if format_date:
                row[date_column] = np.datetime64(row[date_column])
            data.append(row)
    else:  # column_wise
        data = dict()
        for col in df.columns:
            data[col] = df[col].values

    return data
