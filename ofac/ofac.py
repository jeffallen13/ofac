import pandas as pd
import numpy as np
import os
from datetime import datetime
from typing import Optional

class OFACProcessor:
    """A processor for OFAC sanctions list data.

    This class processes OFAC sanctions lists via three steps:
    1. Downloads current SDN and Consolidated lists
    2. Updates the OFAC list tracking historical changes
    3. Creates a panel dataset of sanctions by country over time

    Parameters
    ----------
    data_dir : str, default='data'
        Directory for storing OFAC data files

    Notes
    -----
    The system handles many-to-many relationships between entities and their
    alternate names/addresses. It tracks additions and removals at the
    entity-country level.
    """

    def __init__(self, data_dir: str = 'data') -> None:
        self.data_dir = data_dir
        self.base_url = "https://www.treasury.gov/ofac/downloads"
        self.current_date = datetime.now().strftime('%Y-%m-%d')
        
        # Column names for different file types
        self.main_cols = [
            "Ent_num", "SDN_name", "SDN_type", "Program", "Title", "Call_sign",
            "Vess_type", "Tonnage", "GRT", "Vess_flag", "Vess_owner", "Remarks"
        ]
        self.add_cols = [
            "Ent_num", "Add_num", "Address", "Locality", "Country", "Add_remarks"
        ]
        self.alt_cols = [
            "Ent_num", "Alt_num", "Alt_type", "Alt_name", "Alt_remarks"
        ]
        self.comments_cols = ["Ent_num", "Remarks_cont"]
        
        os.makedirs(data_dir, exist_ok=True)

    def _get_file_url(self, file_name: str, consolidated: bool = False) -> str:
        """Construct URL for OFAC file download.

        Parameters
        ----------
        file_name : str
            Name of the file to download
        consolidated : bool, default=False
            Whether the file is from the consolidated list

        Returns
        -------
        str
            Complete URL for file download
        """
        if consolidated:
            return f"{self.base_url}/consolidated/{file_name}"
        else:
            return f"{self.base_url}/{file_name}"

    def _read_clean_csv(self, url: str, columns: list) -> pd.DataFrame:
        """Read and clean CSV file from OFAC website.

        Parameters
        ----------
        url : str
            URL of the CSV file
        columns : list
            List of column names for the file

        Returns
        -------
        pd.DataFrame
            Cleaned dataframe with proper column names and types
        """
        df = pd.read_csv(url, names=columns)
        # Remove placeholder lines at end; filter second column
        df = df[~pd.isna(df[columns[1]])]  
        df['Ent_num'] = pd.to_numeric(df['Ent_num'])
        return df

    def download_current_data(self) -> pd.DataFrame:
        """Download and process current OFAC data.
        
        Downloads and merges SDN and Consolidated lists, including address,
        alternate names, and comments data. Handles many-to-many relationships
        between entities and their alternate names.

        Returns
        -------
        pd.DataFrame
            Combined dataset with current sanctions data
        """
        # Download SDN data
        sdn = self._read_clean_csv(
            self._get_file_url('sdn.csv'), 
            self.main_cols
        )
        sdn_add = self._read_clean_csv(
            self._get_file_url('add.csv'), 
            self.add_cols
        )
        sdn_alt = self._read_clean_csv(
            self._get_file_url('alt.csv'), 
            self.alt_cols
        )
        sdn_comments = self._read_clean_csv(
            self._get_file_url('sdn_comments.csv'), 
            self.comments_cols
        )

        # Download consolidated data
        cons = self._read_clean_csv(
            self._get_file_url('cons_prim.csv', True), 
            self.main_cols
        )
        cons_add = self._read_clean_csv(
            self._get_file_url('cons_add.csv', True), 
            self.add_cols
        )
        cons_alt = self._read_clean_csv(
            self._get_file_url('cons_alt.csv', True), 
            self.alt_cols
        )
        cons_comments = self._read_clean_csv(
            self._get_file_url('cons_comments.csv', True), 
            self.comments_cols
        )

        # Process SDN data with many-to-many relationships
        sdn_df = (sdn
                .merge(sdn_add, on='Ent_num', how='left')
                .merge(sdn_alt, on='Ent_num', how='outer')  # many-to-many
                .merge(sdn_comments, on='Ent_num', how='left'))
        sdn_df['Program_cat'] = 'SDN'

        # Process consolidated data with many-to-many relationships
        cons_df = (cons
                    .merge(cons_add, on='Ent_num', how='left')
                    .merge(cons_alt, on='Ent_num', how='outer')  # many-to-many
                    .merge(cons_comments, on='Ent_num', how='left'))
        cons_df['Program_cat'] = 'NSDN'

        # Combine datasets and add current date
        current_data = pd.concat([sdn_df, cons_df])
        current_data['Rep_date'] = self.current_date
        
        return current_data

    def update_ofac_list(self) -> pd.DataFrame:
        """Update OFAC list with new data.
        
        Downloads current data and combines with existing OFAC list, tracking
        changes and updating addition/removal dates.

        Returns
        -------
        pd.DataFrame
            Updated OFAC list with tracked changes
        """
        # Download current data and add date columns
        current_data = self.download_current_data()
        current_data['add_date'] = self.current_date
        current_data['removal_date'] = pd.NA
        
        # Read existing OFAC list
        existing_data = pd.read_csv(os.path.join(self.data_dir, 'ofac_list.csv'))
        
        # Store original add dates for entity-country pairs
        # This is necessary because existing entities might have new information
        # (e.g., new addresses) in current_data. These won't be dropped in
        # drop_duplicates, but should keep their original add_date rather than
        # getting today's date
        original_add_dates = (existing_data[['Ent_num', 'Country', 'add_date']]
                                .drop_duplicates(subset=['Ent_num', 'Country']))
        
        # Concat with current data
        full_data = pd.concat([existing_data, current_data])
        
        # Get last appearance date for each entity-country pair
        date_ranges = (full_data.groupby(['Ent_num', 'Country'])['Rep_date']
                        .agg('max')
                        .reset_index()
                        .rename(columns={'Rep_date': 'last_date'}))
        
        # Remove duplicates keeping all info changes, excluding tracking columns
        dedup_cols = [col for col in full_data.columns 
                        if col not in ['Rep_date', 'add_date', 'removal_date']]
        unique_data = full_data.drop_duplicates(subset=dedup_cols, keep='first')
        
        # Merge last appearance dates
        unique_data = unique_data.merge(date_ranges, on=['Ent_num', 'Country'])
        
        # Merge original add dates and handle new entities
        unique_data = unique_data.merge(
            original_add_dates, 
            on=['Ent_num', 'Country'], 
            how='left',
            suffixes=('_current', '_original')
        )
        
        # Use original add_date where it exists, current_date for new entities
        unique_data['add_date'] = np.where(
            unique_data['add_date_original'].isna(),
            unique_data['add_date_current'],
            unique_data['add_date_original']
        )
        
        # Clean up intermediate add_date columns
        unique_data = unique_data.drop(['add_date_current', 'add_date_original'], axis=1)
        
        # Update removal dates:
        # 1. Only process entities where:
        #    - Last appearance is before current date (not in current data)
        #    - No existing removal date
        # 2. For these entities, set removal date to either:
        #    - Current date if month-end would be in future
        #    - Month-end of last appearance if not in future
        unique_data['removal_date'] = np.where(
            (unique_data['last_date'] < self.current_date) & (unique_data['removal_date'].isna()),
            np.where(
                (pd.to_datetime(unique_data['last_date']) + pd.offsets.MonthEnd(1)).dt.strftime('%Y-%m-%d') > self.current_date,
                self.current_date,
                (pd.to_datetime(unique_data['last_date']) + pd.offsets.MonthEnd(1)).dt.strftime('%Y-%m-%d')
            ),
            unique_data['removal_date']
        )
        
        # Clean up intermediate columns
        unique_data = unique_data.drop(['last_date'], axis=1)
        
        return unique_data

    def create_panel(self, data: pd.DataFrame) -> pd.DataFrame:
        """Create panel showing entity counts and changes by country.
        
        Creates a monthly panel dataset showing the number of sanctioned 
        entities by country over time, including additions and removals.

        Parameters
        ----------
        data : pd.DataFrame
            OFAC list with tracking information

        Returns
        -------
        pd.DataFrame
            Panel dataset with entity counts by country and date
        """
        # First get distinct entity-country records using add_date
        base_records = (data[['Ent_num', 'Country', 'add_date', 'removal_date']]
                        .drop_duplicates())
        
        '''
        Consolidate West Bank and Gaza, using World Bank convention to 
        faciliate joining other datasets.
        '''
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

        countries_df = pd.DataFrame(
            {'Country': base_records['Country'].unique()}
        )

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

        panel['entity_counts'] = (
            panel['entity_counts'].fillna(0).astype('int32')
        )
        
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
        panel['change'] = (
            panel['additions'] - panel['removals']
        ).astype('int32')

        panel['temp_col'] = np.where(
            panel['Date'] == first_date, 
            panel['entity_counts'], 
            panel['change']
        ).astype('int32')

        panel['levels'] = (
            panel.groupby('Country')['temp_col'].cumsum().astype('int32')
        )
        
        # Add date components and clean up
        panel['Date'] = pd.to_datetime(panel['Date'])
        panel['yrqtr'] = panel['Date'].dt.to_period('Q')
        panel['yrmon'] = panel['Date'].dt.to_period('M')
        
        cols = ['Country', 'Date', 'yrqtr', 'yrmon', 'levels', 
                'additions', 'removals', 'change']
        
        panel = (
            panel[cols].sort_values(['Country', 'Date']).reset_index(drop=True)
        )

        return panel
