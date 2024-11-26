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
    

def create_bars(fig, all_uses: list, dict_uses: dict, list_selected_items: list, total: int, percentage_mode: bool):
    """
    Creates bars in figure for species usage barplot
    
    Args:
        fig (plotly.graph_objs.Figure): plotly figure
        all_uses (list): list of all possible uses, including some that might not be included in dict_uses
        dict_uses (dict): dictionary of dictionaries of frequencies of uses (see function generate_uses_count), grouped by other parameters (year, country, vulnerability category)
        list_selected_items (list): list of parameters used in dict_uses
        total (int): The total value used to calculate percentages.
        percentage_mode (bool): if true, the figure uses percentages as the x-axis

    Returns:
        None
    """
    for item in list_selected_items:
        #print(item)
        usage_counts = dict_uses[item]
        values = [usage_counts.get(use, 0) for use in all_uses]
        x_list = calculate_values_per_mode(values, total, percentage_mode)
        add_bar(fig, x_list, all_uses, item)
        
def create_figure_with_bar(dict_counts: dict, percentage_mode: bool):
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
    
def update_graph_country(selected_specie, selected_family, selected_order, selected_class, selected_phylum, 
                 selected_kingdom, selected_countries, selected_years, filtered_df, total_by_use):
    
    """
        Updates barplot graph stacked by country

    """
    total = 0
    if selected_countries is None:
        selected_countries = countries
    dict_country_uses = {}        
    for country in selected_countries:
        list_ids_country = list(countries_dataframe[countries_dataframe['Country'] == country]["ID"])
        filtered_df = filtered_df[filtered_df['taxon.sis_id'].isin(list_ids_country)]
        filtered_df = filter_taxonomy(filtered_df, selected_kingdom, selected_phylum, selected_class, selected_order, selected_family, selected_specie)
        if selected_years:
            years_dataframe = filter_some_years(filtered_df, selected_years)
            ids = list(years_dataframe['taxon.sis_id'].unique())
            filtered_df = filtered_df[filtered_df['taxon.sis_id'].isin(ids)]
        usage_counts = generate_uses_count(filtered_df, uses_dataframe)
        dict_country_uses[country] = usage_counts

        for use in usage_counts.keys():
            total_by_use[use] += usage_counts[use]
            total += usage_counts[use]

    return dict_country_uses, total

def update_graph_year(selected_specie, selected_family, selected_order, selected_class, selected_phylum, 
                 selected_kingdom, selected_countries, selected_years, filtered_df, total_by_use):
    
    """
        Updates barplot graph stacked by year
        
    """
    
    dict_year_uses = {}
    total = 0 
    if selected_years is None:
            selected_years = filter_years(dataframe, countries_dataframe, selected_specie, selected_family, selected_order, selected_class, selected_phylum, selected_kingdom, selected_countries)

    if selected_countries:
        ids = list(countries_dataframe[countries_dataframe['Country'].isin(selected_countries)]['ID'].unique())
        filtered_df = filtered_df[filtered_df["taxon.sis_id"].isin(ids)]
    filtered_df = filter_taxonomy(filtered_df, selected_kingdom, selected_phylum, selected_class, selected_order, selected_family, selected_specie)    
        
    for year in selected_years:
        years_dataframe = filter_some_years(filtered_df, [str(year)])
        ids = list(years_dataframe['taxon.sis_id'].unique())
        temp_df = filtered_df[filtered_df['taxon.sis_id'].isin(ids)]
        usage_counts = generate_uses_count(temp_df, uses_dataframe)
        dict_year_uses[year] = usage_counts
        
        for use in usage_counts.keys():
            total_by_use[use] += usage_counts[use]
            total += usage_counts[use]

    return dict_year_uses, total

def update_graph_risk(selected_specie, selected_family, selected_order, selected_class, selected_phylum, 
                 selected_kingdom, selected_countries, selected_years, filtered_df, total_by_use):
    
    """
        Updates barplot graph stacked by risk category
        
    """
    if selected_countries:
            ids = list(countries_dataframe[countries_dataframe['Country'].isin(selected_countries)]['ID'].unique())
            filtered_df = filtered_df[filtered_df["taxon.sis_id"].isin(ids)]
    filtered_df = filter_taxonomy(filtered_df, selected_kingdom, selected_phylum, selected_class, selected_order, selected_family, selected_specie)
    if selected_years:
        years_dataframe = filter_some_years(filtered_df, selected_years)
        ids = list(years_dataframe['taxon.sis_id'].unique())
        filtered_df = filtered_df[filtered_df['taxon.sis_id'].isin(ids)]
        
    dict_categories = {}
    total = 0
    for category in unique_categories:
        temp_dataframe = filtered_df[filtered_df["red_list_category"] == category]
        usage_counts = generate_uses_count(temp_dataframe, uses_dataframe)
        dict_categories[category] = usage_counts
        
        for use in usage_counts.keys():
            total_by_use[use] += usage_counts[use]
            total += usage_counts[use]
    
    return dict_categories, total