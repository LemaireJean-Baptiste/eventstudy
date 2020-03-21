# where the return of a security is explain by a market index
#  (which can be different for each event), 
#  dummy variables for the month effect, 
# descriptive variable on the board (parity level, nb of independent director, average number of year in mandate,...).
# 
def custom_model(security_returns,
                market_returns,
                month,
                board_parity,
                nb_indep_dir,
                avg_mandate,
                *,  # Named arguments only
                estimation_size: int,
                event_window_size: int,
                keep_model: bool = False):

    residuals, df, var_res, model = Model(
        estimation_size = estimation_size,
        event_window_size = event_window_size,
        keep_model = True).OLS(
            X = market_returns,
            Y = [
                market_returns,
                month, # we need to create 11 columns for each month except one.
                board_parity,
                nb_indep_dir,
                avg_mandate
            ]
        )
    if keep_model:
       return residuals, df, var_res, model

    return residuals, df, var_res


import eventstudy as es

#### SINGLE EVENT BASED ON CUSTOM MODEL

# the data of the event should be a dictionary matching the model's function parameter
data = {
    'security_returns': your_data['security'],
    'market_returns': your_data['market'],
    'month': your_data['month'],
    'board_parity': your_data['parity'],
    'nb_indep_dir': your_data['nb_indep_dir'],
    'avg_mandate': your_data['avg_mandate'],
}

# compute the event study based on your custom_model and data
event = es.Single(
    model_func = custom_model,
    model_data = data,
    event_window = (-5, +10),
    estimation_size = 300,
    buffer_size = 20,
    event_date = np.datetime64('2012-02-13')
)
# run the event results and plot functions..
event.results()
event.plot()

#### MULTIPLE EVENTS BASED ON CUSTOM MODEL
# for multiple events the easiest now is to code your own loop

# create the database of the list of events, with the event date and the data to be feed in the model
# the data should be a dictionary matching the model's function parameter
event_list = [
    {'event_date':'2014-02-01', 'data':data_1},
    {'event_date':'2016-03-12', 'data':data_2},
    {'event_date':'2008-02-01', 'data':data_3},
    {'event_date':'2005-12-22', 'data':data_4},
    {'event_date':'2006-05-01', 'data':data_5},
    ...
]

# create a list to contain all events computed in the lopp
sample = list()
for event in event_list:
    # run each event and save it in the sample
    sample.append(
        es.Single(
            model_func = custom_model,
            model_data = event['data'],
            event_window = (-5, +10),
            estimation_size = 300,
            buffer_size = 20,
            event_date = np.datetime64(event['event_date'])
        )
    )

# run the Multiple events computation by passing the sample to the Multiple Class
events = es.Multiple(sample)
# then run the results, plot and so on
events.results()
events.plot()