```eval_rst
.. currentmodule:: eventstudy.EventStudy

EventStudy Class
================

Event Study core object. Implement the classical event study methodology [1]_ for a single event.
This implementation heavily rely on the work of MacKinlay [2]_.

.. contents::
    :local:
    :depth: 1

Run the event study
-------------------

.. autosummary::
   :nosignatures:
   :toctree:

    eventstudy.EventStudy
    eventstudy.EventStudy.market_model
    eventstudy.EventStudy.constant_mean
    eventstudy.EventStudy.FamaFrench_3factor


Import data
-----------

.. autosummary::
   :nosignatures:
   :toctree:

    eventstudy.EventStudy.import_FamaFrench
    eventstudy.EventStudy.import_returns
    eventstudy.EventStudy.import_returns_from_API


Retrieve results
----------------

.. autosummary::
   :nosignatures:
   :toctree:

    eventstudy.EventStudy.plot
    eventstudy.EventStudy.results


References
----------

.. [1] Fama, E. F., L. Fisher, M. C. Jensen, and R. Roll (1969). 
    “The Adjustment of Stock Prices to New Information”.
    In: International Economic Review 10.1, pp. 1–21.
.. [2] Mackinlay, A. (1997). “Event Studies in Economics and Finance”.
    In: Journal of Economic Literature 35.1, p. 13.

```