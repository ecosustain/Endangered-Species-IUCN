#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Nov  7 17:56:11 2024

@author: rafaelom
"""

import pandas as pd
import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
import plotly.graph_objects as go
import plotly.express as px
import geopandas as gpd
#import matplotlib.pyplot as plt
import datetime
import os
import gc

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

def generate_uses_count(dataframe: pd.DataFrame, uses_dataframe: pd.DataFrame) -> dict:
    ids = list(dataframe['taxon.sis_id'].unique())
    filtered_dataframe = uses_dataframe[uses_dataframe['ID'].isin(ids)]
    usage_counts = filtered_dataframe['Use'].value_counts().to_dict()
    try:
        del usage_counts['Unknown']
    except:
        pass
    return usage_counts

def create_bars(fig, all_uses: list, dict_uses: dict, list_selected_items: list, total: int, percentage_mode: bool):
    for item in list_selected_items:
        #print(item)
        usage_counts = dict_uses[item]
        values = [usage_counts.get(use, 0) for use in all_uses]
        x_list = calculate_values_per_mode(values, total, percentage_mode)
        add_bar(fig, x_list, all_uses, item)
        
def create_figure_with_bar(dict_counts: dict, percentage_mode: bool):
    categories = list(dict_counts.keys())
    values = list(dict_counts.values())
    values = calculate_values_per_mode(values, sum(values), percentage_mode)
    return go.Figure(go.Bar(
        x=values,
        y=categories,
        orientation='h',
        marker=dict(color='skyblue')
    ))
    
def read_shapefiles(base_dir):
    shapefiles_dir = os.path.join(base_dir, "../data/shapefiles")
    
    # Lista para armazenar os GeoDataFrames
    geo_dataframes = []
    
    # Colunas que você deseja manter
    columns_to_keep = ["sci_name", "geometry"]  # Inclua 'geometry' para manter a geometria
    
    file_path = os.path.join(shapefiles_dir, 'FW_FISH_PART1.shp')
    gdf =  gpd.read_file(file_path, encoding='utf-8')
    gdf = gdf[columns_to_keep]
    return gdf
    
    # Percorrer todos os arquivos no diretório
    #for file in os.listdir(shapefiles_dir):
        #if file.endswith(".shp"):  # Verificar se é um shapefile
            #file_path = os.path.join(shapefiles_dir, file)
            #gdf = gpd.read_file(file_path, encoding="utf-8")
            #gdf = gdf[columns_to_keep]
            #geo_dataframes.append(gdf)
    
    # Concatenar todos os GeoDataFrames em um único
    final_gdf = gpd.GeoDataFrame(pd.concat(geo_dataframes, ignore_index=True))
    del geo_dataframes
    gc.collect()
    return final_gdf

base_dir = os.path.dirname(os.path.abspath(__file__))
gdf = read_shapefiles(base_dir)
dataframe = pd.read_csv(os.path.join(base_dir, "../data/assessments.csv"))
uses_dataframe = pd.read_csv(os.path.join(base_dir, "../data/uses.csv"))
countries_dataframe = pd.read_csv(os.path.join(base_dir, "../data/countries.csv"))
unique_ids = list(dataframe['taxon.sis_id'].unique())
unique_years = create_list_unique_years(dataframe)
countries = list(countries_dataframe["Country"].unique())
unique_categories = list(dataframe["risk_category"].dropna().unique())
species = list(dataframe['taxon.scientific_name'].unique())

# Inicialização do app Dash
app = dash.Dash(__name__)

# Layout atualizado do app Dash
app.layout = html.Div([
    # Cabeçalho Global
    html.Div([
        html.H1("Interactive Dashboards for Species Analysis", style={
            "font-size": "3.5em",
            "font-weight": "bold",
            "color": "#FFFFFF",
            "margin": "0",
            "margin-bottom": "25px"
        }),
        html.A("Interactive Species Use Chart", href="#stacked-bar-chart", style={
            "font-size": "1em",
            "font-weight": "bold",
            "color": "#FFF",
            "background-color": "#DA2A1C",
            "padding": "7px",
            "border-radius": "5px",
            "text-decoration": "none",
            "margin-right": "20px",
        }),
        html.A("Risk of Extinction of Species", href="#risk-graph", style={
            "font-size": "1em",
            "font-weight": "bold",
            "color": "#FFF",
            "background-color": "#DA2A1C",
            "padding": "7px",
            "border-radius": "5px",
            "text-decoration": "none",
            "margin-right": "20px",
        }),
        html.A("Species Distribution", href="#distribution-map", style={
            "font-size": "1em",
            "font-weight": "bold",
            "color": "#FFF",
            "background-color": "#DA2A1C",
            "padding": "7px",
            "border-radius": "5px",
            "text-decoration": "none",
        })
    ], style={
        "text-align": "center",
        "padding": "20px 20px",
        "background-color": "#AD180D",
        "border-bottom": "2px solid #DA2A1C"
    }),

    # Caixa principal com filtros e gráfico
    html.Div([
    	html.Div([
            html.H2("Interactive Species Use Chart", style={
                "text-align": "center",
                "color": "#AD180D",
                "margin-bottom": "20px",
                "font-size": "2.5em",
                "font-weight": "bold",
            })
        ], style={"width": "100%"}),
        # Filtros e Opções
        html.Div([
            html.H3("Filters and Options", style={
            "color": "#DA2A1C",
            "font-size": "22px",
            "text-align": "center",
            "text-weight": "bold"
            }),
            html.Div([
                html.H4("Filtering by Country", style={
                "color": "#AD180D"
                }),
                dcc.Dropdown(
                    id="country-dropdown",
                    options=[{"label": c, "value": c} for c in countries],
                    placeholder="Select a country",
                    multi=True,
                    style={"margin-bottom": "10px"}
                )
            ], style={"margin-bottom": "20px"}),

            html.Div([
                html.H4("Filtering by Taxonomy", style={"color": "#AD180D"}),
                dcc.Dropdown(id="kingdom-dropdown", placeholder="Select a kingdom", style={"margin-bottom": "10px"}),
                dcc.Dropdown(id="phylum-dropdown", placeholder="Select a phylum", style={"margin-bottom": "10px"}),
                dcc.Dropdown(id="class-dropdown", placeholder="Select a class", style={"margin-bottom": "10px"}),
                dcc.Dropdown(id="order-dropdown", placeholder="Select an order", style={"margin-bottom": "10px"}),
                dcc.Dropdown(id="family-dropdown", placeholder="Select a family", style={"margin-bottom": "10px"}),
                dcc.Dropdown(id="specie-dropdown", placeholder="Select a species", style={"margin-bottom": "10px"}),
            ], style={"margin-bottom": "20px"}),

            html.Div([
                html.H4("Filtering by Year", style={"color": "#AD180D"}),
                dcc.Dropdown(
                    id="year-dropdown",
                    options=[{"label": year, "value": year} for year in unique_years],
                    placeholder="Select one or more years",
                    multi=True,
                    style={"margin-bottom": "10px"}
                )
            ]),

            html.Div([
                html.H4("View Options", style={"color": "#AD180D"}),
                dcc.Checklist(
                    id="default-mode-checklist",
                    options=[{"label": "Accumulated graph", "value": "default_mode"}],
                    value=["default_mode"],
                    labelStyle={'display': 'block', "margin-bottom": "5px"}
                ),
                dcc.Checklist(
                    id="country-mode-checklist",
                    options=[{"label": "Stacked chart by country", "value": "country_mode"}],
                    labelStyle={"display": "block", "margin-bottom": "5px"}
                ),
                dcc.Checklist(
                    id="year-mode-checklist",
                    options=[{"label": "Stacked chart by year", "value": "year_mode"}],
                    labelStyle={"display": "block", "margin-bottom": "5px"}
                ),
                dcc.Checklist(
                    id="category-checklist",
                    options=[{"label": "Stacked chart by risk category", "value": "category_mode"}],
                    labelStyle={"display": "block", "margin-bottom": "5px"}
                ),
                html.H4("Value Options", style={"color": "#AD180D"}),
                dcc.Checklist(
                    id="absolute-mode-checklist",
                    options=[{"label": "Absolute Values", "value": "absolute_mode"}],
                    value=["absolute_mode"],
                    labelStyle={'display': 'block', "margin-bottom": "5px"}
                ),
                dcc.Checklist(
                    id="percentage-mode-checklist",
                    options=[{"label": "Percentage Values", "value": "percentage_mode"}],
                    labelStyle={"display": "block", "margin-bottom": "5px"}
                )
            ])
        ], style={
            "width": "30%",
            "background-color": "#f9f9f9",
            "padding": "0px 20px 20px 20px",
            "border": "1px solid #ddd",
            "border-radius": "5px",
            "box-shadow": "2px 2px 5px #ccc"
        }),

        # Gráfico
        dcc.Graph(
            id="stacked-bar-chart",
            style={
                "height": "600px",
                "width": "65%",
                "border": "1px solid #ddd",
                "border-radius": "5px",
                "padding": "10px",
                "background-color": "#ffffff",
                "box-shadow": "2px 2px 5px #ccc"
            }
        )
    ], style={
        "display": "flex",
        "flex-direction": "row",
        "justify-content": "space-between",
        "flex-wrap": "wrap", 
        "align-items": "flex-start",
        "margin": "20px auto",
        "width": "90%",
        "background-color": "rgb(250, 250, 250)",
        "padding": "20px",
        "border-radius": "10px"
    }),
    
    # Caixa principal com filtros e gráfico
    html.Div([
        html.Div([
            html.H2("Risk of Extinction of Species Over the Years", style={
                "text-align": "center",
                "color": "#AD180D",
                "margin-bottom": "20px",
                "font-size": "2.5em",
                "font-weight": "bold",
            })
        ], style={"width": "100%"}),

        html.Div([

            html.Div([
                html.H4("Search for a Species", style={"color": "#DA2A1C",
                                "font-size": "22px",
                                "margin-bottom": "10px"}),
                dcc.Input(
                    id="species-input",
                    type="text",
                    placeholder="Type a scientific species name",
                    style={"margin-bottom": "10px", "width": "80%", "padding": "8px"},
                ),
                html.Button(
                    "Submit",
                    id="submit-button",
                    style={
                        "background-color": "#DA2A1C",
                        "color": "#fff",
                        "border": "none",
                        "padding": "10px 20px",
                        "margin-top": "10px",
                        "margin-left": "10px",
                        "cursor": "pointer",
                        "border-radius": "5px",
                        "font-size": "16px"
                    },
                ),
                html.Div(
                    id="error-message",
                    style={"color": "red", "margin-top": "10px", "font-size": "14px"}
                )
            ], style={"margin-bottom": "20px"})
        ]
        , style={
            "width": "60%",
            "background-color": "#f9f9f9",
            "padding": "0px 20px 10px 20px",
            "border": "1px solid #ddd",
            "border-radius": "5px",
            "box-shadow": "2px 2px 5px #ccc",
            "margin-bottom": "10px"
        }),

        # Gráfico
        dcc.Graph(
            id="risk-graph",
            style={
                "height": "600px",
                "width": "60%",
                "border": "1px solid #ddd",
                "border-radius": "5px",
                "padding": "10px",
                "background-color": "#ffffff",
                "box-shadow": "2px 2px 5px #ccc"
            }
        )
    ], style={
        "display": "flex",
        "flex-direction": "row",
        "justify-content": "center",
        "flex-wrap": "wrap", 
        "align-items": "center",
        "align-content": "center", 
        "margin": "20px auto",
        "width": "90%",
        "background-color": "rgb(250, 250, 250)",
        "padding": "20px",
        "border-radius": "10px"
    }),
    
    html.Div([
        html.Div([
            html.H2("Species Distribution", style={
                "text-align": "center",
                "color": "#AD180D",
                "margin-bottom": "20px",
                "font-size": "2.5em",
                "font-weight": "bold",
            })
        ], style={"width": "100%"}),

        html.Div([

            html.Div([
                html.H4("Search for a Species", style={"color": "#DA2A1C",
                                "font-size": "22px",
                                "margin-bottom": "10px"}),
                dcc.Input(
                    id="species-input2",
                    type="text",
                    placeholder="Type a scientific species name",
                    style={"margin-bottom": "10px", "width": "80%", "padding": "8px"},
                ),
                html.Button(
                    "Submit",
                    id="submit-button2",
                    style={
                        "background-color": "#DA2A1C",
                        "color": "#fff",
                        "border": "none",
                        "padding": "10px 20px",
                        "margin-top": "10px",
                        "margin-left": "10px",
                        "cursor": "pointer",
                        "border-radius": "5px",
                        "font-size": "16px"
                    },
                ),
                html.Div(
                    id="error-message2",
                    style={"color": "red", "margin-top": "10px", "font-size": "14px"}
                )
            ], style={"margin-bottom": "20px"})
        ]
        , style={
            "width": "60%",
            "background-color": "#f9f9f9",
            "padding": "0px 20px 10px 20px",
            "border": "1px solid #ddd",
            "border-radius": "5px",
            "box-shadow": "2px 2px 5px #ccc",
            "margin-bottom": "10px"
        }),

        # Gráfico
        dcc.Graph(
            id="distribution-map",
            style={
                "height": "600px",
                "width": "60%",
                "border": "1px solid #ddd",
                "border-radius": "5px",
                "padding": "10px",
                "background-color": "#ffffff",
                "box-shadow": "2px 2px 5px #ccc"
            }
        )
    ], style={
        "display": "flex",
        "flex-direction": "row",
        "justify-content": "center",
        "flex-wrap": "wrap", 
        "align-items": "center",
        "align-content": "center", 
        "margin": "20px auto",
        "width": "90%",
        "background-color": "rgb(250, 250, 250)",
        "padding": "20px",
        "border-radius": "10px"
    }),

    # Rodapé
    html.Div([], style={
        "background-color": "#AD180D",
        "height": "50px",
        "border-top": "2px solid #DA2A1C"
    })
], style={"font-family": "Arial, sans-serif", "background-color": "#fff", "margin": "0 auto"})


def filter_dataframe_by_specie(df, specie):
    mapping1 = {'NE': 0,
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
    df_plot['categoriaOrdem'] = df_plot['risk_category'].map(mapping1)
    df_plot.drop('year_published', axis=1, inplace=True)
    df_plot = df_plot.ffill()
    return df_plot
    
@app.callback(
    [Output("risk-graph", "figure"), Output("error-message", "children")],
    [Input("submit-button", "n_clicks"), Input("species-input", "n_submit")],
    State("species-input", "value")
)
def update_graph(n_clicks, n_submit, input_value):
    if input_value is None or input_value.strip() == "":
        return dash.no_update, ""

    if input_value not in species:
        return dash.no_update, f"Error: '{input_value}' is not a valid species."

    mapping3 = {'No Risk Data': 0,
            'Least Concern': 1,
            'Little Threatened': 2,
            'Vulnerable': 3,
            'Endangered': 4,
            'Critically Endangered': 5,
            'Regionally Extinct': 6,
            'Extinct in the Wild': 7,
            'Extinct': 8}
    fig = go.Figure()
    df_plot = filter_dataframe_by_specie(dataframe, input_value)
    fig.add_trace(go.Scatter(x=df_plot['Years'], y=df_plot['categoriaOrdem'],
                             mode='lines',
                             line=dict(color='darkred'),
                             name=input_value))
    fig.update_layout(xaxis_title='Years',
                      yaxis_title='Risk Category',
                      yaxis_range=[0,8],
                      yaxis=dict(tickmode='array',
                                 tickvals=list(mapping3.values()),
                                 ticktext=list(mapping3.keys())),
                      xaxis_showgrid=False,
                      yaxis_showgrid=False)
    
    return fig, ""
    
@app.callback(
    [Output("distribution-map", "figure"), Output("error-message2", "children")],
    [Input("submit-button2", "n_clicks"), Input("species-input2", "n_submit")],
    State("species-input2", "value")
)
def update_map(n_clicks, n_submit, input_value):
    if input_value is None or input_value.strip() == "":
        return dash.no_update, ""

    if input_value not in species:
        return dash.no_update, f"Error: '{input_value}' is not a valid species."

    filtered_gdf = gdf[gdf['sci_name'] == input_value]
    filtered_gdf['id'] = filtered_gdf.index
    
    fig = px.choropleth(
        filtered_gdf,
        geojson=filtered_gdf.__geo_interface__,
        locations='id',
        color_discrete_map= {input_value:'#871108'},
        color='sci_name',
    )
    # title_text='Distribuição da espécie ' + input_value,
    fig.update_layout(
        showlegend = False,
        geo=dict(
            showframe=False,
            showcoastlines=False,
            showcountries=True,
            projection_type='equirectangular',
            fitbounds="geojson",
        ),
        annotations = [dict(
            x=0.55,
            y=0.1,
            xref='paper',
            yref='paper',
            showarrow = False
        )]
    )
    return fig, ""

@app.callback(
    [Output("default-mode-checklist", "value"), Output("country-mode-checklist", "value"), Output("year-mode-checklist", "value"), Output("category-checklist", "value")],
    [Input("default-mode-checklist", "value"), Input("country-mode-checklist", "value"), Input("year-mode-checklist", "value"), Input("category-checklist", "value")],
)
def update_mode_checklists(selected_default_mode, selected_country_mode, selected_year_mode, selected_category_mode):
    ctx = dash.callback_context  # contexto do callback para identificar o acionador

    triggered_id = ctx.triggered[0]["prop_id"].split(".")[0]

    # Se o checklist de país foi acionado, ajusta para "stacked_country" e limpa o de ano
    if triggered_id == "country-mode-checklist" and selected_country_mode:  # se estiver selecionado, aplica "stacked_country"
        return [], ["country_mode"], [], []

    # Se o checklist de ano foi acionado, ajusta para "stacked_year" e limpa o de país
    elif triggered_id == "year-mode-checklist" and selected_year_mode:  # se estiver selecionado, aplica "stacked_year"
        return [], [], ["year_mode"], []

        
    elif triggered_id == "category-checklist" and selected_category_mode:  # se estiver selecionado, aplica "stacked_year"
        return [], [], [], ["category_mode"]
    return ["default_mode"], [], [], []

@app.callback(
    [Output("absolute-mode-checklist", "value"),
     Output("percentage-mode-checklist", "value")],
    [Input("absolute-mode-checklist", "value"),
     Input("percentage-mode-checklist", "value")]
)
def update_values_mode_checklists(absolute_value, percentage_value):
    ctx = dash.callback_context
    
    if not ctx.triggered:
        # Inicia com o modo padrão marcado
        return ["absolute_mode"], []

    triggered_id = ctx.triggered[0]["prop_id"].split(".")[0]

    if triggered_id == "absolute-mode-checklist" and absolute_value:
        return ["absolute_mode"], []

    elif triggered_id == "percentage-mode-checklist" and percentage_value:
        return [], ["percentage_mode"]

    return ["absolute_mode"], []  # Caso todos sejam desmarcados
        
# Callback para atualizar o dropdown de reino baseado no país selecionado
@app.callback(
    Output("kingdom-dropdown", "options"),
    [Input("country-dropdown", "value")]
)
def update_kingdom_options(selected_countries):
    #if not selected_countries:
        #return []
    kingdoms = dataframe["taxon.kingdom_name"].unique()
    return [{"label": k, "value": k} for k in kingdoms]

# Callbacks para atualizar os dropdowns sequencialmente (reino, filo, classe, ordem, família)
@app.callback(
    Output("phylum-dropdown", "options"),
    [Input("kingdom-dropdown", "value"), Input("country-dropdown", "value")]
)
def update_phylum_options(selected_kingdom, selected_countries):
    if not selected_kingdom:
        return []
    phyla = dataframe[dataframe["taxon.kingdom_name"] == selected_kingdom]["taxon.phylum_name"].unique()
    return [{"label": p, "value": p} for p in phyla]

@app.callback(
    Output("class-dropdown", "options"),
    [Input("phylum-dropdown", "value"), Input("kingdom-dropdown", "value")]
)
def update_class_options(selected_phylum, selected_kingdom):
    if selected_phylum is None:
        return []
    classes = dataframe[(dataframe["taxon.kingdom_name"] == selected_kingdom) & 
                 (dataframe["taxon.phylum_name"] == selected_phylum)]["taxon.class_name"].unique()
    return [{"label": c, "value": c} for c in classes]

@app.callback(
    Output("order-dropdown", "options"),
    [Input("class-dropdown", "value"), Input("phylum-dropdown", "value"), Input("kingdom-dropdown", "value")]
)
def update_order_options(selected_class, selected_phylum, selected_kingdom):
    if selected_class is None:
        return []
    orders = dataframe[(dataframe["taxon.kingdom_name"] == selected_kingdom) & 
                (dataframe["taxon.phylum_name"] == selected_phylum) &
                (dataframe["taxon.class_name"] == selected_class)]["taxon.order_name"].unique()
    return [{"label": o, "value": o} for o in orders]

@app.callback(
    Output("family-dropdown", "options"),
    [Input("order-dropdown", "value"), Input("class-dropdown", "value"), Input("phylum-dropdown", "value"), Input("kingdom-dropdown", "value")]
)
def update_family_options(selected_order, selected_class, selected_phylum, selected_kingdom):
    if selected_order is None:
        return []
    families = dataframe[(dataframe["taxon.kingdom_name"] == selected_kingdom) & 
                  (dataframe["taxon.phylum_name"] == selected_phylum) &
                  (dataframe["taxon.class_name"] == selected_class) &
                  (dataframe["taxon.order_name"] == selected_order)]["taxon.family_name"].unique()
    return [{"label": f, "value": f} for f in families]

@app.callback(
    Output("specie-dropdown", "options"),
    [Input("family-dropdown", "value"), Input("order-dropdown", "value"), Input("class-dropdown", "value"), Input("phylum-dropdown", "value"), Input("kingdom-dropdown", "value")]
)
def update_specie_options(selected_family, selected_order, selected_class, selected_phylum, selected_kingdom):
    if selected_family is None:
        return []
    species = dataframe[(dataframe["taxon.kingdom_name"] == selected_kingdom) & 
                  (dataframe["taxon.phylum_name"] == selected_phylum) &
                  (dataframe["taxon.class_name"] == selected_class) &
                  (dataframe["taxon.order_name"] == selected_order) &
                  (dataframe["taxon.family_name"] == selected_family)]["taxon.scientific_name"].unique()
    return [{"label": f, "value": f} for f in species]

def filter_years(dataframe, countries_dataframe, selected_specie, selected_family, selected_order, selected_class, selected_phylum, selected_kingdom, selected_countries):
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
    #ids_countries = []
    if selected_countries:
        ids_countries = list(countries_dataframe[countries_dataframe['Country'].isin(selected_countries)]['ID'].dropna().unique())
    if selected_countries and selected_kingdom:    
        ids = list(set(ids_countries) & set(ids_species))
        species = list(dataframe[dataframe["taxon.sis_id"].isin(ids)]["year_published"].dropna().unique())
    elif selected_kingdom:
        species = list(dataframe[dataframe["taxon.sis_id"].isin(ids_species)]["year_published"].dropna().unique())
    elif selected_countries:
        species = list(dataframe[dataframe["taxon.sis_id"].isin(ids_countries)]["year_published"].dropna().unique())
    else: 
        species = list(dataframe["year_published"].dropna().unique())
        #print(species)
    species.sort()
    return species
    

@app.callback(
    Output("year-dropdown", "options"),
    [Input("specie-dropdown", "value"),
     Input("family-dropdown", "value"), Input("order-dropdown", "value"),
     Input("class-dropdown", "value"), Input("phylum-dropdown", "value"),
     Input("kingdom-dropdown", "value"), Input("country-dropdown", "value")]
)
def update_years_options(selected_specie, selected_family, selected_order, selected_class, selected_phylum, selected_kingdom, selected_countries):
    years = filter_years(dataframe, countries_dataframe, selected_specie, selected_family, selected_order, selected_class, selected_phylum, selected_kingdom, selected_countries)
    return [{"label": f, "value": f} for f in years]



# Callback para atualizar o gráfico de barras
@app.callback(
    Output("stacked-bar-chart", "figure"),
    [Input("specie-dropdown", "value"),
     Input("family-dropdown", "value"), Input("order-dropdown", "value"),
     Input("class-dropdown", "value"), Input("phylum-dropdown", "value"),
     Input("kingdom-dropdown", "value"), Input("country-dropdown", "value"),
     Input("year-dropdown", "value"), 
     Input("country-mode-checklist", "value"), Input("year-mode-checklist", "value"), 
     Input("percentage-mode-checklist", "value"), Input("category-checklist", "value")]
)
def update_graph(selected_specie, selected_family, selected_order, selected_class, selected_phylum, 
                 selected_kingdom, selected_countries, selected_years, country_mode, year_mode, percentage_mode, category_mode):
    filtered_df = dataframe.copy()
    fig = go.Figure()
    total_by_use = {'Food': 0,
                    'Pets/display animals, horticulture': 0,
                    'Medicine - human & veterinary': 0,
                    'Others': 0,
                    'Sport hunting/specimen collecting': 0,
                    'Construction or structural materials': 0,
                    'Fuels': 0,
                    'Handicrafts, jewellery, etc.': 0,
                    'Chemicals': 0,
                    'Wearing apparel, accessories': 0,
                    'Research': 0}
    total = 0
    all_uses = list(total_by_use.keys())
    if country_mode:
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

        # Calcular os percentuais para cada país
        create_bars(fig, all_uses, dict_country_uses, selected_countries, total, percentage_mode)
        if percentage_mode:
            update_fig_layout(fig, "Species Use by Country", "Percentage (%)", "Categories")
        else:
            update_fig_layout(fig, "Species Use by Country", "Count", "Categories")

    elif year_mode:
        dict_year_uses = {}
        
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
        # Calcular os percentuais para cada país
        create_bars(fig, all_uses, dict_year_uses, selected_years, total, percentage_mode)

        if percentage_mode:
            update_fig_layout(fig, "Species Use by Year", "Percentage (%)", "Categories")
        else:
            update_fig_layout(fig, "Species Use by Year", "Count", "Categories")
    elif category_mode:
        if selected_countries:
            ids = list(countries_dataframe[countries_dataframe['Country'].isin(selected_countries)]['ID'].unique())
            filtered_df = filtered_df[filtered_df["taxon.sis_id"].isin(ids)]
        filtered_df = filter_taxonomy(filtered_df, selected_kingdom, selected_phylum, selected_class, selected_order, selected_family, selected_specie)
        if selected_years:
            years_dataframe = filter_some_years(filtered_df, selected_years)
            ids = list(years_dataframe['taxon.sis_id'].unique())
            filtered_df = filtered_df[filtered_df['taxon.sis_id'].isin(ids)]
            
        dict_categories = {}
        for category in unique_categories:
            temp_dataframe = filtered_df[filtered_df["red_list_category"] == category]
            usage_counts = generate_uses_count(temp_dataframe, uses_dataframe)
            dict_categories[category] = usage_counts
            
            for use in usage_counts.keys():
                total_by_use[use] += usage_counts[use]
                total += usage_counts[use]
                
        create_bars(fig, all_uses, dict_categories, unique_categories, total, percentage_mode)
        if percentage_mode:
            update_fig_layout(fig, "Use of Species by Risk Category", "Percentage (%)", "Categories")
        else:
            update_fig_layout(fig, "Use of Species by Risk Category", "Count", "Categories")
        
    else:   
        if selected_countries:
            ids = list(countries_dataframe[countries_dataframe['Country'].isin(selected_countries)]['ID'].unique())
            filtered_df = filtered_df[filtered_df["taxon.sis_id"].isin(ids)]
        filtered_df = filter_taxonomy(filtered_df, selected_kingdom, selected_phylum, selected_class, selected_order, selected_family, selected_specie)
        if selected_years:
            years_dataframe = filter_some_years(filtered_df, selected_years)
            ids = list(years_dataframe['taxon.sis_id'].unique())
            filtered_df = filtered_df[filtered_df['taxon.sis_id'].isin(ids)]

        # Contar o número de espécies por categoria de uso
        usage_counts = generate_uses_count(filtered_df, uses_dataframe)
        for use in usage_counts.keys():
            total_by_use[use] += usage_counts[use]
            total += usage_counts[use]

        fig = create_figure_with_bar(total_by_use, percentage_mode)
        
        if percentage_mode:
            update_fig_layout(fig, "Use of Species", "Percentage (%)", "Categories")
        else:
            update_fig_layout(fig, "Use of Species", "Count", "Categories")
    
    return fig

if __name__ == "__main__":
    app.run_server(debug=True, host="0.0.0.0", port=8040)

