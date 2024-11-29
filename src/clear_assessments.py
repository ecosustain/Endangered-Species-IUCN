#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import pandas as pd

# Auxiliar Functions

def create_list_of_items(dictionary: dict) -> list:
    """
    Converts a dictionary into a list of item pairs, where each key is paired with each of its values.
    
    Args:
        dictionary (dict): A dictionary where each key maps to a list of values.
        
    Returns:
        list: A list of lists, where each inner list contains a key-value pair from the dictionary.
    """
    rows = []
    for key, values in dictionary.items():
        for value in values:
            rows.append([key, value])
    return rows

# Reading Assessments

def json_to_dataframe(json_file: str) -> pd.DataFrame:
    """
    Reads a JSON file and converts it into a Pandas DataFrame.
    
    Args:
        json_file (str): The path to the JSON file where each line is a JSON object.
        
    Returns:
        pd.DataFrame: A DataFrame containing the structured data from the JSON file.
    """
    data = []
    with open(json_file, 'r') as file:
        for line in file:
            data.append(json.loads(line))
    dataframe = pd.json_normalize(data)
    return dataframe

def rename_uses(df: pd.DataFrame) -> None:
    """
    Renames and standardizes values in the 'use_and_trade' column of a DataFrame.
    
    This function processes a DataFrame to unify different terms in the 'use_and_trade' column, consolidating them into standard categories.
    Unknown or unlisted uses are labeled appropriately.
    
    Args:
        df (pd.DataFrame): The DataFrame containing a 'use_and_trade' column, with each entry being a list of uses.
        
    Returns:
        None: The function modifies the DataFrame in place.
    """
    valid_uses = ['Pets/display animals, horticulture', 
                  'Sport hunting/specimen collecting', 
                  'Construction or structural materials', 
                  'Fuels',
                  'Medicine - human & veterinary', 
                  'Research',
                  'Handicrafts, jewellery, etc.',
                  'Wearing apparel, accessories']
    for i in range(len(df)):
        uses = df.iloc[i]['use_and_trade']
        new_uses = []
        for use in uses:
            if use == "Unknown" and len(uses) <= 1:
                new_uses = ["Unknown"]
            elif use in valid_uses:
                new_uses.append(use)
            elif use == "Food - human" or use == "Food - animal":
                if "Food" not in new_uses:
                    new_uses.append("Food")
            elif use == 'Manufacturing chemicals' or use == 'Other chemicals':
                if 'Chemicals' not in new_uses:
                    new_uses.append('Chemicals')
            else:
                if 'Others' not in new_uses:
                    new_uses.append('Others')
        if len(uses) == 0:
            new_uses = ["Unknown"]
        df.at[i, 'use_and_trade'] = new_uses
        
def map_risk_categories(dataframe: pd.DataFrame) -> pd.DataFrame:
    """
    Maps and standardizes risk categories in the assessments dataframe to a simplified set of categories.

    Parameters:
        dataframe (pd.DataFrame): The assessments dataframe.

    Returns:
        pd.DataFrame: The dataframe with a renamed and standardized 'risk_category' column.

    Notes:
        This method maps various risk category values to a unified set of categories for consistency. 
        Examples of mappings include:
            - 'LC', 'LR/lc' → 'LC' (Least Concern)
            - 'NT', 'LR/nt' → 'LT' (Little Threatened)
            - 'V', 'VU' → 'VU' (Vulnerable)
            - 'EN', 'E' → 'EN' (Endangered)
            - 'CR' → 'CR' (Critically Endangered)
            - 'RE' (Regionally Extinct)
            - 'EW' (Extinct in the Wild)
            - 'EX', 'Ex/E' → 'EX' (Extinct)
            - Other unrecognized categories are mapped to 'NE' (Not Evaluated).
    """
    mapping = {'LC': 'LC',
            'LR/lc': 'LC',
            'EN': 'EN',
            'E': 'EN',
            'NT': 'LT',
            'nt': 'LT',
            'LR/nt': 'LT',
            'LR/cd': 'LT',
            'VU': 'VU',
            'V': 'VU',
            'RE': 'RE',
            'DD': 'NE',
            'O': 'NE',
            'I': 'NE',
            'K': 'NE',
            'T': 'EN',
            'R': 'NE',
            'CR': 'CR',
            'N/A': 'NE',
            'NA': 'NE',
            'NE': 'NE',
            'EX': 'EX',
            'Ex': 'EX',
            'Ex/E': 'EX',
            'Ex?': 'EX',
            'EW': 'EW',
            'NR': 'NE',
            'CUSTOM': 'NE',
            'CT': 'NE'}
    dataframe['red_list_category'] = dataframe['red_list_category'].replace(mapping)
    return dataframe.rename(columns={'red_list_category': 'risk_category'})
    
    
def clean_assessments(dataframe: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans and processes the assessments dataframe by standardizing data and removing invalid entries.

    Parameters:
        dataframe (pd.DataFrame): The dataframe containing species assessments.

    Returns:
        pd.DataFrame: The cleaned dataframe with updated risk categories and no missing risk data.

    Steps:
        1. Renames and groups usage-related data using `rename_uses`.
        2. Removes rows where the 'red_list_category' is missing.
        3. Standardizes the risk categories using `map_risk_categories`.
        4. Saves the cleaned dataframe to a CSV file for later use.
    
    Notes:
        The cleaned dataframe is saved to "../data/assessments.csv".
    """
    rename_uses(dataframe) # Rename and Group Usages
    dataframe = dataframe.dropna(subset=['red_list_category']) # Remove Assessments without Risk Data
    dataframe = map_risk_categories(dataframe) # Clear Risk Categories
    dataframe.to_csv("../data/assessments.csv")
    return dataframe
    
def create_dict_uses_by_id(dataframe: pd.DataFrame, column: str, unique_ids: list) -> dict:
    """
    Creates a dictionary mapping each unique taxon ID to the longest list of values in a specified column.
    
    Args:
        dataframe (pd.DataFrame): The DataFrame containing species data and the specified column.
        column (str): The name of the column to retrieve lists of values from.
        unique_ids (list): A list of unique taxon IDs (from 'taxon.sis_id') to filter by.
        
    Returns:
        dict: A dictionary where each key is a taxon ID, and each value is the longest list of values from the specified column.
    """
    dict_uses_id = {}
    for i in range(len(unique_ids)):
        filtered_dataframe = dataframe[dataframe['taxon.sis_id'] == unique_ids[i]]
        list_of_max_length = []
        for j in range(len(filtered_dataframe)):
            list_of_values = filtered_dataframe.iloc[j][column]
            if len(list_of_values) > len(list_of_max_length):
                list_of_max_length = list_of_values
        dict_uses_id[unique_ids[i]] = list_of_max_length
    return dict_uses_id

def create_dataframe_uses_by_id(dataframe: pd.DataFrame, unique_ids: list) -> None:
    """
    Creates a DataFrame that maps each taxon ID to its associated uses or trades.
    
    Args:
        dataframe (pd.DataFrame): The DataFrame containing species data, including the 'use_and_trade' column.
        unique_ids (list): A list of unique taxon IDs to filter by.
        
    Returns:
        None
    """
    dict_uses_id = create_dict_uses_by_id(dataframe, 'use_and_trade', unique_ids)
    rows = create_list_of_items(dict_uses_id)
    uses_dataframe = pd.DataFrame(rows, columns=["ID", "Use"])
    uses_dataframe.to_csv("../data/uses.csv")

def create_dataframe_countries_by_id(dataframe: pd.DataFrame, unique_ids: list) -> None:
    """
    Creates a DataFrame mapping each taxon ID to the countries in which it is located.
    
    Args:
        dataframe (pd.DataFrame): The DataFrame containing species data, including the 'locations' column.
        unique_ids (list): A list of unique taxon IDs to filter by.
        
    Returns:
        None
    """
    dict_countries_id = create_dict_uses_by_id(dataframe, 'locations', unique_ids)
    rows = []
    for key, values in dict_countries_id.items():
        for value in values:
            rows.append([key, value['country']])
    countries_dataframe = pd.DataFrame(rows, columns=["ID", "Country"])
    countries_dataframe.to_csv("../data/countries.csv")
    

def main():
    json_file = '../data/assessments.json'
    dataframe = json_to_dataframe(json_file) # Read Assessments
    dataframe = clean_assessments(dataframe)
    unique_ids = list(dataframe['taxon.sis_id'].unique())
    create_dataframe_uses_by_id(dataframe, unique_ids)
    create_dataframe_countries_by_id(dataframe, unique_ids)
    
if __name__ == '__main__':
    main()
