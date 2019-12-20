# Excel export

If needed, you can export your results to excel directly using the `excelExporter` module.

## Prerequisite

To use the excel export functionalities, you must first install [`XlsxWriter`](https://xlsxwriter.readthedocs.io/) with the following command-line.

```bash
$ pip install XlsxWriter
```

Then add the following import statement at the beginning of your python script:

```python
import eventstudy as es
from eventstudy import excelExporter
```

The last line will attach to the `eventstudy.Single` and `eventstudy.Multiple` classes a new function: `.to_excel()`.

## Usage

lorem...