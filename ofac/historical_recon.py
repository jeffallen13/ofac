'''
Process historical OFAC data for Python redevelopment in late 2024
'''

import pandas as pd
import numpy as np
import glob
import os

def reconcile_historical_data(data_dir='data'):
    """Process historical OFAC data preserving all entity relationships"""
    files = glob.glob(os.path.join(data_dir, 'ofac_full_*.csv'))
    files.sort()

    dfs = []
    for file in files:
        df = pd.read_csv(file)
        dfs.append(df)

    full_data = pd.concat(dfs, ignore_index=True)

    # Get first and last dates by Ent_num and Country
    date_ranges = (full_data.groupby(['Ent_num', 'Country'])['Rep_date']
                    .agg(['min', 'max'])
                    .reset_index()
                    .rename(columns={'min': 'add_date', 'max': 'last_date'}))

    # Remove duplicates keeping all info changes
    dedup_cols = [col for col in full_data.columns if col != 'Rep_date']
    unique_data = full_data.drop_duplicates(subset=dedup_cols, keep='first')

    # Merge date ranges
    unique_data = unique_data.merge(date_ranges, on=['Ent_num', 'Country'])

    # Get most recent date from files
    latest_date = files[-1].split('_')[-1].replace('.csv', '')

    # Set removal date as end of month after last appearance
    unique_data['removal_date'] = np.where(
        unique_data['last_date'] < latest_date,
        (pd.to_datetime(unique_data['last_date']) + pd.offsets.MonthEnd(1)).dt.strftime('%Y-%m-%d'),
        np.nan
    )

    # Clean up intermediate columns
    unique_data = unique_data.drop(['last_date'], axis=1)

    return unique_data

def create_panel(data):
    """Create panel showing entity counts and changes by country"""
    # First get distinct entity-country records using add_date
    base_records = (data[['Ent_num', 'Country', 'add_date', 'removal_date']]
                    .drop_duplicates())

    # Consolidate West Bank and Gaza
    wb_g = ['West Bank', 'Region: Gaza', 'Region: West Bank', 'Palestinian']
    base_records['Country'] = base_records['Country'].replace(
        wb_g, 'West Bank and Gaza'
    )

    # Remove special cases
    base_records = base_records[
        ~(base_records['Country'].str.startswith('-', na=False) |
            base_records['Country'].str.startswith('Region', na=False) |
            base_records['Country'].eq('undetermined'))
    ]

    # Create panel dates/countries
    dates_df = pd.DataFrame({'Date': sorted(data['Rep_date'].unique())})
    countries_df = pd.DataFrame({'Country': base_records['Country'].unique()})
    panel = dates_df.merge(countries_df, how='cross')

    # Count entities by country-date using add_date
    entity_counts = (base_records
                    .groupby(['Country', 'add_date'])
                    .size()
                    .reset_index(name='entity_counts')
                    .astype({'entity_counts': 'int32'}))

    # Merge entity counts to panel
    panel = panel.merge(entity_counts, 
                        left_on=['Country', 'Date'],
                        right_on=['Country', 'add_date'],
                        how='left')
    panel['entity_counts'] = panel['entity_counts'].fillna(0).astype('int32')

    # Create additions column
    first_date = dates_df['Date'].min()
    panel['additions'] = np.where(
        panel['Date'] == first_date, 0, panel['entity_counts']
    ).astype('int32')

    # Count and merge removals using removal_date
    removals = (base_records[base_records['removal_date'].notna()]
                .groupby(['Country', 'removal_date'])
                .size()
                .reset_index(name='removals')
                .astype({'removals': 'int32'}))

    panel = panel.merge(removals, 
                        left_on=['Country', 'Date'],
                        right_on=['Country', 'removal_date'],
                        how='left')
    panel['removals'] = panel['removals'].fillna(0).astype('int32')

    # Calculate changes and levels
    panel['change'] = (panel['additions'] - panel['removals']).astype('int32')
    panel['temp_col'] = np.where(panel['Date'] == first_date, 
                                 panel['entity_counts'], 
                                 panel['change']).astype('int32')
    panel['levels'] = panel.groupby('Country')['temp_col'].cumsum().astype('int32')

    # Add date components and clean up
    panel['Date'] = pd.to_datetime(panel['Date'])
    panel['yrqtr'] = panel['Date'].dt.to_period('Q')
    panel['yrmon'] = panel['Date'].dt.to_period('M')

    cols = ['Country', 'Date', 'yrqtr', 'yrmon', 'levels', 
            'additions', 'removals', 'change']
    
    panel = panel[cols].sort_values(['Country', 'Date']).reset_index(drop=True)

    return panel