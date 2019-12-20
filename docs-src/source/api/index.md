# API

The package implements two classes [`Single`](eventstudy.Single.md) and [`Multiple`](eventstudy.Multiple.md)
to compute event studies respectively on single events (with measures such as Abnormal Returns (AR)
and Cumulative Abnormal Returns (CAR)) and on aggregates of events (with measures such as 
Average Abnormal Returns (AAR) and Cumulative Abnormal Returns (CAAR)).

The second class ([`Multiple`](eventstudy.Multiple.md)) relies on the first one ([`Single`](eventstudy.Single.md)) 
as it basically performs a loop of single event studies and then aggregates them.

```eval_rst
.. toctree::
   :maxdepth: 2

   eventstudy.Single
   eventstudy.Multiple
   Excel export <eventstudy.excelExporter>
```

