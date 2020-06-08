# updating reports

Reports live in [./src/observer/reports.py](https://github.com/elifesciences/observer/blob/develop/src/observer/reports.py)
and query a database defined in [./src/observer/models.py](https://github.com/elifesciences/observer/blob/develop/src/observer/models.py).

Each report has a set of default parameters and configuration options.

1. Write a function that returns data. This is your 'report'.
2. Wrap your function in the `report` decorator with a dictionary of report metadata.
3. Reports querying `Article` data may use the `article_meta` function. It provides a dictionary of sensible metadata 
defaults for `Article` data.
4. Update the `known_report_idx` function with your new report function.
5. Regenerate the `README.md` file with `./regenerate-readme.md` to add report documentation.
