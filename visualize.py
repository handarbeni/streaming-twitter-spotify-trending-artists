import dash
from dash.dependencies import Output, Input
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objs as go
import datetime
import pandas as pd
from cassandraConnect import CassandraConnect

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

cassandra = CassandraConnect('spotify')
minutes = 60 # number of minutes back to show

app_color = {
    "graph_bg": "rgb(221, 236, 255)",
    "graph_line": "rgb(8, 70, 151)",
    "graph_font":"rgb(2, 29, 65)"
}

chart_colors = [
    '#664DFF',
    '#893BFF',
    '#3CC5E8',
    '#2C93E8',
    '#0BEBDD',
    '#0073FF',
    '#00BDFF',
    '#A5E82C',
    '#FFBD42',
    '#FFCA30',
    '#664DFF',
    '#893BFF',
    '#3CC5E8',
    '#2C93E8',
    '#0BEBDD',
    '#0073FF',
    '#00BDFF',
    '#A5E82C',
    '#FFBD42',
    '#FFCA30'
]

app = dash.Dash(
    __name__
)
app.css.append_css({
    "external_url": "https://maxcdn.bootstrapcdn.com/bootstrap/4.3.1/css/bootstrap.min.css"
})
app.layout = html.Div(
    [
      # header
        html.Div(
            [
                html.Div(
                    [
                        html.H1(
                            "TRENDING MUSIC ARTISTS ON TWITTER",
                        ),
                        html.P(
                            "This app streams tweets about  music (open.spotify.com) in real time, then use Spotify API to get information about the music, and displays live charts to see the top trending artist",
                            className="app__header__title--grey",
                        ),
                    ],
                    className="app__header__desc",
                )
            ]
        ),
        html.Div(
                [
                    html.Span(
                        "Total number of tweets streamed during last 60 seconds: ",
                        className="font-weight-bold",
                    ),
                    html.Span(
                        "0",
                        id="total-tweets",
                        style={'font-size':'25px'},
                    ),
                ],
                className="auto__container",
                style={
                    'font-size':'20px'
                },
            ),
        html.Div(
                [
                    html.Span(
                        "Date: ",
                        className="font-weight-bold"
                    ),
                    html.Span(
                        "DD/MM/YY",
                        id="date",
                        className="auto__p",
                        style={
                            'font-size':'25px',
                            'margin-top': '10px'
                        },
                    ),
                ],
                className="auto__container",
                style={
                    'font-size':'20px'
                },
            ),
        html.Div(
                [
                    html.Span(
                        "Time: ",
                        className="font-weight-bold"
                    ),
                    html.Span(
                        "00:00:00",
                        id="time",
                        className="auto__p",
                        style={
                            'font-size':'25px',
                            'margin-top': '10px'
                        },
                    ),
                ],
                className="auto__container",
                style={
                    'margin-bottom': '20px',
                    'font-size':'20px'
                },
            ),
        dcc.Graph(
            id='live-graph',
            animate=False,
            figure=go.Figure(
                layout=go.Layout(
                    plot_bgcolor=app_color["graph_bg"],
                    paper_bgcolor=app_color["graph_bg"],
                )
            )
        ),
        dcc.Interval(
            id='graph-update',
            interval=5*1000, # update once every second
            n_intervals=0
        ),
    ],
    className='container mt-xl-5'
)

@app.callback(
    Output('live-graph', 'figure'),
    [Input('graph-update', 'n_intervals')])
def update_graph_bar(n):
    try:
        rows = cassandra.get_data(minutes, 'artistcount')

        # Create dataframe
        df = []
        time_now = datetime.datetime.now().replace(microsecond=0).isoformat()
        for row in rows:
            df.append({'date': time_now, 'artist': row.artist, 'total_count': row.total_count})
        df = pd.DataFrame(df)

        # Parse datetime
        df.date = pd.to_datetime(df.date, format='%Y/%m/%d %H:%M:%S', errors='ignore')

        sorted_df = df.sort_values('total_count', ascending=False).head(20)

        # Take x, y from last 10 minutes, update
        X = sorted_df.total_count.values
        Y = sorted_df.artist.values
        print(X)
        print(Y)
        # Define bars
        data = go.Bar(
            x=X,
            y=Y,
            name='Top 10 Artist',
            orientation='h',
            marker=dict(color=chart_colors[::-1]),
            #opacity=0.6
        )

        layout = go.Layout(

            title='Twitter mentions of Spotify',
            xaxis=dict(
                tickfont=dict(
                    size=15,
                    color='rgb(107, 107, 107)'
                ),
                autorange= True,
                title= dict(
                    text='Number of tweets',
                    font=dict(size=20)
                )
            ),
            yaxis=dict(
                tickfont=dict(
                    size=15,
                ),
                autorange=True,
                title=dict(
                    text='Number of tweets',
                    font=dict(size=20)
                )
            ),
            height= 700,
            plot_bgcolor=app_color["graph_bg"],
            paper_bgcolor=app_color["graph_bg"],
            font={"color": app_color["graph_font"]},
            autosize=True,
            margin=go.layout.Margin(
                l=200,
                r=25,
                b=75,
                t=55,
                pad=4
            ),
        )

        return {'data': [data], "layout": layout}


    except Exception as e:
        with open('errors.txt','a') as f:
            f.write(str(e))
            f.write('\n')

@app.callback(
    Output("total-tweets", "children"),
    [Input("graph-update", "n_intervals")],
)
def show_num_tweet(n):
    """ Display the number of tweets. """
    rows = cassandra.get_data(minutes, 'artistcount')

    # Create dataframe
    df = []
    time_now = datetime.datetime.now().replace(microsecond=0).isoformat()
    for row in rows:
        df.append({'date': time_now, 'artist': row.artist, 'total_count': row.total_count})
    df = pd.DataFrame(df)
    total = df.total_count.sum()

    return str(int(total))

@app.callback(
    Output("date", "children"),
    [Input("graph-update", "n_intervals")],
)
def show_num_tweet(n):
    """ Display the date and time. """
    time_now = datetime.datetime.now().strftime("%B %d, %Y")
    return str(time_now)

@app.callback(
    Output("time", "children"),
    [Input("graph-update", "n_intervals")],
)
def show_num_tweet(n):
    """ Display the date and time. """
    time_now = datetime.datetime.now().strftime("%H:%M:%S")
    return str(time_now)

if __name__ == '__main__':
    app.run_server(debug=True)
