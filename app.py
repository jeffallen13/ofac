from dash import Dash, html, dcc, callback, Output, Input
import plotly.express as px
import pandas as pd

df = pd.read_csv('data/ofac_panel.csv')

app = Dash()

app.layout = [
    html.H1(children='OFAC Time Series Explorer', style={'textAlign':'center'}),
    dcc.Dropdown(df.Country.unique(), 'China', id='dropdown-selection'),
    dcc.Graph(id='graph-content')
]

@callback(
    Output('graph-content', 'figure'),
    Input('dropdown-selection', 'value'),
)
def update_graph(selected_country):
    dff = df[df.Country==selected_country]
    fig = px.line(dff, x='Date', y='levels')
    fig.update_layout(
        title=f'Number of entities on OFAC lists ({selected_country})',
        xaxis_title='Monthly',
        yaxis_title=''
    )
    return fig

if __name__ == '__main__':
    app.run(debug=True)
