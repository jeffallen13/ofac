'''
Downloads and processes OFAC sanctions data at the end of each month
'''

from ofac import OFACProcessor

processor = OFACProcessor()

ofac_list = processor.update_ofac_list()

ofac_list.to_csv('data/ofac_list.csv', index=False)

ofac_panel = processor.create_panel(ofac_list)

ofac_panel.to_csv('data/ofac_panel.csv', index=False)

# Example plot

from ofac import plot_ofac_series
import pandas as pd

ofac_panel = pd.read_csv('data/ofac_panel.csv', parse_dates=['Date'])

plot_ofac_series(ofac_panel, country='Russia', var='levels')


