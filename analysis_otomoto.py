import numpy as np
import pandas as pd
import psycopg2
import pandas.io.sql as sqlio
import matplotlib.pyplot as plt
import pylab as pl
import folium
import json
import os
from folium import plugins

# %matplotlib inline

import plotly.graph_objects as go
import dash
import dash_html_components as html
import dash_core_components as dcc
from dash.dependencies import Input, Output, State
import plotly.express as px
import dash_bootstrap_components as dbc
import dash_core_components as dcc
from waitress import serve

with open('Data_to_Otomoto.json') as file:
    Data_to_Otomoto = json.loads(file.read())
car_brand = Data_to_Otomoto["car_brand"]
options = Data_to_Otomoto["options"]

psql = psycopg2.connect(host='192.168.10.163', port='5432', database='Otomoto', user='barto', password='biznes')


cur = psql.cursor()
sql_line_graph = "SELECT AVG(cena), rok_produkcji, marka_pojazdu FROM otomoto_10 GROUP BY rok_produkcji, marka_pojazdu ORDER BY rok_produkcji DESC ;"
line_graph = sqlio.read_sql_query(sql_line_graph, psql)
sql_scatter_plot = "SELECT cena, przebieg, marka_pojazdu FROM otomoto_10;"
scatter_plot = sqlio.read_sql_query(sql_scatter_plot, psql)
conn = None

a = 0
for index, row in scatter_plot.iterrows():
    if (np.isnan(scatter_plot.at[index,'przebieg']) or np.isnan(scatter_plot.at[index,'cena'])):
        scatter_plot = scatter_plot.drop([index])
        a += 1
print("Drop rows where Nan from table otomoto: ", a)

scatter_plot = scatter_plot.reset_index(drop=True)

app = dash.Dash(__name__,external_stylesheets=[dbc.themes.LITERA])

app.layout = html.Div(children=[
    html.H1('Analysis of cars for sale (Otomoto)',style={'textAlign': 'center','front-size' :50}),
    dcc.Dropdown(id='brand_dropdown',
    options=options,

    optionHeight=35,
    value='BMW',
    disabled=False,
    multi=False,
    searchable=True,
    search_value='',
    placeholder='Please select...',
    clearable=True,
    className='dropdown',  
    ),
                                        
    html.Br(),
    html.Div(className='text', children=[
            html.Span('Number of years from which we have data: '),
            html.Span(id='total_rows_line_graph_data'),]),
    dcc.Graph(id='line_graph_fig'),
    html.Div(className='text', children=[
            html.Span('Number of cars used to generate graph: '),
            html.Span(id='total_rows_scatter_plot_data'),]),
    dcc.Graph(id='scatter_plot_fig')

    ])

@app.callback(
    [Output(component_id='line_graph_fig', component_property='figure'),
    Output(component_id='scatter_plot_fig', component_property='figure'),
    Output(component_id='total_rows_line_graph_data', component_property='children'),
    Output(component_id='total_rows_scatter_plot_data', component_property='children')],
    [Input(component_id='brand_dropdown', component_property='value')]
)

def build_graph(brand_chosen):
    
    line_graph_data = line_graph.loc[line_graph['marka_pojazdu'] == brand_chosen]
    line_graph_fig = go.Figure([go.Scatter(x=line_graph_data['rok_produkcji'], y=line_graph_data['avg'], 
                                mode='lines+markers')])
    
    line_graph_fig.update_layout(
    title="Price distribution depending on the year of car production",
    xaxis_title="Year of car production",
    yaxis_title="Car price")
    
    scatter_plot_data = scatter_plot.loc[scatter_plot['marka_pojazdu'] == brand_chosen]
    scatter_plot_fig = px.scatter(scatter_plot_data, x=scatter_plot_data['przebieg'], 
                     y=scatter_plot_data['cena'], trendline="ols")
    scatter_plot_fig.update_layout(
    title="Price distribution depending on the car mileage",
    xaxis_title="Car mileage",
    yaxis_title="Car price")
    
    total_rows_line_graph_data = len(line_graph_data.index) 
    total_rows_scatter_plot_data = len(scatter_plot_data.index) 
    
    return line_graph_fig, scatter_plot_fig, total_rows_line_graph_data, total_rows_scatter_plot_data


if __name__ == '__main__':
    app.run_server(host='0.0.0.0')
    serve(app.server, host='0.0.0.0', port=8051) # PRODUCTION