from dash import Dash, html, dcc, callback, Output, Input
import plotly.express as px
import pandas as pd

df = pd.read_csv('data/ofac_panel.csv')

app = Dash()

metrics = ['levels', 'additions', 'removals', 'change']

app.layout = [
    html.H1(children='OFAC Time Series Explorer', style={'textAlign':'center'}),
    dcc.Dropdown(sorted(df.Country.unique()), 'China', id='dropdown-country'),
    dcc.Dropdown(metrics, 'levels', id='dropdown-metric'),
    dcc.Graph(id='graph-content')
]

@callback(
    Output('graph-content', 'figure'),
    Input('dropdown-country', 'value'),
    Input('dropdown-metric', 'value'),
)
def update_graph(selected_country, selected_metric):
    dff = df[df.Country==selected_country]
    fig = px.line(dff, x='Date', y=selected_metric)
    fig.update_layout(
        title={
            'text': f'{selected_metric.capitalize()} of entities on OFAC lists ({selected_country})',
            'x': 0.5,
            'xanchor': 'center',
            'yanchor': 'top'
        },
        xaxis_title='Monthly',
        yaxis_title=''
    )
    return fig

if __name__ == '__main__':
    app.run(debug=False)
