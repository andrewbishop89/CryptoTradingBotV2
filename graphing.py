
from data_collection import *
from setup import *
from parameters import *
import plotly.graph_objects as go
import pandas as pd


def graph(klines, x=False):
    fig = go.Figure(data=[go.Candlestick(
        x=[x for x in range(0,len(klines))],
        open=klines.loc[:, 'o'], high=klines.loc[:, 'h'],
        low=klines.loc[:, 'l'], close=klines.loc[:, 'c'],
        increasing_line_color= 'green', decreasing_line_color= 'red'
    )])
    
    if x:
        fig.update_layout(
            shapes=[dict(
                x0=x, x1=x, y0=0, y1=1, xref='x', yref='paper',
                line_width=2)],
        )
    
    fig.show()
