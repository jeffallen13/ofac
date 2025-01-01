'''
OFAC historical reconiliation: first step in Python redesign
'''

from ofac.historical_recon import reconcile_historical_data, create_panel

df = reconcile_historical_data(data_dir='data')

df.to_csv('data/ofac_list.csv', index=False)

panel = create_panel(df)

panel.to_csv('data/ofac_panel.csv', index=False)
