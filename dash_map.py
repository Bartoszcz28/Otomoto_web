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
from waitress import serve
# %matplotlib inline

import plotly.graph_objects as go
import dash
import dash_html_components as html
import dash_core_components as dcc
from dash.dependencies import Input, Output, State
import plotly.express as px
import dash_bootstrap_components as dbc
import dash_core_components as dcc

with open('Data_to_Otomoto.json') as file:
    Data_to_Otomoto = json.loads(file.read())
    car_brand = Data_to_Otomoto["car_brand"]
    options = Data_to_Otomoto["options"]

psql = psycopg2.connect(host='192.168.10.163', port='5432', database='Otomoto', user='barto', password='biznes')

cur = psql.cursor()
sql_otomoto = "SELECT * FROM otomoto_10;"
dat_otomoto = sqlio.read_sql_query(sql_otomoto, psql)
conn = None

car_loc = dat_otomoto[["latitude","longitude","cena","marka_pojazdu"]]

a = 0
for index, row in car_loc.iterrows():
    if (np.isnan(car_loc.at[index,'latitude']) or np.isnan(car_loc.at[index,'longitude']) 
    or np.isnan(car_loc.at[index,'cena'])):
        car_loc = car_loc.drop([index])
        a += 1
print("Drop rows where Nan from table otomoto: ", a)

# car_loc = car_loc.sample(n=1000)

car_loc = car_loc.reset_index(drop=True)

def world_new():    
    my_world = folium.Map(
    zoom_start=6,
    location=[51.9194, 19.1451], prefer_canvas=True)
    my_world = plugins.MarkerCluster().add_to(my_world)
    return my_world 

max_value_price = car_loc["cena"].max()
min_value_price = car_loc["cena"].min()
car_loc_coll=car_loc

app = dash.Dash(__name__,external_stylesheets=[dbc.themes.LITERA])

app.layout = html.Div(children=[
dbc.Row(
    dbc.Col(html.H1('Cars for sell in Otomoto',style={'textAlign': 'center','front-size' :50}))),
dbc.Row(children=[
    dbc.Col(html.Iframe(id = 'map', srcDoc = world_new().get_root().render(),
                width = '100%',height = '100%', className='map'),
            width=8, lg={'size': 8,'order': 'first'}),
    dbc.Col(style={'text-align': 'center'}, children=[
    dcc.Input(id="Price_MIN", type="number", placeholder="Price_MIN", value=1000, className='cell'),
    dcc.Input(id="Price_MAX", type="number", placeholder="Price_MAX", value=1000000, className='cell'),
    html.Button(id='max-button', n_clicks=0, children="MAX",
                   className='button-max'),
    dcc.Dropdown(id='brand_dropdown',
    options=options,

    optionHeight=35,                    
    value=['Ferrari','Lamborghini','Bentley'],                 
    disabled=False,         
    multi=True,                       
    searchable=True,               
    search_value='',                
    placeholder='Please select...',   
    clearable=True, 
    className='dropdown',         
    ),
        
    html.Button(id='my-button', n_clicks=0, children="Update", className='button-update'),
    html.Br(),
    html.Div(id='total_rows'),
    html.Br(),  
    dcc.Graph(id="fig")], width=8, lg={'size': 4, 'order': 'last'})])
    ])




@app.callback(
    [dash.dependencies.Output('map', 'srcDoc'),
     dash.dependencies.Output('total_rows', 'children'),
     dash.dependencies.Output('fig', 'figure')],
    [dash.dependencies.State('Price_MIN', 'value'),
     dash.dependencies.State('Price_MAX', 'value'),
     dash.dependencies.State('brand_dropdown', 'value')],
    [dash.dependencies.Input('my-button', 'n_clicks')]
    )
    
def Rent_Price_Limiter(Price_MIN, Price_MAX, brand, n_clicks):

    car_loc_limit = car_loc.sort_values(by=['marka_pojazdu'])
    car_loc_limit = car_loc_limit.reset_index(drop=True)
     
    for row in range(len(car_loc_limit.index)):
        if car_loc_limit.at[row,'marka_pojazdu'] in brand:
            pass
        else:
            car_loc_limit = car_loc_limit.drop([row])
    
    car_loc_limit = car_loc_limit.reset_index(drop=True)
    
    my_world = world_new()
    
    car_loc_limit = car_loc_limit[car_loc.cena.between(Price_MIN, Price_MAX, inclusive=False)]
    car_loc_limit = car_loc_limit.reset_index(drop=True)
    
    for row in range(len(car_loc_limit.index)):
        folium.CircleMarker(
            location=[car_loc_limit.at[row,'latitude'], car_loc_limit.at[row,'longitude']],
            radius=3,
            popup='Price: ' + str(car_loc_limit.at[row,'cena']) + '<br>' +str(car_loc_limit.at[row,'marka_pojazdu']) ,
            color='red',
            fill=True,
            fill_color='red',
            fill_opacity=1
        ).add_to(my_world)

    html_string = my_world.get_root().render()
    
    total_rows = len(car_loc_limit.index)
    
    pie_data = car_loc_limit['marka_pojazdu'].value_counts()
    pie_data = pie_data.to_frame()
    pie_data.reset_index(inplace=True)
    
    fig = go.Figure(data=[go.Pie(labels=pie_data['index'], values=pie_data['marka_pojazdu'], textinfo='none')])
    
    return html_string, total_rows, fig

@app.callback(
    [dash.dependencies.Output('Price_MIN', 'value'),
     dash.dependencies.Output('Price_MAX', 'value')],
    [dash.dependencies.Input('max-button', 'n_clicks')]
    )

def give_max(n_clicks_price_sell):     
    return min_value_price, max_value_price


if __name__ == '__main__':
    # app.run_server(host='0.0.0.0', port=8050)
    serve(app.server, host='0.0.0.0', port=8050) # PRODUCTION