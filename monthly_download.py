'''
Downloads and processes OFAC sanctions data at the end of each month
Last updated: 10/31/2025
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
import matplotlib.pyplot as plt

ofac_panel = pd.read_csv('data/ofac_panel.csv', parse_dates=['Date'])

plot_ofac_series(ofac_panel, country='Russia', var='levels')

plt.savefig('images/ofac_russia.png', bbox_inches='tight')
