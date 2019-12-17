# Excel export
import xlsxwriter as xl
from .single import Single

import tempfile


def write_file(self, path, *, chart_as_picture=False):

    wb = xl.Workbook(path)
    ws = wb.add_worksheet("Summary")

    # Formats
    f_h1 = wb.add_format({"font_size": 15, "bold": 1})
    f_h2 = wb.add_format({"italic": 1})

    # Heading
    ws.write(0, 0, "Event study analysis", f_h1)

    # Table of results
    results = {
        "#": range(self.event_window[0], self.event_window[1] + 1),
        "AR": self.AR,
        "Variance AR": self.var_AR,
        "CAR": self.CAR,
        "Variance CAR": self.var_CAR,
        "T-stat": self.tstat,
        "P-value": self.pvalue,
    }
    last_row, last_col = print_table(wb, ws, 2, 0, results, "Table of results")

    # Display chart
    ws.write(2, last_col + 2, "Graph of CAR", f_h2)

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
                "categories": [ws.name, 4, 0, last_row, 0],
                "values": [ws.name, 4, 3, last_row, 3],
                "name": [ws.name, 3, 3],
                "line": {"width": 1},
            }
        )

        AR_chart = wb.add_chart({"type": "column"})
        AR_chart.add_series(
            {
                "categories": [ws.name, 4, 0, last_row, 0],
                "values": [ws.name, 4, 1, last_row, 1],
                "name": [ws.name, 3, 1],
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
    wb.close()


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


Single.to_excel = write_file
