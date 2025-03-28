import pandas as pd
import numpy as np
import regex


## Read in Prison Popultion totals by State
tot_prison_pop = pd.read_csv("raw_data/p22stat01.csv")
# print(tot_prison_pop.describe())

# rename the columns for later merging
cols_prison_pop = tot_prison_pop.columns
# print(cols_prison_pop)
new_cols_prison_pop = ['jurisdiction', 'total_prison_pop_22', 'white_pop_22', 'black_pop_22', 'hispanic_pop_22',
       'american_indian_pop_22', 'asian_pop_22', 'pic_pop_22', 'more_races_pop_22', 'other_pop_22', 'unknown_pop_22', 'no_report_pop_22']
tot_prison_pop.columns = new_cols_prison_pop
 
# remove misc. characters & commas, also turn / and ~ to NAs
tot_prison_pop = tot_prison_pop.replace([",","\""],"" ,regex=True).replace(["/","~"], pd.NA, regex = True)

# fix data types
numeric_cols = ['total_prison_pop_22', 'white_pop_22', 'black_pop_22', 'hispanic_pop_22',
       'american_indian_pop_22', 'asian_pop_22', 'pic_pop_22', 'more_races_pop_22', 'other_pop_22', 'unknown_pop_22', 'no_report_pop_22']

tot_prison_pop[numeric_cols] = tot_prison_pop[numeric_cols].apply(pd.to_numeric)

# print(tot_prison_pop.head())

# for the main data frame I just need the total populations, but I will save the demographics data as a csv also
tot_prison_pop_sub = tot_prison_pop.iloc[:,0:2]
# print(tot_prison_pop_sub.head())

## Read in Prison population per 100,000 people
prison_rate = pd.read_csv("raw_data/p22stt07.csv")

# keep just the total column for 2022
prison_rate_df = prison_rate[['Jurisdiction','Total_2022']]

# convert total column to numeric
prison_rate_df['Total_2022'] = pd.to_numeric(prison_rate_df['Total_2022'])

# rename columns
prison_rate_df.columns = ['jurisdiction','total_inmates_per_100000']

# print(prison_rate_df.head())

## Read in State Expenditure Data
state_expends = pd.read_csv("raw_data/StateExpenditures2022.csv")

# save the column names
col_names = state_expends['Type of Expenditure'].to_list()
# strip the extra space from column names
strip_col_names = [s.strip() for s in col_names]

# Flip columns and rows, since our unit of obsercation is states
state_expends_t = state_expends.T

state_expends_t.columns = strip_col_names

# we need just need the Correction column
state_corrections_expends = state_expends_t['Correction'].replace(",","",regex=True)
state_corrections_expends = state_corrections_expends.reset_index()

# remove the first row since it is a duplicate of headers
state_corrections_expends = state_corrections_expends.iloc[1:]

# update "United States" to Federal
state_corrections_expends.loc[state_corrections_expends['index'] == "United States", 'index'] = "Federal"

#remove commas and convert to numeric
state_corrections_expends["Correction"] = pd.to_numeric(state_corrections_expends['Correction'])

# data is in thousands, so have a columns that reflects the true values
state_corrections_expends.loc[:, 'total_correction_expends'] = state_corrections_expends['Correction'] * 1000

# update column names
state_corrections_expends.columns = ["jurisdiction",'correction_expends_abv','total_correction_expends']

# print(state_corrections_expends.head())

## Read in State Corrections Officer Data
all_proffesions_df = pd.read_csv("raw_data/state_M2022_dl.csv")

# filter for just Correctional Officers and Jailers
corrections_df = all_proffesions_df[all_proffesions_df['OCC_TITLE'] == "Correctional Officers and Jailers"]

# choose just the relavent columns: AREA_TITLE, TOT_EMP, A_MEAN
corrections_sub_df = corrections_df[['AREA_TITLE', 'TOT_EMP', 'A_MEAN']].replace(",","", regex=True)

# convert columns to numeric
corrections_sub_df['TOT_EMP'] = pd.to_numeric(corrections_sub_df['TOT_EMP'], errors='coerce')
corrections_sub_df['A_MEAN'] = pd.to_numeric(corrections_sub_df['A_MEAN'], errors='coerce')

# rename the columns
corrections_sub_df.columns = ['jurisdiction','total_co_employment','annual_mean_salary']

# drop the Puerto Rico column
corrections_sub_df = corrections_sub_df[corrections_sub_df['jurisdiction'] != "Puerto Rico"]

# print(corrections_sub_df.head())

## Read in Captive Labor Data
labor_df = pd.read_csv("raw_data/Captive Labor ACLU (Merged Data Sets).csv")

# keep only the first five columns
labor_df = labor_df.iloc[:,0:4]

# simplify column names
new_l_col_names = ['State','num_prison_workers','pay_scale_non_industry','pay_scale_state_industry']
labor_df.columns = new_l_col_names

# parse the pay scale columns
# create columns to fill in the data frame
labor_df[['lower_bound_pay_non_industry', 'upper_bound_pay_non_industry',
          'lower_bound_pay_state_industry', 'upper_bound_pay_state_industry']] = np.nan

# Regex patterns for the range format (e.g., "$10.00 to $20.00 per hour")
pattern_range = r'\$(\d+(\.\d+)?) to \$(\d+(\.\d+)?) per hour'
# Regex for the single value format (e.g., "$0.25 per hour")
pattern_single_value = r'\$(\d+(\.\d+)?) per hour'

for index, row in labor_df.iterrows():
    # Check if the string contains "to" (indicating a range format)
    if isinstance(row['pay_scale_non_industry'], str) and 'to' in row['pay_scale_non_industry']:
       # Apply range regex if the string contains "to"
       extracted_values_range = pd.Series(row['pay_scale_non_industry']).str.extract(pattern_range)
       labor_df.at[index, 'lower_bound_pay_non_industry'] = extracted_values_range.iloc[0, 0]
       labor_df.at[index, 'upper_bound_pay_non_industry'] = extracted_values_range.iloc[0, 2]
    elif isinstance(row['pay_scale_non_industry'], str):
       # Apply single value regex if the string does not contain "to"
       extracted_values_single = pd.Series(row['pay_scale_non_industry']).str.extract(pattern_single_value)
       labor_df.at[index, 'lower_bound_pay_non_industry'] = extracted_values_single.iloc[0, 0]
       labor_df.at[index, 'upper_bound_pay_non_industry'] = extracted_values_single.iloc[0, 0]
    
    # Same logic for the 'pay_scale_state_industry' column
    if isinstance(row['pay_scale_state_industry'], str) and 'to' in row['pay_scale_state_industry']:
       # Apply range regex if the string contains "to"
       extracted_values_range = pd.Series(row['pay_scale_state_industry']).str.extract(pattern_range)
       labor_df.at[index, 'lower_bound_pay_state_industry'] = extracted_values_range.iloc[0, 0]
       labor_df.at[index, 'upper_bound_pay_state_industry'] = extracted_values_range.iloc[0, 2]
    elif isinstance(row['pay_scale_state_industry'], str):
       # Apply single value regex if the string does not contain "to"
       extracted_values_single = pd.Series(row['pay_scale_state_industry']).str.extract(pattern_single_value)
       labor_df.at[index, 'lower_bound_pay_state_industry'] = extracted_values_single.iloc[0, 0]
       labor_df.at[index, 'upper_bound_pay_state_industry'] = extracted_values_single.iloc[0, 0]

# Convert the extracted values to numeric
labor_df['lower_bound_pay_non_industry'] = pd.to_numeric(labor_df['lower_bound_pay_non_industry'], errors='coerce')
labor_df['upper_bound_pay_non_industry'] = pd.to_numeric(labor_df['upper_bound_pay_non_industry'], errors='coerce')
labor_df['lower_bound_pay_state_industry'] = pd.to_numeric(labor_df['lower_bound_pay_state_industry'], errors='coerce')
labor_df['upper_bound_pay_state_industry'] = pd.to_numeric(labor_df['upper_bound_pay_state_industry'], errors='coerce')

# # any state that has zero needs to be made to be zero
labor_df.loc[labor_df['pay_scale_non_industry'] == "$0", 'lower_bound_pay_non_industry'] = 0.00
labor_df.loc[labor_df['pay_scale_non_industry'] == "$0", 'upper_bound_pay_non_industry'] = 0.00

labor_df.loc[labor_df['pay_scale_state_industry'] == "$0", 'lower_bound_pay_state_industry'] = 0.00
labor_df.loc[labor_df['pay_scale_state_industry'] == "$0", 'upper_bound_pay_state_industry'] = 0.00

# Find the mean of the pay scales
labor_df['mean_pay_non_industry'] = round(((labor_df['lower_bound_pay_non_industry']+labor_df['upper_bound_pay_non_industry'])/2),2)
labor_df['mean_pay_state_industry'] = round(((labor_df["lower_bound_pay_state_industry"] + labor_df['upper_bound_pay_state_industry'])/2),2)

# change the number of prison works to numeric
labor_df['num_prison_workers'] = labor_df['num_prison_workers'].replace(',',"",regex=True)
labor_df['num_prison_workers'] = pd.to_numeric(labor_df['num_prison_workers'], errors = 'coerce')

# remove the two unneeded string columns
labor_df = labor_df.drop(['pay_scale_non_industry', 'pay_scale_state_industry'], axis=1)

# fix the strings of the state column
labor_df['State'] = labor_df['State'].str.strip(' ') 
# print(labor_df.head())

# needed to manually update two rows because they were written very differently
labor_df.loc[labor_df['State'] == "Washington", :] = ["Washington",8392.0,0.0,0.39,0.7,2.7,0.2,1.7]
labor_df.loc[labor_df['State'] == "Wyoming", :] = ["Wyoming",None,0.35,1.00,0.50,1.20,0.68,0.85]


## Read in Minimum Wage data
min_wage_df = pd.read_csv("raw_data/minimum_wage_2022.csv")
# nothing needs to be done with this data frame

## All CSV files are in and cleaned, now we merge

# our different key fields are State and jurisdiction
main_df = tot_prison_pop_sub.merge(prison_rate_df, how = 'outer', on='jurisdiction')
main_df = main_df.merge(labor_df, how = 'outer', left_on='jurisdiction', right_on='State')
main_df = main_df.merge(min_wage_df, how = "outer", on = 'jurisdiction')
main_df = main_df.merge(corrections_sub_df, how = 'outer', on='jurisdiction')
main_df = main_df.merge(state_corrections_expends, how = 'outer', on='jurisdiction')

# drop the state column
main_df = main_df.drop(['State'], axis = 1)

print(main_df.head())

# write to a csv
main_df.to_csv('processed_data/merged_state_obs.csv', index=False)

# save the prison demographics for later use
tot_prison_pop.to_csv('processed_data/prison_pop_demographics_2022.csv', index=False)