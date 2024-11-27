import pandas as pd
import dash
from dash import Dash, dcc, html
from dash.dependencies import Input, Output, State
import plotly.graph_objects as go
import plotly.express as px
import geopandas as gpd
import datetime
import os
import gc

def clean_input(input_string: str) -> str:
    return ' '.join(input_string.strip().split())

def filter_dataframe_by_specie(df, specie):
    """
    Generate year series dataframe for a specific species

    Args:
        df (pd.DataFrame): DataFrame of species assessments
        specie (str): Scientific name of a species
    
    Returns:
        pd.DataFrame: contains status of a species in every year between first and last assessments

    """
    status_enum = {'NE': 0,
            'LC': 1,
            'LT': 2,
            'VU': 3,
            'EN': 4,
            'CR': 5,
            'RE': 6,
            'EW': 7,
            'EX': 8}
    
    year = datetime.date.today().year
    df_specie = df[df['taxon.scientific_name'] == specie]
    df_specie = df_specie.dropna(subset=['year_published'])
    df_specie["year_published"] = df_specie["year_published"].astype(int)

    year_series = pd.Series(list(range(min(df_specie['year_published']), year+1)), name="Years")
    df_plot = year_series.to_frame()
    df_plot = df_plot.merge(df_specie[['year_published', 'risk_category']], how='left', left_on='Years', right_on='year_published')
    df_plot['categoriaOrdem'] = df_plot['risk_category'].map(status_enum)
    df_plot.drop('year_published', axis=1, inplace=True)
    df_plot = df_plot.ffill()
    return df_plot
    

def filter_taxonomy(dataframe: pd.DataFrame, 
                   selected_kingdom: str, 
                   selected_phylum: str, 
                   selected_class: str, 
                   selected_order: str, 
                   selected_family: str, 
                   selected_specie: str) -> pd.DataFrame:
    """
    Filters the DataFrame based on selected taxonomic criteria.
    
    Args:
        dataframe (pd.DataFrame): DataFrame containing taxonomic columns such as 'taxon.kingdom_name', 'taxon.phylum_name', etc.
        selected_kingdom (str): The kingdom to filter by, or None to skip filtering by kingdom.
        selected_phylum (str): The phylum to filter by, or None to skip filtering by phylum.
        selected_class (str): The class to filter by, or None to skip filtering by class.
        selected_order (str): The order to filter by, or None to skip filtering by order.
        selected_family (str): The family to filter by, or None to skip filtering by family.
        selected_specie (str): The species to filter by, or None to skip filtering by species.
        
    Returns:
        pd.DataFrame: A filtered DataFrame containing only entries matching the selected taxonomic criteria.
    """
    filtered_df = dataframe.copy()
    if selected_kingdom:
        filtered_df = dataframe[dataframe["taxon.kingdom_name"] == selected_kingdom]
    if selected_phylum:
        filtered_df = filtered_df[filtered_df["taxon.phylum_name"] == selected_phylum]
    if selected_class:
        filtered_df = filtered_df[filtered_df["taxon.class_name"] == selected_class]
    if selected_order:
        filtered_df = filtered_df[filtered_df["taxon.order_name"] == selected_order]
    if selected_family:
        filtered_df = filtered_df[filtered_df["taxon.family_name"] == selected_family]
    if selected_specie:
        filtered_df = filtered_df[filtered_df["taxon.scientific_name"] == selected_specie]
    return filtered_df

def filter_years(dataframe, countries_dataframe, selected_specie, selected_family, selected_order, selected_class, selected_phylum, selected_kingdom, selected_countries):
    """
    Generates list of unique years of assessments given taxonomic criteria and country subset.
    
    Args:
        dataframe (pd.DataFrame): DataFrame containing taxonomic columns such as 'taxon.kingdom_name', 'taxon.phylum_name', etc.
        countries_dataframe (pd.DataFrame): DataFrame containing status of species in countries it inhabits
        selected_kingdom (str): The kingdom to filter by, or None to skip filtering by kingdom.
        selected_phylum (str): The phylum to filter by, or None to skip filtering by phylum.
        selected_class (str): The class to filter by, or None to skip filtering by class.
        selected_order (str): The order to filter by, or None to skip filtering by order.
        selected_family (str): The family to filter by, or None to skip filtering by family.
        selected_specie (str): The species to filter by, or None to skip filtering by species.
        selected_countries (list): Countries to filter by
        
    Returns:
        list of years with at least one assessment fitting the given criteria
    """
    
    if selected_kingdom is None:
        ids_species = []
    if selected_phylum is None:
        ids_species = list(dataframe[dataframe["taxon.kingdom_name"] == selected_kingdom]["taxon.sis_id"].dropna().unique())
    elif selected_class is None:
        ids_species = list(dataframe[(dataframe["taxon.kingdom_name"] == selected_kingdom) & 
                  (dataframe["taxon.phylum_name"] == selected_phylum)]["taxon.sis_id"].dropna().unique())
    elif selected_order is None:
        ids_species = list(dataframe[(dataframe["taxon.kingdom_name"] == selected_kingdom) & 
                  (dataframe["taxon.phylum_name"] == selected_phylum) &
                  (dataframe["taxon.class_name"] == selected_class)]["taxon.sis_id"].dropna().unique())
    elif selected_family is None:
        ids_species = list(dataframe[(dataframe["taxon.kingdom_name"] == selected_kingdom) & 
                  (dataframe["taxon.phylum_name"] == selected_phylum) &
                  (dataframe["taxon.class_name"] == selected_class) &
                  (dataframe["taxon.order_name"] == selected_order)]["taxon.sis_id"].dropna().unique())
    elif selected_specie is None:
        ids_species = list(dataframe[(dataframe["taxon.kingdom_name"] == selected_kingdom) & 
                  (dataframe["taxon.phylum_name"] == selected_phylum) &
                  (dataframe["taxon.class_name"] == selected_class) &
                  (dataframe["taxon.order_name"] == selected_order) &
                  (dataframe["taxon.family_name"] == selected_family)]["taxon.sis_id"].dropna().unique())
    else:
        ids_species = list(dataframe[(dataframe["taxon.kingdom_name"] == selected_kingdom) & 
                  (dataframe["taxon.phylum_name"] == selected_phylum) &
                  (dataframe["taxon.class_name"] == selected_class) &
                  (dataframe["taxon.order_name"] == selected_order) &
                  (dataframe["taxon.family_name"] == selected_family) &
                  (dataframe["taxon.scientific_name"] == selected_specie)]["taxon.sis_id"].dropna().unique())
    if selected_countries:
        ids_countries = list(countries_dataframe[countries_dataframe['Country'].isin(selected_countries)]['ID'].dropna().unique())
    if selected_countries and selected_kingdom:    
        ids = list(set(ids_countries) & set(ids_species))
        filtered_years = list(dataframe[dataframe["taxon.sis_id"].isin(ids)]["year_published"].dropna().unique())
    elif selected_kingdom:
        filtered_years = list(dataframe[dataframe["taxon.sis_id"].isin(ids_species)]["year_published"].dropna().unique())
    elif selected_countries:
        filtered_years = list(dataframe[dataframe["taxon.sis_id"].isin(ids_countries)]["year_published"].dropna().unique())
    else: 
        filtered_years = list(dataframe["year_published"].dropna().unique())
    filtered_years.sort()
    return filtered_years
    

def filter_some_years(dataframe: pd.DataFrame, list_years: list) -> pd.DataFrame:
    """
    Filters the DataFrame to include only entries published in specified years.
    
    Args:
        dataframe (pd.DataFrame): DataFrame containing a 'year_published' column with publication years.
        list_years (list): List of years to filter the data by.
        
    Returns:
        pd.DataFrame: Filtered DataFrame containing only rows with publication years in list_years.
    """
    return dataframe[dataframe['year_published'].isin(list_years)]


def calculate_values_per_mode(list_of_values: list, total: int, percentage_mode: bool) -> list:
    """
    Calculates values as percentages or raw values based on a mode.
    
    Args:
        list_of_values (list): A list of numerical values to process.
        total (int or float): The total value used to calculate percentages.
        percentage_mode (bool): If True, returns values as percentages of total; otherwise, returns raw values.
        
    Returns:
        list: A list of values, either as percentages or as raw values depending on the mode.
    """
    if percentage_mode:
        return [(value / total) * 100 if total > 0 else 0 for value in list_of_values]
    return list_of_values

def create_list_unique_years(dataframe: pd.DataFrame) -> list:
    """
    Extracts and returns a sorted list of unique years from the 'year_published' column in the DataFrame.
    
    Args:
        dataframe (pd.DataFrame): The DataFrame containing the 'year_published' column with publication years.
        
    Returns:
        list: A sorted list of unique years as integers, excluding any non-integer values.
    """
    years = list(dataframe['year_published'].unique())
    unique_years = []
    for value in years:
        try:
            int_value = int(value)
            unique_years.append(int_value)
        except:
            continue
    unique_years.sort()
    return unique_years

def generate_uses_count(dataframe: pd.DataFrame, uses_dataframe: pd.DataFrame) -> dict:
    """
    Create dictionary with frequencies of uses of certain species
    
    Args:
        dataframe (pd.DataFrame): DataFrame containing taxonomic columns such as 'taxon.kingdom_name', 'taxon.phylum_name', etc.
        uses_dataframe (pd.Dataframe): DataFrame containing uses of species
        
    Returns:
        dict: frequencies of uses, determined by the species contained in "dataframe"
    """
    ids = list(dataframe['taxon.sis_id'].unique())
    filtered_dataframe = uses_dataframe[uses_dataframe['ID'].isin(ids)]
    usage_counts = filtered_dataframe['Use'].value_counts().to_dict()
    try:
        del usage_counts['Unknown']
    except:
        pass
    return usage_counts

def read_shapefiles(base_dir):
    """
        Reads shapefiles from a directory into a GeoDataFrame 

        Args:
            base_dir (str): path to base directory

        Returns:
            GeoDataFrame: containing scientific names of species and their habitats' geometries
    """

    shapefiles_dir = os.path.join(base_dir, "../../data/shapefiles")
    
    # Lista para armazenar os GeoDataFrames
    geo_dataframes = []
    
    # Colunas que você deseja manter
    columns_to_keep = ["sci_name", "geometry"]  # Inclua 'geometry' para manter a geometria
    #file_path = os.path.join(shapefiles_dir, 'FW_FISH_PART1.shp')
    #gdf =  gpd.read_file(file_path, encoding='utf-8')
    #gdf = gdf[columns_to_keep]
    #return gdf

    # Percorrer todos os arquivos no diretório
    for file in os.listdir(shapefiles_dir):
        if file.endswith(".shp"):  # Verificar se é um shapefile
            file_path = os.path.join(shapefiles_dir, file)
            gdf = gpd.read_file(file_path, encoding="utf-8")
            gdf = gdf[columns_to_keep]
            geo_dataframes.append(gdf)
    
    # Concatenar todos os GeoDataFrames em um único
    final_gdf = pd.concat(geo_dataframes, ignore_index=True)
    del geo_dataframes
    gc.collect()
    return final_gdf

base_dir = os.path.dirname(os.path.abspath(__file__))
gdf = read_shapefiles(base_dir)

dataframe = pd.read_csv(os.path.join(base_dir, "../../data/assessments.csv"))
uses_dataframe = pd.read_csv(os.path.join(base_dir, "../../data/uses.csv"))
countries_dataframe = pd.read_csv(os.path.join(base_dir, "../../data/countries.csv"))

unique_ids = list(dataframe['taxon.sis_id'].unique())
unique_years = create_list_unique_years(dataframe)
countries = list(countries_dataframe["Country"].unique())
unique_categories = ["NE", "LC", "LT", "VU", "EN", "CR", "RE", "EW", "EX"]
#unique_categories = list(dataframe["risk_category"].dropna().unique())
species = list(dataframe['taxon.scientific_name'].unique())
