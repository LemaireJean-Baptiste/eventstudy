```eval_rst

Multiple Class
================

.. automodule:: eventstudy.Multiple

.. contents::
    :local:
    :depth: 1

Run the event study
-------------------

.. autosummary::
   :nosignatures:
   :toctree:

    eventstudy.Multiple.__init__
    eventstudy.Multiple.from_csv
    eventstudy.Multiple.from_list
    eventstudy.Multiple.from_text
    eventstudy.Multiple.error_report

Import data
-----------

.. note:: Returns and factor data are directly imported at the single event study level.

.. autosummary::
   :nosignatures:
   :toctree:

    eventstudy.Single.import_FamaFrench
    eventstudy.Single.import_returns
    eventstudy.Single.import_returns_from_API


Retrieve results
----------------

.. autosummary::
   :nosignatures:
   :toctree:

    eventstudy.Multiple.plot
    eventstudy.Multiple.results
    eventstudy.Multiple.get_CAR_dist
    eventstudy.Multiple.sign_test
    eventstudy.Multiple.rank_test

```