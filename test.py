import eventstudy as es
import numpy as np
import matplotlib.pyplot as plt

es.Single.import_returns('example/returns_GAFAM.csv')
es.Single.import_FamaFrench('example/famafrench.csv')

event = es.Single.FamaFrench_3factor(
    security_ticker = 'AAPL',
    event_date = np.datetime64('2013-03-04'),
    event_window = (-2,+10), 
    estimation_size = 300,
    buffer_size = 30
)

#event.plot(AR=True)
#plt.show()

print(event.results(decimals=[3,5,3,5,2,2]))

release_10K = es.Multiple.from_csv(
    path = 'example/10K.csv', # the path to the csv file created
    event_study_model = es.Single.market_model,
    event_window = (-5,+10),
    estimation_size = 200,
    buffer_size = 30,
    date_format = '%d/%m/%Y',
    ignore_errors = True
)
#print(release_10K.error_report())

#release_10K.plot()
#plt.show()

print(release_10K.results(decimals=[3,5,3,5,2,2]))