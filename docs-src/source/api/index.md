# API

The package implements two classes [`Single`](eventstudy.Single) and [`Multiple`](eventstudy.Multiple)
to compute event studies respectively on single events (with measures such as Abnormal Returns (AR)
and Cumulative Abnormal Returns (CAR)) and on aggregates of events (with measures such as 
Average Abnormal Returns (AAR) and Cumulative Abnormal Returns (CAAR)).

The second class ([`Multiple`](eventstudy.Multiple)) relies on the first one ([`Single`](eventstudy.Single)) 
as it basically performs a loop of single event studies and then aggregates them.

```eval_rst
.. toctree::
   :maxdepth: 1
   :titlesonly:
   :glob:

   For a single event <eventstudy.Single>
   For an aggregate of events <eventstudy.Multiple>
```