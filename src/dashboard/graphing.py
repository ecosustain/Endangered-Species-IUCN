from data_manipulation import *

def update_fig_layout(fig, title: str, x_label: str, y_label: str) -> None:
    """
    Updates the layout of a Plotly figure with a title, axis labels, and a specified theme.
    
    Args:
        fig (plotly.graph_objs.Figure): The figure to update.
        title (str): The title of the plot.
        x_label (str): Label for the x-axis.
        y_label (str): Label for the y-axis.
        
    Returns:
        None: Modifies the figure in place.
    """
    fig.update_layout(
            title=title,
            xaxis_title=x_label,
            yaxis=dict(title=y_label, categoryorder='total ascending'),
            barmode='stack',
            template="plotly_white"
        )
    
def add_bar(fig, x_values: list, y_values: list, name: str) -> None:
    """
    Adds a horizontal bar to a Plotly figure.
    
    Args:
        fig (plotly.graph_objs.Figure): The figure to which the bar will be added.
        x_values (list): Values along the x-axis.
        y_values (list): Values along the y-axis.
        name (str): The name of the bar trace.
        
    Returns:
        None: Modifies the figure in place.
    """
    fig.add_trace(go.Bar(
                x=x_values,
                y=y_values,
                name=name,
                orientation='h'
            ))
    

def create_bars(fig, 
		all_uses: list, 
		dict_uses: dict, 
		list_selected_items: list, 
		total: int, 
		percentage_mode: bool, 
		years_mode=False) -> None:
    """
    Creates bars in figure for species usage barplot
    
    Args:
        fig (plotly.graph_objs.Figure): plotly figure
        all_uses (list): list of all possible uses, including some that might not be included in dict_uses
        dict_uses (dict): dictionary of dictionaries of frequencies of uses (see function generate_uses_count), grouped by other parameters (year, country, vulnerability category)
        list_selected_items (list): list of parameters used in dict_uses
        total (int): The total value used to calculate percentages.
        percentage_mode (bool): if true, the figure uses percentages as the x-axis
	years_mode (bool): if true, formats the labels for the stacked bar chart by year.

    Returns:
        None
    """
    for item in list_selected_items:
        usage_counts = dict_uses[item]
        values = [usage_counts.get(use, 0) for use in all_uses]
        x_list = calculate_values_per_mode(values, total, percentage_mode)
        if years_mode:
            # remove decimal places from year represented as float
            add_bar(fig, x_list, all_uses, str(int(item)))
        else:
            add_bar(fig, x_list, all_uses, item)
        
def create_figure_with_bar(dict_counts: dict, percentage_mode: bool) -> None:
    """
    Generates figure with barplot

    Args:
        dict_counts (dict): dictionary of frequencies of certain categories
        percentage_mode (bool): if true, the figure uses percentages as the x-axis

    Returns:
        None

    """
    categories = list(dict_counts.keys())
    values = list(dict_counts.values())
    values = calculate_values_per_mode(values, sum(values), percentage_mode)
    return go.Figure(go.Bar(
        x=values,
        y=categories,
        orientation='h',
        marker=dict(color='skyblue')
    ))
    
def update_graph_country(selected_species: str, 
                         selected_family: str, 
                         selected_order: str, 
                         selected_class: str, 
                         selected_phylum: str, 
                         selected_kingdom: str, 
                         selected_countries: list, 
                         selected_years: list, 
                         filtered_df: pd.DataFrame, 
                         total_by_use: dict) -> tuple:
    """
    Updates a stacked barplot grouped by country.

    This method filters the assessments dataframe based on selected 
    taxonomy (species, family, order, class, phylum, kingdom), countries, and years.
    It calculates the total counts of uses for each species within the selected countries
    and generates a dictionary of usage counts by country.

    Parameters:
        selected_species (str): Selected species name.
        selected_family (str): Selected taxonomic family name.
        selected_order (str): Selected taxonomic order name.
        selected_class (str): Selected taxonomic class name.
        selected_phylum (str): Selected taxonomic phylum name.
        selected_kingdom (str): Selected taxonomic kingdom name.
        selected_countries (list): List of selected country names.
        selected_years (list): List of selected years.
        filtered_df (pd.DataFrame): Assessments DataFrame.
        total_by_use (dict): Dictionary to accumulate usage counts.

    Returns:
        tuple: Selected countries, dictionary of usage counts by country, total usage count.
    """
    total = 0
    if selected_countries is None or len(selected_countries) == 0:
        selected_countries = UNIQUE_COUNTRIES

    dict_country_uses = {}
    for country in selected_countries:
        # Filter by country
        list_ids_country = list(COUNTRIES_DATAFRAME[COUNTRIES_DATAFRAME['Country'] == country]["ID"])
        filtered_df = filtered_df[filtered_df['taxon.sis_id'].isin(list_ids_country)]
        # Filter by taxonomy
        filtered_df = filter_taxonomy(filtered_df, selected_kingdom, selected_phylum, selected_class, selected_order, selected_family, selected_species)
        # Filter by years
        if selected_years:
            years_dataframe = filter_some_years(filtered_df, selected_years)
            ids = list(years_dataframe['taxon.sis_id'].unique())
            filtered_df = filtered_df[filtered_df['taxon.sis_id'].isin(ids)]
        # Count usage
        usage_counts = generate_uses_count(filtered_df, USES_DATAFRAME)
        dict_country_uses[country] = usage_counts

        # Update total counts
        for use in usage_counts.keys():
            total_by_use[use] += usage_counts[use]
            total += usage_counts[use]

    return selected_countries, dict_country_uses, total


def update_graph_year(selected_species: str, 
                      selected_family: str, 
                      selected_order: str, 
                      selected_class: str, 
                      selected_phylum: str, 
                      selected_kingdom: str, 
                      selected_countries: list, 
                      selected_years: list, 
                      filtered_df: pd.DataFrame, 
                      total_by_use: dict) -> tuple:
    """
    Updates a stacked barplot grouped by year.

    This method filters the assessments dataframe based on selected 
    taxonomy (species, family, order, class, phylum, kingdom), countries, and years.
    It calculates the total counts of uses for each species within the selected years
    and generates a dictionary of usage counts by year.

    Parameters:
        selected_species (str): Selected species name.
        selected_family (str): Selected taxonomic family name.
        selected_order (str): Selected taxonomic order name.
        selected_class (str): Selected taxonomic class name.
        selected_phylum (str): Selected taxonomic phylum name.
        selected_kingdom (str): Selected taxonomic kingdom name.
        selected_countries (list): List of selected country names.
        selected_years (list): List of selected years.
        filtered_df (pd.DataFrame): Assessments DataFrame.
        total_by_use (dict): Dictionary to accumulate usage counts.

    Returns:
        tuple: Selected years, dictionary of usage counts by year, total usage count.
    """
    dict_year_uses = {}
    total = 0
    if selected_years is None or len(selected_years) == 0:
        # Determine available years if none are selected
        selected_years = filter_years(ASSESSMENT_DATAFRAME, COUNTRIES_DATAFRAME, selected_species, selected_family, selected_order, selected_class, selected_phylum, selected_kingdom, selected_countries)

    if selected_countries:
        # Filter by country
        ids = list(COUNTRIES_DATAFRAME[COUNTRIES_DATAFRAME['Country'].isin(selected_countries)]['ID'].unique())
        filtered_df = filtered_df[filtered_df["taxon.sis_id"].isin(ids)]
    # Filter by taxonomy
    filtered_df = filter_taxonomy(filtered_df, selected_kingdom, selected_phylum, selected_class, selected_order, selected_family, selected_species)

    for year in selected_years:
        # Filter by year
        years_dataframe = filter_some_years(filtered_df, [year])
        ids = list(years_dataframe['taxon.sis_id'].unique())
        temp_df = filtered_df[filtered_df['taxon.sis_id'].isin(ids)]
        # Count usage
        usage_counts = generate_uses_count(temp_df, USES_DATAFRAME)
        dict_year_uses[year] = usage_counts

        # Update total counts
        for use in usage_counts.keys():
            total_by_use[use] += usage_counts[use]
            total += usage_counts[use]

    return selected_years, dict_year_uses, total


def update_graph_risk(selected_species: str, 
                      selected_family: str, 
                      selected_order: str, 
                      selected_class: str, 
                      selected_phylum: str, 
                      selected_kingdom: str, 
                      selected_countries: str, 
                      selected_years: str, 
                      filtered_df: pd.DataFrame, 
                      total_by_use: dict) -> tuple:
    """
    Updates a stacked barplot grouped by risk category.

    This method filters the assessments dataframe based on selected 
    taxonomy (species, family, order, class, phylum, kingdom), countries, and years.
    It calculates the total counts of uses for each species within the selected risk 
    categories and generates a dictionary of usage counts by risk category.

    Parameters:
        selected_species (str): Selected species name.
        selected_family (str): Selected taxonomic family name.
        selected_order (str): Selected taxonomic order name.
        selected_class (str): Selected taxonomic class name.
        selected_phylum (str): Selected taxonomic phylum name.
        selected_kingdom (str): Selected taxonomic kingdom name.
        selected_countries (str): List of selected country names.
        selected_years (str): List of selected years.
        filtered_df (pd.DataFrame): Assessments DataFrame.
        total_by_use (dict): Dictionary to accumulate usage counts.

    Returns:
        tuple: Dictionary of usage counts by risk category, total usage count.
    """
    if selected_countries:
        # Filter by country
        ids = list(COUNTRIES_DATAFRAME[COUNTRIES_DATAFRAME['Country'].isin(selected_countries)]['ID'].unique())
        filtered_df = filtered_df[filtered_df["taxon.sis_id"].isin(ids)]
    # Filter by taxonomy
    filtered_df = filter_taxonomy(filtered_df, selected_kingdom, selected_phylum, selected_class, selected_order, selected_family, selected_species)
    # Filter by years
    if selected_years:
        years_dataframe = filter_some_years(filtered_df, selected_years)
        ids = list(years_dataframe['taxon.sis_id'].unique())
        filtered_df = filtered_df[filtered_df['taxon.sis_id'].isin(ids)]

    dict_categories = {}
    total = 0
    for category in UNIQUE_CATEGORIES:
        # Filter by risk category
        temp_dataframe = filtered_df[filtered_df["risk_category"] == category]
        # Count usage
        usage_counts = generate_uses_count(temp_dataframe, USES_DATAFRAME)
        dict_categories[category] = usage_counts

        # Update total counts
        for use in usage_counts.keys():
            total_by_use[use] += usage_counts[use]
            total += usage_counts[use]

    return dict_categories, total

