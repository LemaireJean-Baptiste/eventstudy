# Excel export
try:
    import xlsxwriter as xl
except ImportError:
    import logging
    msg = """\
Package Missing: Please install the `xlsxwriter` package, using `pip install XlsxWriter`.
See xlsxwriter's documentation: https://xlsxwriter.readthedocs.io/
"""
    logging.warning(msg)
from .single import Single
from .multiple import Multiple

import tempfile
import numpy as np

def print_table(wb, ws, row: int, col: int, data: dict, title: str = None):
    f_title = wb.add_format({"italic": 1})
    f_header = wb.add_format({"bold": 1, "bottom": 1})

    if title:
        ws.write(row, col, title, f_title)
        row += 1

    maxLen = 0
    for key, values in data.items():
        ws.write(row, col, key, f_header)
        ws.write_column(row + 1, col, values)
        col += 1
        if len(values) > maxLen:
            maxLen = len(values)

    # last row and colum used
    last_row = maxLen + row
    last_col = col - 1
    return last_row, last_col

def write_summary(self, type:str, wb, sheet_name = 'summary', *, chart_as_picture: bool=False):
    ws = wb.add_worksheet(sheet_name)

    # Formats
    f_h1 = wb.add_format({"font_size": 15, "bold": 1})
    f_h2 = wb.add_format({"italic": 1})
    f_t_sum = wb.add_format({"bold": 1, "right": 1})

    # Heading
    ws.write(0, 0, "Event study analysis", f_h1)

    # Table Summary
    ws.write(0, 0, "Specification", f_h2)
    ws.write(2, 0, "Description", f_t_sum)
    if self.description:
        ws.write(2, 1, self.description)
    else:
        ws.write(2, 1, "no description")



    # Table of results
    if type == 'Single':
        ws.write(3, 0, "Event date", f_t_sum)
        ws.write(3, 1, np.datetime_as_string(self.event_date,))
        ws.write(4, 0, "Event window start", f_t_sum)
        ws.write(4, 1, self.event_window[0])
        ws.write(5, 0, "Event window end", f_t_sum)
        ws.write(5, 1, self.event_window[1])
        ws.write(6, 0, "Estimation size", f_t_sum)
        ws.write(6, 1, self.estimation_size)
        ws.write(6, 0, "Estimation size", f_t_sum)
        ws.write(6, 1, self.estimation_size)

        results = {
            "#": range(self.event_window[0], self.event_window[1] + 1),
            "AR": self.AR,
            "Variance AR": self.var_AR,
            "CAR": self.CAR,
            "Variance CAR": self.var_CAR,
            "T-stat": self.tstat,
            "P-value": self.pvalue,
        }
    elif type == 'Multiple':
        results = {
            "#": range(self.event_window[0], self.event_window[1] + 1),
            "AAR": self.AAR,
            "Variance AAR": self.var_AAR,
            "CAAR": self.CAAR,
            "Variance CAAR": self.var_CAAR,
            "T-stat": self.tstat,
            "P-value": self.pvalue,
        }

    last_row, last_col = print_table(wb, ws, 8, 0, results, "Table of results")

    # Display chart
    if type == 'Single': ws.write(2, last_col + 2, "Graph of CAR", f_h2)
    if type == 'Multiple': ws.write(2, last_col + 2, "Graph of CAAR", f_h2)

    if chart_as_picture:
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmpfile:
            self.plot(AR=True).savefig(
                tmpfile, format="png", pad_inches=0.05, bbox_inches="tight"
            )
            ws.insert_image(4, last_col + 2, tmpfile.name)
    else:
        CAR_chart = wb.add_chart({"type": "line"})
        CAR_chart.add_series(
            {
                "categories": [ws.name, 10, 0, last_row, 0],
                "values": [ws.name, 10, 3, last_row, 3],
                "name": [ws.name, 9, 3],
                "line": {"width": 1},
            }
        )

        AR_chart = wb.add_chart({"type": "column"})
        AR_chart.add_series(
            {
                "categories": [ws.name, 10, 0, last_row, 0],
                "values": [ws.name, 10, 1, last_row, 1],
                "name": [ws.name, 9, 1],
                "gap": 500,
                "fill": {"color": "#000000"},
            }
        )
        CAR_chart.combine(AR_chart)
        CAR_chart.set_x_axis(
            {
                "position_axis": "on_tick",
                "major_tick_mark": "none",
                "line": {"color": "black"},
                "label_position": "low",
            }
        )
        CAR_chart.set_y_axis(
            {"major_gridlines": {"visible": False}, "line": {"color": "black"}}
        )
        CAR_chart.set_legend({"position": "bottom"})
        CAR_chart.set_plotarea({"border": {"color": "black", "width": 1}})
        ws.insert_chart(4, last_col + 2, CAR_chart)

def write_Single(self, path: str, *, chart_as_picture: bool=False, event_details: bool=True):
    wb = xl.Workbook(path)
    write_summary(self=self, type='Single', wb=wb, sheet_name = 'summary', chart_as_picture= chart_as_picture)
    wb.close()

def write_Multiple(self, path: str, *, chart_as_picture: bool=False, event_details: bool=True):
    wb = xl.Workbook(path)
    write_summary(self=self, type='Multiple', wb=wb, sheet_name = 'summary', chart_as_picture= chart_as_picture)
    for i, event in enumerate(self.sample, 1):
        write_summary(self=event, type='Single', wb=wb, sheet_name = 'event_'+str(i), chart_as_picture= chart_as_picture)
    wb.close()

Single.to_excel = write_Single
Multiple.to_excel = write_Multiple
