import numpy as np
import matplotlib.pyplot as plt

import eventstudy as es

es.EventStudy.import_returns('returns_small.csv')
es.EventStudy.import_FamaFrench('famafrench.csv')

AAPL_10K = es.EventStudyBatch.from_csv('AAPL_10K.csv', es.EventStudy.FamaFrench_3factor, date_format = '%d/%m/%Y')
AAPL_10K.print_errors()

AAPL_10K.plot()
plt.show()
print(AAPL_10K.results())

#security_returns = [np.random.normal() for i in range(1000)]
#market_returns = [np.random.normal() for i in range(1000)]
#riskFreeReturns = [np.random.normal() for i in range(1000)]
#SMB = [np.random.normal() for i in range(1000)]
#HML = [np.random.normal() for i in range(1000)]
#
#testMM=EventStudy(
#            market_model,
#            {'security_returns':security_returns,'market_returns':market_returns},
#            event_window = (-10,+10),
#            estimation_size = 300,
#            buffer_size= 30,
#            keep_model = False)
#testMM.to_excel('testMM.xlsx', chart_as_picture=True)
#testMM.to_excel('testMMC.xlsx')
#testFF = EventStudy(FamaFrench_3factor,
#            {
#                'security_returns':security_returns,
#                'market_returns':market_returns,
#                'riskFreeReturns':riskFreeReturns,
#                'SMB':SMB,
#                'HML':HML,
#            },
#            event_window = (-10,+300),
#            estimation_size = 300,
#            buffer_size= 30,
#            keep_model = False)
#
#testFF.to_excel('testFF.xlsx', chart_as_picture=True)
#testFF.to_excel('testFFC.xlsx')
#testCM = EventStudy(constant_mean,
#            {
#                'security_returns':security_returns,
#            },
#            event_window = (-10,+10),
#            estimation_size = 300,
#            buffer_size= 30,
#            keep_model = False)
#
#testCM.to_excel('testCM.xlsx', chart_as_picture=True)
#testCM.to_excel('testCMC.xlsx')