import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
import plotly.graph_objs as go
import pandas as pd
from sqlalchemy import create_engine, text
from datetime import datetime, timedelta
import os
import time
from sqlalchemy.exc import OperationalError
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize the Dash app with a modern theme
app = dash.Dash(__name__, 
    external_stylesheets=[
        'https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500&display=swap',
        'https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css'
    ],
    meta_tags=[
        {"name": "viewport", "content": "width=device-width, initial-scale=1"}
    ]
)

# Enable the app to be embedded in an iframe
app.config.suppress_callback_exceptions = True
server = app.server  # Expose Flask server for gunicorn

# Get database connection details from environment variables with defaults
DB_USER = os.getenv('POSTGRES_USER', 'airflow')
DB_PASSWORD = os.getenv('POSTGRES_PASSWORD', 'airflow')
DB_HOST = os.getenv('POSTGRES_HOST', 'postgres')
DB_PORT = os.getenv('POSTGRES_PORT', '5432')
DB_NAME = os.getenv('POSTGRES_DB', 'stockdata')

logger.info(f"Attempting to connect to database: postgresql://{DB_USER}:***@{DB_HOST}:{DB_PORT}/{DB_NAME}")

# Create database connection with retry logic
def get_db_engine(max_retries=5, retry_interval=5):
    for attempt in range(max_retries):
        try:
            engine = create_engine(f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}')
            # Test the connection
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info(f"Successfully connected to database {DB_NAME}")
            return engine
        except OperationalError as e:
            logger.error(f"Database connection attempt {attempt + 1} failed: {str(e)}")
            if attempt < max_retries - 1:
                logger.info(f"Retrying in {retry_interval} seconds...")
                time.sleep(retry_interval)
            else:
                logger.error(f"Failed to connect to database after {max_retries} attempts")
                raise e

# Create database connection
try:
    engine = get_db_engine()
except Exception as e:
    logger.error(f"Failed to connect to database: {str(e)}")
    engine = None

# Styles
COLORS = {
    'background': '#F8F9FA',
    'text': '#212529',
    'primary': '#007BFF',
    'success': '#28A745',
    'danger': '#DC3545'
}

# Layout
app.layout = html.Div([
    # Header
    html.Div([
        html.H1('Stock Market Dashboard', 
                style={'color': COLORS['text'], 'textAlign': 'center', 'marginBottom': '20px'}),
        html.Div(id='connection-status', 
                 style={'textAlign': 'center', 'marginBottom': '20px'})
    ], style={'padding': '20px', 'backgroundColor': COLORS['background']}),
    
    # Controls
    html.Div([
        html.Div([
            html.Label('Select Stock:', style={'fontWeight': 'bold'}),
            dcc.Dropdown(
                id='stock-selector',
                options=[
                    {'label': stock, 'value': stock} for stock in 
                    ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'META', 'TSLA', 'NVDA', 'NFLX', 'AMD', 'INTC']
                ],
                value='AAPL',
                style={'width': '200px'}
            )
        ], style={'marginRight': '20px'}),
        
        html.Div([
            html.Label('Select Time Range:', style={'fontWeight': 'bold'}),
            dcc.RadioItems(
                id='time-range',
                options=[
                    {'label': '1 Hour', 'value': '1H'},
                    {'label': '4 Hours', 'value': '4H'},
                    {'label': '1 Day', 'value': '1D'}
                ],
                value='1H',
                style={'display': 'flex', 'gap': '10px'}
            )
        ])
    ], style={'display': 'flex', 'padding': '20px', 'backgroundColor': '#FFFFFF', 'borderRadius': '5px', 'marginBottom': '20px'}),
    
    # Loading spinner for graphs
    dcc.Loading(
        id="loading-graphs",
        type="default",
        children=[
            # Graphs
            html.Div([
                dcc.Graph(id='price-graph'),
                dcc.Graph(id='volume-graph'),
                dcc.Graph(id='change-graph')
            ], style={'padding': '20px'})
        ]
    ),
    
    # Auto-refresh interval
    dcc.Interval(
        id='interval-component',
        interval=60*1000,  # refresh every minute
        n_intervals=0
    )
], style={'backgroundColor': COLORS['background'], 'minHeight': '100vh'})

def create_figure(df, x, y, title, type='scatter', color=COLORS['primary']):
    if df.empty:
        return go.Figure().update_layout(
            title=title,
            annotations=[{
                'text': 'No data available',
                'xref': 'paper',
                'yref': 'paper',
                'showarrow': False,
                'font': {'size': 20}
            }]
        )
    
    fig = go.Figure()
    
    if type == 'scatter':
        fig.add_trace(go.Scatter(
            x=df[x],
            y=df[y],
            mode='lines',
            line=dict(color=color, width=2),
            name=y
        ))
    elif type == 'bar':
        fig.add_trace(go.Bar(
            x=df[x],
            y=df[y],
            marker_color=color,
            name=y
        ))
        
    fig.update_layout(
        title=title,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(
            title='Time',
            gridcolor='#EEEEEE',
            showgrid=True
        ),
        yaxis=dict(
            gridcolor='#EEEEEE',
            showgrid=True
        ),
        margin=dict(l=40, r=40, t=40, b=40)
    )
    
    return fig

@app.callback(
    [Output('connection-status', 'children'),
     Output('price-graph', 'figure'),
     Output('volume-graph', 'figure'),
     Output('change-graph', 'figure')],
    [Input('stock-selector', 'value'),
     Input('time-range', 'value'),
     Input('interval-component', 'n_intervals')]
)
def update_graphs(selected_stock, time_range, n):
    if engine is None:
        return html.Div("Database connection failed!", style={'color': COLORS['danger']}), {}, {}, {}
        
    try:
        # Calculate time range
        now = datetime.now()
        if time_range == '1H':
            start_time = now - timedelta(hours=1)
        elif time_range == '4H':
            start_time = now - timedelta(hours=4)
        else:  # 1D
            start_time = now - timedelta(days=1)
        
        # Query data from PostgreSQL
        query = f"""
        SELECT window_start as timestamp, avg_price, avg_volume, avg_change
        FROM stock_metrics
        WHERE symbol = :symbol
        AND window_start >= :start_time
        ORDER BY window_start
        """
        df = pd.read_sql_query(
            text(query),
            engine,
            params={'symbol': selected_stock, 'start_time': start_time}
        )
        
        if df.empty:
            logger.warning(f"No data available for {selected_stock}")
            return html.Div(f"No data available for {selected_stock}", 
                          style={'color': COLORS['danger']}), {}, {}, {}
        
        # Create figures
        price_fig = create_figure(df, 'timestamp', 'avg_price', 
                                f'{selected_stock} Price', color=COLORS['primary'])
        volume_fig = create_figure(df, 'timestamp', 'avg_volume', 
                                 f'{selected_stock} Volume', type='bar', color=COLORS['success'])
        change_fig = create_figure(df, 'timestamp', 'avg_change', 
                                 f'{selected_stock} Price Change %', color=COLORS['primary'])
        
        return html.Div(f"Connected to database, showing data for {selected_stock}", 
                       style={'color': COLORS['success']}), price_fig, volume_fig, change_fig
                       
    except Exception as e:
        logger.error(f"Error updating graphs: {str(e)}")
        return html.Div(f"Error: {str(e)}", 
                       style={'color': COLORS['danger']}), {}, {}, {}

if __name__ == '__main__':
    app.run_server(
        host='0.0.0.0',
        port=int(os.getenv('PORT', 8050)),
        debug=False
    ) 
