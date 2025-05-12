import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from db_operations import DatabaseManager
from spot import show_analysis_options
from visualization.charts import plot_price_chart, plot_volume_chart, plot_technical_indicators
from technical_indicator.moving_average import calculate_moving_averages, calculate_ema
from technical_indicator.macd import calculate_macd
from technical_indicator.super_trend import calculate_supertrend, get_supertrend_signals
import numpy as np
from analysis_tools.gap_analysis import analyze_gaps, get_gap_summary
from analysis_tools.ib_analysis import analyze_inside_bars, get_ib_summary
from analysis_tools.orb_analysis import analyze_orb, get_orb_summary
from visualization.gap_charts import plot_gap_analysis, plot_gap_fill_analysis, plot_gap_direction_analysis, plot_gap_patterns, plot_gap_risk_reward
from visualization.ib_charts import plot_ib_analysis, plot_ib_size_distribution, plot_ib_position_analysis, plot_ib_breakout_analysis
from visualization.orb_charts import plot_orb_analysis, plot_orb_success_analysis, plot_orb_time_analysis

# Set page config
st.set_page_config(
    page_title="Indian Market Analysis Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .main {
        padding: 2rem;
    }
    .stButton>button {
        width: 100%;
        background-color: #4CAF50;
        color: white;
        padding: 0.5rem 1rem;
        border: none;
        border-radius: 4px;
        cursor: pointer;
        font-size: 1rem;
    }
    .stButton>button:hover {
        background-color: #45a049;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 4px;
        margin: 0.5rem 0;
    }
    .stSelectbox {
        background-color: white;
    }
    .stDateInput {
        background-color: white;
    }
    .analysis-option {
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 4px;
        background-color: #f8f9fa;
        border: 1px solid #dee2e6;
    }
    .analysis-option:hover {
        background-color: #e9ecef;
        cursor: pointer;
    }
    .card {
        background: #23272f;
        border-radius: 12px;
        padding: 1.2rem 1rem 1rem 1rem;
        margin: 0.5rem 0.5rem 1.2rem 0.5rem;
        box-shadow: 0 2px 12px #0003;
        color: #fff;
        text-align: center;
        transition: transform 0.15s;
    }
    .card:hover {
        transform: scale(1.04);
        box-shadow: 0 4px 24px #0005;
    }
    .card .icon {
        font-size: 2.2rem;
        margin-bottom: 0.2rem;
    }
    .card .highlight {
        color: #4CAF50;
        font-weight: bold;
    }
    .card .negative {
        color: #e53935;
        font-weight: bold;
    }
    .card .neutral {
        color: #fbc02d;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

# Title and description
st.markdown("""
    <div style='text-align: center; padding: 1rem;'>
        <h1 style='color: #1E88E5;'>Indian Market Analysis Dashboard</h1>
        <p style='color: #666;'>Analyze Nifty, Bank Nifty, and Sensex data with advanced tools</p>
    </div>
    """, unsafe_allow_html=True)

# Initialize database connection
@st.cache_resource
def init_db():
    return DatabaseManager()

def main():
    # Initialize database
    db = init_db()
    
    # Sidebar navigation
    with st.sidebar:
        st.markdown("""
            <div style='text-align: center; padding: 1rem;'>
                <h2 style='color: #1E88E5;'>Navigation</h2>
            </div>
        """, unsafe_allow_html=True)
        # Move Analysis to be a top-level navigation option between Spot and Options
        page = st.radio(
            "Select Analysis Type",
            ["Spot", "Analysis", "Options"],
            label_visibility="collapsed"
        )
        st.markdown("---")
        # Add data import buttons
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Sample Data"):
                with st.spinner("Inserting sample data..."):
                    if db.insert_sample_data():
                        st.success("Sample data inserted successfully!")
                    else:
                        st.error("Failed to insert sample data.")
        with col2:
            if st.button("📥 Import DuckDB"):
                with st.spinner("Importing data from DuckDB..."):
                    if db.import_from_duckdb():
                        st.success("Data imported successfully!")
                    else:
                        st.error("Failed to import data.")
        st.markdown("""
            <div style='text-align: center; padding: 1rem;'>
                <p style='color: #666;'>Select an index and date range to begin analysis</p>
            </div>
        """, unsafe_allow_html=True)

    if page == "Spot":
        # Only spot-specific logic here, remove Actions section and related logic
        tables = db.get_table_names()
        base_tables = [table.replace('_1min', '') for table in tables if table.endswith('_1min')]
        base_tables = sorted(list(set(base_tables)))
        if not base_tables:
            st.error("No data tables found in the database. Please check your database setup.")
            return
        st.markdown("### Analysis Controls")
        st.markdown("#### Select Index")
        index_type = st.selectbox("Select Index", base_tables, key="spot_index")
        st.markdown("#### Select Timeframe")
        timeframe = st.selectbox(
            "Select Timeframe",
            ["Daily", "1 Hour", "15 Minute", "5 Minute", "1 Minute"],
            key="spot_timeframe_main"
        )
        # Convert timeframe selection to database format
        timeframe_map = {
            "Daily": "daily",
            "1 Hour": "1hour",
            "15 Minute": "15min",
            "5 Minute": "5min",
            "1 Minute": "1min"
        }
        selected_timeframe = timeframe_map[timeframe]
        spot_analysis(db, index_type=index_type, selected_timeframe=selected_timeframe, show_actions=False)
    elif page == "Analysis":
        # Analysis page: allow user to select index, timeframe, date range, and show data/analysis
        st.markdown("# Analysis Section")
        tables = db.get_table_names()
        base_tables = [table.replace('_1min', '') for table in tables if table.endswith('_1min')]
        base_tables = sorted(list(set(base_tables)))
        if not base_tables:
            st.error("No data tables found in the database. Please check your database setup.")
        else:
            st.markdown("#### Select Index and Date Range")
            # Use columns to align Select Index, Select Date Range, and Reports horizontally
            col1, col2, col3 = st.columns([2, 2, 1])
            with col1:
                st.markdown("<label style='font-size: 1.1rem; font-weight: 600; color: #23272f;'><span style='font-size: 1.5rem; vertical-align: middle;'>📈</span> Select Index</label>", unsafe_allow_html=True)
                index_type = st.selectbox("Select Index", base_tables, key="analysis_index")
            with col2:
                st.markdown("<label style='font-size: 1.1rem; font-weight: 600; color: #23272f;'><span style='font-size: 1.5rem; vertical-align: middle;'>📅</span> Select Date Range</label>", unsafe_allow_html=True)
                table_name = f"{index_type}_daily"
                start_date, end_date = db.get_available_dates(table_name)
                if start_date and end_date:
                    start_date = start_date.date()
                    end_date = end_date.date()
                    date_range = st.date_input(
                        "Select Date Range",
                        value=(end_date - timedelta(days=30), end_date),
                        min_value=start_date,
                        max_value=end_date,
                        key="analysis_date_range"
                    )
            with col3:
                st.markdown("<label style='font-size: 1.1rem; font-weight: 600; color: #23272f;'><span style='font-size: 1.5rem; vertical-align: middle;'>📝</span> Reports</label>", unsafe_allow_html=True)
                selected_report = st.selectbox("Select Report", ["gap", "ib", "Open Range Break (ORB)"], key="analysis_report")
            
            # Add weekday filter for all analysis
            weekdays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
            selected_weekdays = st.multiselect("Filter by Weekday", weekdays, default=weekdays, key="analysis_weekday_filter")
            
            # Show gap analysis section if 'gap' is selected in Reports
            if selected_report == "gap":
                st.markdown("## Gap Analysis Dashboard")
                
                # Get data for analysis
                df = db.get_index_data(index_type, date_range, "daily")
                if df is not None and not df.empty:
                    df['weekday'] = pd.to_datetime(df['datetime']).dt.day_name()
                    df = df[df['weekday'].isin(selected_weekdays)]
                    
                    # Analyze gaps
                    df, gap_stats = analyze_gaps(df, date_range)
                    
                    # Display key metrics
                    total_gaps = gap_stats['total_gaps']
                    filled_gaps = gap_stats['filled_gaps']
                    unfilled_gaps = total_gaps - filled_gaps
                    up_gaps = df[df['gap_direction'] == 'Up']['gap_category'].isin(['Medium', 'High']).sum()
                    down_gaps = df[df['gap_direction'] == 'Down']['gap_category'].isin(['Medium', 'High']).sum()
                    fill_rate = gap_stats['gap_fill_rate']
                    
                    col1, col2, col3, col4, col5 = st.columns(5)
                    with col1:
                        st.metric("Total Gaps", total_gaps, f"Fill Rate: {fill_rate:.1f}%")
                    with col2:
                        st.metric("Gap Up Count", up_gaps)
                    with col3:
                        st.metric("Gap Down Count", down_gaps)
                    with col4:
                        st.metric("Total Gaps Filled", filled_gaps)
                    with col5:
                        st.metric("Total Gaps Unfilled", unfilled_gaps)
                    
                    # Gap Range Analysis Table
                    st.markdown("""
                    ### Gap Range Analysis Table
                    **Gap Ranges:**  
                    - Flat: ±0.3%  
                    - Medium: ±0.3% to ±0.7%  
                    - High: >±0.7%  
                    
                    **Table format:** `count (filled/unfilled)`
                    """)
                    gap_ranges = ['Flat', 'Medium', 'High']
                    directions = ['Up', 'Down']
                    table_data = []
                    overall = {'Direction': 'Overall'}
                    total_sum = 0
                    for rng in gap_ranges:
                        overall[rng] = 0
                    overall_filled = 0
                    overall_unfilled = 0
                    for direction in directions:
                        row = {'Direction': f'Gap {direction}'}
                        dir_gaps = df[df['gap_direction'] == direction]
                        total = 0
                        for rng in gap_ranges:
                            gaps = dir_gaps[dir_gaps['gap_category'] == rng]
                            count = len(gaps)
                            filled = gaps['gap_filled'].sum()
                            unfilled = count - filled
                            row[rng] = f"{count} ({filled}/{unfilled})"
                            # For overall row
                            if overall[rng] == 0:
                                overall[rng] = [0, 0, 0]  # [count, filled, unfilled]
                            overall[rng][0] += count
                            overall[rng][1] += filled
                            overall[rng][2] += unfilled
                            total += count
                        row['Total'] = total
                        table_data.append(row)
                        total_sum += total
                    # Build overall row
                    overall_total = 0
                    for rng in gap_ranges:
                        count, filled, unfilled = overall[rng]
                        overall[rng] = f"{count} ({filled}/{unfilled})"
                        overall_total += count
                        overall_filled += filled
                        overall_unfilled += unfilled
                    overall['Total'] = f"{overall_total} ({overall_filled}/{overall_unfilled})"
                    table_data.append(overall)
                    gap_range_df = pd.DataFrame(table_data)
                    st.dataframe(gap_range_df, use_container_width=True)
                    
                    # Display gap analysis charts
                    st.plotly_chart(plot_gap_analysis(df), use_container_width=True)
                    st.plotly_chart(plot_gap_fill_analysis(df), use_container_width=True)
                    
                    # Add new detailed gap analysis visualizations
                    st.markdown("### Detailed Gap Analysis")
                    tab1, tab2, tab3 = st.tabs(["Direction Analysis", "Pattern Analysis", "Risk-Reward Analysis"])
                    
                    with tab1:
                        direction_fig = plot_gap_direction_analysis(df)
                        if direction_fig:
                            st.plotly_chart(direction_fig, use_container_width=True)
                        
                        # Separate detailed analysis tables for gap up and gap down
                        st.markdown("### Detailed Gap Up Analysis")
                        up_gaps = df[df['gap_direction'] == 'Up'].copy()
                        if not up_gaps.empty:
                            # Calculate additional metrics for gap up
                            up_gaps['gap_size_category'] = pd.qcut(up_gaps['gap_size'], q=5, labels=['Very Small', 'Small', 'Medium', 'Large', 'Very Large'])
                            up_gaps['fill_time_category'] = pd.qcut(up_gaps['days_to_fill'].fillna(999), q=5, labels=['Very Fast', 'Fast', 'Medium', 'Slow', 'Very Slow'])
                            
                            # Create detailed metrics table
                            up_metrics = pd.DataFrame({
                                'Metric': [
                                    'Total Gaps',
                                    'Filled Gaps',
                                    'Fill Rate',
                                    'Average Gap Size',
                                    'Average Days to Fill',
                                    'Average Return',
                                    'Win Rate',
                                    'Average Risk-Reward',
                                    'Max Adverse Excursion',
                                    'Max Favorable Excursion'
                                ],
                                'Value': [
                                    len(up_gaps),
                                    up_gaps['gap_filled'].sum(),
                                    f"{up_gaps['gap_filled'].mean()*100:.1f}%",
                                    f"{up_gaps['gap_size'].mean():.2f}%",
                                    f"{up_gaps['days_to_fill'].mean():.1f}",
                                    f"{up_gaps['fill_return'].mean():.2f}%",
                                    f"{(up_gaps['fill_return'] > 0).mean()*100:.1f}%",
                                    f"{up_gaps['risk_reward_ratio'].mean():.2f}",
                                    f"{up_gaps['max_adverse_excursion'].mean():.2f}%",
                                    f"{up_gaps['max_favorable_excursion'].mean():.2f}%"
                                ]
                            })
                            st.dataframe(up_metrics, use_container_width=True)
                            
                            # Size-based analysis
                            st.markdown("#### Gap Up Analysis by Size")
                            size_analysis = up_gaps.groupby('gap_size_category').agg({
                                'gap': 'count',
                                'gap_filled': 'mean',
                                'days_to_fill': 'mean',
                                'fill_return': 'mean',
                                'risk_reward_ratio': 'mean'
                            }).round(3)
                            st.dataframe(size_analysis, use_container_width=True)
                            
                            # Fill time analysis
                            st.markdown("#### Gap Up Analysis by Fill Time")
                            time_analysis = up_gaps.groupby('fill_time_category').agg({
                                'gap': 'count',
                                'gap_filled': 'mean',
                                'fill_return': 'mean',
                                'risk_reward_ratio': 'mean'
                            }).round(3)
                            st.dataframe(time_analysis, use_container_width=True)
                        
                        st.markdown("### Detailed Gap Down Analysis")
                        down_gaps = df[df['gap_direction'] == 'Down'].copy()
                        if not down_gaps.empty:
                            # Calculate additional metrics for gap down
                            down_gaps['gap_size_category'] = pd.qcut(down_gaps['gap_size'], q=5, labels=['Very Small', 'Small', 'Medium', 'Large', 'Very Large'])
                            down_gaps['fill_time_category'] = pd.qcut(down_gaps['days_to_fill'].fillna(999), q=5, labels=['Very Fast', 'Fast', 'Medium', 'Slow', 'Very Slow'])
                            
                            # Create detailed metrics table
                            down_metrics = pd.DataFrame({
                                'Metric': [
                                    'Total Gaps',
                                    'Filled Gaps',
                                    'Fill Rate',
                                    'Average Gap Size',
                                    'Average Days to Fill',
                                    'Average Return',
                                    'Win Rate',
                                    'Average Risk-Reward',
                                    'Max Adverse Excursion',
                                    'Max Favorable Excursion'
                                ],
                                'Value': [
                                    len(down_gaps),
                                    down_gaps['gap_filled'].sum(),
                                    f"{down_gaps['gap_filled'].mean()*100:.1f}%",
                                    f"{down_gaps['gap_size'].mean():.2f}%",
                                    f"{down_gaps['days_to_fill'].mean():.1f}",
                                    f"{down_gaps['fill_return'].mean():.2f}%",
                                    f"{(down_gaps['fill_return'] > 0).mean()*100:.1f}%",
                                    f"{down_gaps['risk_reward_ratio'].mean():.2f}",
                                    f"{down_gaps['max_adverse_excursion'].mean():.2f}%",
                                    f"{down_gaps['max_favorable_excursion'].mean():.2f}%"
                                ]
                            })
                            st.dataframe(down_metrics, use_container_width=True)
                            
                            # Size-based analysis
                            st.markdown("#### Gap Down Analysis by Size")
                            size_analysis = down_gaps.groupby('gap_size_category').agg({
                                'gap': 'count',
                                'gap_filled': 'mean',
                                'days_to_fill': 'mean',
                                'fill_return': 'mean',
                                'risk_reward_ratio': 'mean'
                            }).round(3)
                            st.dataframe(size_analysis, use_container_width=True)
                            
                            # Fill time analysis
                            st.markdown("#### Gap Down Analysis by Fill Time")
                            time_analysis = down_gaps.groupby('fill_time_category').agg({
                                'gap': 'count',
                                'gap_filled': 'mean',
                                'fill_return': 'mean',
                                'risk_reward_ratio': 'mean'
                            }).round(3)
                            st.dataframe(time_analysis, use_container_width=True)
                        
                        # Add comparison table
                        st.markdown("### Gap Up vs Gap Down Comparison")
                        comparison_data = {
                            'Metric': [
                                'Total Gaps',
                                'Fill Rate',
                                'Average Gap Size',
                                'Average Days to Fill',
                                'Average Return',
                                'Win Rate',
                                'Risk-Reward Ratio',
                                'Max Adverse Excursion',
                                'Max Favorable Excursion'
                            ],
                            'Gap Up': [
                                len(up_gaps),
                                f"{up_gaps['gap_filled'].mean()*100:.1f}%",
                                f"{up_gaps['gap_size'].mean():.2f}%",
                                f"{up_gaps['days_to_fill'].mean():.1f}",
                                f"{up_gaps['fill_return'].mean():.2f}%",
                                f"{(up_gaps['fill_return'] > 0).mean()*100:.1f}%",
                                f"{up_gaps['risk_reward_ratio'].mean():.2f}",
                                f"{up_gaps['max_adverse_excursion'].mean():.2f}%",
                                f"{up_gaps['max_favorable_excursion'].mean():.2f}%"
                            ],
                            'Gap Down': [
                                len(down_gaps),
                                f"{down_gaps['gap_filled'].mean()*100:.1f}%",
                                f"{down_gaps['gap_size'].mean():.2f}%",
                                f"{down_gaps['days_to_fill'].mean():.1f}",
                                f"{down_gaps['fill_return'].mean():.2f}%",
                                f"{(down_gaps['fill_return'] > 0).mean()*100:.1f}%",
                                f"{down_gaps['risk_reward_ratio'].mean():.2f}",
                                f"{down_gaps['max_adverse_excursion'].mean():.2f}%",
                                f"{down_gaps['max_favorable_excursion'].mean():.2f}%"
                            ]
                        }
                        comparison_df = pd.DataFrame(comparison_data)
                        st.dataframe(comparison_df, use_container_width=True)
                    
                    with tab2:
                        pattern_fig = plot_gap_patterns(df)
                        if pattern_fig:
                            st.plotly_chart(pattern_fig, use_container_width=True)
                        
                        # Pattern statistics
                        col1, col2 = st.columns(2)
                        with col1:
                            st.subheader("Temporal Patterns")
                            weekday_stats = df.groupby('weekday').agg({
                                'gap': 'count',
                                'gap_filled': 'mean',
                                'fill_return': 'mean'
                            }).round(3)
                            st.dataframe(weekday_stats)
                        
                        with col2:
                            st.subheader("Consecutive Gaps")
                            consecutive_stats = df.groupby('consecutive').agg({
                                'gap': 'count',
                                'gap_filled': 'mean',
                                'fill_return': 'mean'
                            }).round(3)
                            st.dataframe(consecutive_stats)
                    
                    with tab3:
                        risk_fig = plot_gap_risk_reward(df)
                        if risk_fig:
                            st.plotly_chart(risk_fig, use_container_width=True)
                        
                        # Risk metrics
                        col1, col2 = st.columns(2)
                        with col1:
                            st.subheader("Risk Metrics")
                            st.metric("Avg Max Adverse Excursion", f"{df['max_adverse_excursion'].mean():.2f}%")
                            st.metric("Avg Max Favorable Excursion", f"{df['max_favorable_excursion'].mean():.2f}%")
                            st.metric("Win Rate", f"{(df['fill_return'] > 0).mean()*100:.1f}%")
                        
                        with col2:
                            st.subheader("Gap Size Analysis")
                            size_stats = df.groupby('gap_size_bin').agg({
                                'gap': 'count',
                                'gap_filled': 'mean',
                                'fill_return': 'mean',
                                'risk_reward_ratio': 'mean'
                            }).round(3)
                            st.dataframe(size_stats)
                    
                    # Display gap summary table
                    st.markdown("### Gap Summary")
                    summary_df = get_gap_summary(df)
                    if not summary_df.empty:
                        st.dataframe(
                            summary_df.style.background_gradient(subset=['fill_rate'], cmap='RdYlGn'),
                            use_container_width=True
                        )
                    
                    # Display detailed gap history
                    st.markdown("### Gap History")
                    gap_history = df[df['gap_category'].isin(['Medium', 'High'])][
                        ['datetime', 'open', 'close', 'gap', 'gap_category', 'gap_direction', 'gap_filled', 'days_to_fill']
                    ].copy()
                    
                    if not gap_history.empty:
                        gap_history['datetime'] = gap_history['datetime'].dt.strftime('%Y-%m-%d')
                        st.dataframe(
                            gap_history.style.format({
                                'gap': '{:.2f}%',
                                'open': '{:.2f}',
                                'close': '{:.2f}',
                                'days_to_fill': lambda x: f"{x:.0f}" if pd.notnull(x) else '-',
                                'gap_filled': lambda x: 'Yes' if x is True else ('No' if x is False else '-')
                            }).background_gradient(subset=['gap'], cmap='RdYlGn'),
                            use_container_width=True,
                            height=400
                        )
                    else:
                        st.info("No significant gaps found in the selected period.")
                else:
                    st.error("No data available for the selected period.")
            elif selected_report == "ib":
                st.markdown("## Inside Bar Analysis Dashboard")
                
                # Get data for analysis
                df = db.get_index_data(index_type, date_range, "daily")
                if df is not None and not df.empty:
                    df['weekday'] = pd.to_datetime(df['datetime']).dt.day_name()
                    df = df[df['weekday'].isin(selected_weekdays)]
                    
                    # Analyze inside bars
                    ib_stats = analyze_inside_bars(df)
                    
                    # Display key metrics
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Total Bars", ib_stats['total_bars'])
                    with col2:
                        st.metric("Inside Bars", ib_stats['inside_bars'])
                    with col3:
                        st.metric("IB Percentage", f"{ib_stats['ib_percentage']:.1f}%")
                    with col4:
                        st.metric("Avg IB Size", f"{ib_stats['size_stats']['mean']:.2f}%")
                    
                    # Display breakout statistics
                    st.markdown("### Breakout Statistics")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Up Breakouts", ib_stats['breakout_stats']['up_breakouts'])
                    with col2:
                        st.metric("Down Breakouts", ib_stats['breakout_stats']['down_breakouts'])
                    with col3:
                        st.metric("Up Breakout Rate", f"{ib_stats['breakout_stats']['up_breakout_rate']:.1f}%")
                    
                    # Display inside bar analysis charts
                    st.plotly_chart(plot_ib_analysis(df), use_container_width=True)
                    
                    # Add detailed analysis tabs
                    tab1, tab2, tab3 = st.tabs(["Size Analysis", "Position Analysis", "Breakout Analysis"])
                    
                    with tab1:
                        st.plotly_chart(plot_ib_size_distribution(df), use_container_width=True)
                        
                        # Size statistics table
                        size_stats = pd.DataFrame({
                            'Metric': ['Mean', 'Median', 'Min', 'Max', 'Std Dev'],
                            'Value': [
                                f"{ib_stats['size_stats']['mean']:.2f}%",
                                f"{ib_stats['size_stats']['median']:.2f}%",
                                f"{ib_stats['size_stats']['min']:.2f}%",
                                f"{ib_stats['size_stats']['max']:.2f}%",
                                f"{ib_stats['size_stats']['std']:.2f}%"
                            ]
                        })
                        st.dataframe(size_stats, use_container_width=True)
                    
                    with tab2:
                        st.plotly_chart(plot_ib_position_analysis(df), use_container_width=True)
                        
                        # Position statistics table
                        position_stats = pd.DataFrame({
                            'Metric': ['Mean', 'Median', 'Std Dev'],
                            'Value': [
                                f"{ib_stats['position_stats']['mean']:.2f}",
                                f"{ib_stats['position_stats']['median']:.2f}",
                                f"{ib_stats['position_stats']['std']:.2f}"
                            ]
                        })
                        st.dataframe(position_stats, use_container_width=True)
                    
                    with tab3:
                        st.plotly_chart(plot_ib_breakout_analysis(df), use_container_width=True)
                        
                        # Breakout statistics table
                        breakout_stats = pd.DataFrame({
                            'Metric': ['Up Breakouts', 'Down Breakouts', 'Up Breakout Rate', 'Down Breakout Rate'],
                            'Value': [
                                ib_stats['breakout_stats']['up_breakouts'],
                                ib_stats['breakout_stats']['down_breakouts'],
                                f"{ib_stats['breakout_stats']['up_breakout_rate']:.1f}%",
                                f"{ib_stats['breakout_stats']['down_breakout_rate']:.1f}%"
                            ]
                        })
                        st.dataframe(breakout_stats, use_container_width=True)
                    
                    # Display inside bar summary table
                    st.markdown("### Inside Bar Summary")
                    summary_df = get_ib_summary(df)
                    if not summary_df.empty:
                        st.dataframe(
                            summary_df.style.format({
                                'ib_size': '{:.2f}%',
                                'ib_position': '{:.2f}',
                                'breakout_up': lambda x: 'Yes' if x else 'No',
                                'breakout_down': lambda x: 'Yes' if x else 'No'
                            }),
                            use_container_width=True,
                            height=400
                        )
                    else:
                        st.info("No inside bars found in the selected period.")
                else:
                    st.error("No data available for the selected period.")
            elif selected_report == "Open Range Break (ORB)":
                st.markdown("## Open Range Break (ORB) Analysis Dashboard")
                
                # Get the selected timeframe
                timeframe_map = {
                    "Daily": "daily",
                    "1 Hour": "1hour",
                    "15 Minute": "15min",
                    "5 Minute": "5min",
                    "1 Minute": "1min"
                }
                
                # Add timeframe selection
                selected_timeframe = st.selectbox(
                    "Select Timeframe",
                    ["1 Minute", "5 Minute", "15 Minute"],
                    key="orb_timeframe"
                )
                
                # Convert to database format
                db_timeframe = timeframe_map[selected_timeframe]
                
                # Get data for the selected timeframe
                df = db.get_index_data(index_type, date_range, db_timeframe)
                
                if df is not None and not df.empty:
                    df['datetime'] = pd.to_datetime(df['datetime'])
                    df = df[(df['datetime'].dt.date >= date_range[0]) & (df['datetime'].dt.date <= date_range[1])]
                    df['date'] = df['datetime'].dt.date
                    df['time'] = df['datetime'].dt.time
                    df['weekday'] = df['datetime'].dt.day_name()
                    df = df[df['weekday'].isin(selected_weekdays)]
                    market_start = datetime.strptime("09:15", "%H:%M").time()
                    both = 0
                    up_only = 0
                    down_only = 0
                    none = 0
                    orb_results = []
                    high_only_stats = []
                    low_only_stats = []
                    both_broken_stats = []
                    
                    if df.empty:
                        st.error("No data available for the selected period.")
                    else:
                        # Add range minutes selection based on timeframe
                        if selected_timeframe == "1 Minute":
                            range_minutes = st.slider("Select Range Minutes", min_value=5, max_value=60, value=5, step=5)
                        elif selected_timeframe == "5 Minute":
                            range_minutes = st.slider("Select Range Minutes", min_value=5, max_value=60, value=15, step=5)
                        else:  # 15 Minute
                            range_minutes = st.slider("Select Range Minutes", min_value=15, max_value=60, value=30, step=15)
                        
                        # Remove debug prints for clean UI
                        # ORB analysis loop with original logic
                        for day, day_df in df.groupby('date'):
                            day_df = day_df.sort_values('datetime')
                            orb_window = day_df[day_df['time'] >= market_start].head(range_minutes)
                            if orb_window.empty or len(orb_window) < range_minutes:
                                continue
                            
                            orb_high = orb_window['high'].max()
                            orb_low = orb_window['low'].min()
                            after_orb = day_df[day_df['datetime'] > orb_window['datetime'].max()]
                            
                            up_broken = False
                            down_broken = False
                            breakout_time_up = None
                            breakout_time_down = None
                            
                            # Calculate detailed statistics
                            day_stats = calculate_orb_statistics(day_df, orb_high, orb_low, market_start, range_minutes)
                            day_stats['orb_high'] = orb_high
                            day_stats['orb_low'] = orb_low
                            day_stats['day_df'] = day_df
                            
                            for _, row in after_orb.iterrows():
                                if not up_broken and row['high'] > orb_high:
                                    up_broken = True
                                    breakout_time_up = row['datetime']
                                if not down_broken and row['low'] < orb_low:
                                    down_broken = True
                                    breakout_time_down = row['datetime']
                            
                            if up_broken and down_broken:
                                scenario = 'Both Broken'
                                both += 1
                                both_broken_stats.append(day_stats)
                            elif up_broken:
                                scenario = 'Up Only'
                                up_only += 1
                                high_only_stats.append(day_stats)
                            elif down_broken:
                                scenario = 'Down Only'
                                down_only += 1
                                low_only_stats.append(day_stats)
                            else:
                                scenario = 'None Broken'
                                none += 1
                            
                            orb_results.append({
                                'date': day,
                                'orb_high': orb_high,
                                'orb_low': orb_low,
                                'up_broken': up_broken,
                                'down_broken': down_broken,
                                'breakout_time_up': breakout_time_up,
                                'breakout_time_down': breakout_time_down,
                                'scenario': scenario
                            })
                        
                        # Calculate percentages
                        orb_results_df = pd.DataFrame(orb_results)
                        total_days = len(orb_results_df)
                        up_pct = (up_only / total_days * 100) if total_days > 0 else 0
                        down_pct = (down_only / total_days * 100) if total_days > 0 else 0
                        both_pct = (both / total_days * 100) if total_days > 0 else 0
                        none_pct = (none / total_days * 100) if total_days > 0 else 0
                        
                        # Display results
                        st.markdown("### ORB Analysis Results")
                        
                        # Visualization: 4 gauges side by side
                        import plotly.graph_objects as go
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            fig_up = go.Figure(go.Indicator(
                                mode = "gauge+number",
                                value = up_pct,
                                title = {'text': "Up Only %"},
                                gauge = {'axis': {'range': [None, 100]}}
                            ))
                            st.plotly_chart(fig_up, use_container_width=True)
                        with col2:
                            fig_down = go.Figure(go.Indicator(
                                mode = "gauge+number",
                                value = down_pct,
                                title = {'text': "Down Only %"},
                                gauge = {'axis': {'range': [None, 100]}}
                            ))
                            st.plotly_chart(fig_down, use_container_width=True)
                        with col3:
                            fig_both = go.Figure(go.Indicator(
                                mode = "gauge+number",
                                value = both_pct,
                                title = {'text': "Both Broken %"},
                                gauge = {'axis': {'range': [None, 100]}}
                            ))
                            st.plotly_chart(fig_both, use_container_width=True)
                        with col4:
                            fig_none = go.Figure(go.Indicator(
                                mode = "gauge+number",
                                value = none_pct,
                                title = {'text': "Both Sides Not Broken %"},
                                gauge = {'axis': {'range': [None, 100]}}
                            ))
                            st.plotly_chart(fig_none, use_container_width=True)
                        
                        # Display detailed results
                        st.markdown("### ORB Per-Day Results")
                        if not orb_results_df.empty:
                            st.dataframe(
                                orb_results_df.style.format({
                                    'orb_high': '{:.2f}',
                                    'orb_low': '{:.2f}',
                                    'up_broken': lambda x: 'Yes' if x else 'No',
                                    'down_broken': lambda x: 'Yes' if x else 'No',
                                    'breakout_time_up': lambda x: x.strftime('%Y-%m-%d %H:%M') if pd.notnull(x) else '-',
                                    'breakout_time_down': lambda x: x.strftime('%Y-%m-%d %H:%M') if pd.notnull(x) else '-',
                                    'scenario': str
                                }),
                                use_container_width=True,
                                height=400
                            )
                        else:
                            st.info("No ORB patterns found in the selected period.")
                        
                        # Detailed analysis tabs
                        st.markdown("## Detailed ORB Statistics")
                        tab1, tab2, tab3 = st.tabs(["High Only Analysis", "Low Only Analysis", "Both Broken Analysis"])
                        
                        with tab1:
                            if high_only_stats:
                                st.markdown("### Statistical Analysis")
                                high_break_to_close = []
                                high_break_to_max = []
                                high_break_to_max_time = []
                                
                                for s in high_only_stats:
                                    day_df = s['day_df']
                                    orb_high = s['orb_high']
                                    after_orb = day_df[day_df['datetime'] > s['first_break_time']] if s['first_break_time'] is not None else pd.DataFrame()
                                    
                                    if not after_orb.empty:
                                        close_of_day = day_df['close'].iloc[-1]
                                        after_orb_reset = after_orb.reset_index(drop=True)
                                        
                                        if not after_orb_reset['high'].isnull().all():
                                            max_high_pos = after_orb_reset['high'].idxmax()
                                            max_high_after_break = after_orb_reset.iloc[max_high_pos]['high']
                                            max_high_datetime = after_orb_reset.iloc[max_high_pos]['datetime']
                                        else:
                                            max_high_after_break = None
                                            max_high_datetime = None
                                        
                                        high_break_price = orb_high
                                        high_break_to_close.append((close_of_day - high_break_price) / high_break_price * 100)
                                        
                                        if max_high_after_break is not None:
                                            high_break_to_max.append((max_high_after_break - high_break_price) / high_break_price * 100)
                                        else:
                                            high_break_to_max.append(float('nan'))
                                        high_break_to_max_time.append(max_high_datetime)
                                
                                if high_break_to_close:
                                    col1, col2, col3 = st.columns(3)
                                    with col1:
                                        st.metric("Average Range (HIGH BREAK TO CLOSE)", f"{np.mean(high_break_to_close):.2f}%")
                                        st.metric("Median Range (HIGH BREAK TO CLOSE)", f"{np.median(high_break_to_close):.2f}%")
                                    with col2:
                                        if high_break_to_max:
                                            max_idx = np.nanargmax(high_break_to_max)
                                            max_range = high_break_to_max[max_idx]
                                            max_datetime = high_break_to_max_time[max_idx]
                                            st.metric("Max Range (MOVED FROM THE HIGH BREAK)", f"{max_range:.2f}%", f"at {max_datetime}")
                                        else:
                                            st.metric("Max Range (MOVED FROM THE HIGH BREAK)", "N/A")
                                        st.metric("Min Range (MOVED FROM THE HIGH BREAK)", f"{np.nanmin(high_break_to_max):.2f}%")
                                    with col3:
                                        st.metric("Std Dev (HIGH BREAK TO CLOSE)", f"{np.std(high_break_to_close):.2f}%")
                                        st.metric("Std Dev (MOVED FROM THE HIGH BREAK)", f"{np.nanstd(high_break_to_max):.2f}%")
                        
                        with tab2:
                            if low_only_stats:
                                st.markdown("### Statistical Analysis")
                                low_break_to_close = []
                                low_break_to_min = []
                                low_break_to_min_time = []
                                
                                for s in low_only_stats:
                                    day_df = s['day_df']
                                    orb_low = s['orb_low']
                                    after_orb = day_df[day_df['datetime'] > s['first_break_time']] if s['first_break_time'] is not None else pd.DataFrame()
                                    
                                    if not after_orb.empty:
                                        close_of_day = day_df['close'].iloc[-1]
                                        after_orb_reset = after_orb.reset_index(drop=True)
                                        
                                        if not after_orb_reset['low'].isnull().all():
                                            min_low_pos = after_orb_reset['low'].idxmin()
                                            min_low_after_break = after_orb_reset.iloc[min_low_pos]['low']
                                            min_low_datetime = after_orb_reset.iloc[min_low_pos]['datetime']
                                        else:
                                            min_low_after_break = None
                                            min_low_datetime = None
                                        
                                        low_break_price = orb_low
                                        low_break_to_close.append((close_of_day - low_break_price) / low_break_price * 100)
                                        
                                        if min_low_after_break is not None:
                                            low_break_to_min.append((min_low_after_break - low_break_price) / low_break_price * 100)
                                        else:
                                            low_break_to_min.append(float('nan'))
                                        low_break_to_min_time.append(min_low_datetime)
                                
                                if low_break_to_close:
                                    col1, col2, col3 = st.columns(3)
                                    with col1:
                                        st.metric("Average Range (LOW BREAK TO CLOSE)", f"{np.mean(low_break_to_close):.2f}%")
                                        st.metric("Median Range (LOW BREAK TO CLOSE)", f"{np.median(low_break_to_close):.2f}%")
                                    with col2:
                                        if low_break_to_min:
                                            max_idx = np.nanargmax(low_break_to_min)
                                            max_range = low_break_to_min[max_idx]
                                            max_datetime = low_break_to_min_time[max_idx]
                                            st.metric("Max Range (MOVED FROM THE LOW BREAK)", f"{max_range:.2f}%", f"at {max_datetime}")
                                        else:
                                            st.metric("Max Range (MOVED FROM THE LOW BREAK)", "N/A")
                                        st.metric("Min Range (MOVED FROM THE LOW BREAK)", f"{np.nanmin(low_break_to_min):.2f}%")
                                    with col3:
                                        st.metric("Std Dev (LOW BREAK TO CLOSE)", f"{np.std(low_break_to_close):.2f}%")
                                        st.metric("Std Dev (MOVED FROM THE LOW BREAK)", f"{np.nanstd(low_break_to_min):.2f}%")
                        
                        with tab3:
                            if both_broken_stats:
                                # For each day, analyze the first break and its max move after break
                                first_break_moves = []
                                first_break_times = []
                                first_break_types = []
                                for s in both_broken_stats:
                                    day_df = s['day_df']
                                    first_break_time = s['first_break_time']
                                    break_direction = s['break_direction']
                                    if first_break_time is not None:
                                        after_break = day_df[day_df['datetime'] > first_break_time].reset_index(drop=True)
                                        if break_direction == 'high':
                                            if not after_break['high'].isnull().all():
                                                max_pos = after_break['high'].idxmax()
                                                max_val = after_break.iloc[max_pos]['high']
                                                max_time = after_break.iloc[max_pos]['datetime']
                                                move = (max_val - s['orb_high']) / s['orb_high'] * 100
                                                first_break_moves.append(move)
                                                first_break_times.append(max_time)
                                                first_break_types.append('High')
                                        elif break_direction == 'low':
                                            if not after_break['low'].isnull().all():
                                                min_pos = after_break['low'].idxmin()
                                                min_val = after_break.iloc[min_pos]['low']
                                                min_time = after_break.iloc[min_pos]['datetime']
                                                move = (min_val - s['orb_low']) / s['orb_low'] * 100
                                                first_break_moves.append(move)
                                                first_break_times.append(min_time)
                                                first_break_types.append('Low')
                                # Now display stats
                                if first_break_moves:
                                    col1, col2, col3 = st.columns(3)
                                    with col1:
                                        st.metric("Average Move (First Break to Max/Min)", f"{np.mean(first_break_moves):.2f}%")
                                        st.metric("Median Move", f"{np.median(first_break_moves):.2f}%")
                                    with col2:
                                        max_idx = np.nanargmax(np.abs(first_break_moves))
                                        st.metric("Max Move", f"{first_break_moves[max_idx]:.2f}%", f"at {first_break_times[max_idx]}")
                                        st.metric("Min Move", f"{np.nanmin(first_break_moves):.2f}%")
                                    with col3:
                                        st.metric("Std Dev", f"{np.nanstd(first_break_moves):.2f}%")
                                # Show a breakdown of how many times high/low was first
                                high_first = first_break_types.count('High')
                                low_first = first_break_types.count('Low')
                                st.markdown("### First Break Analysis")
                                col1, col2 = st.columns(2)
                                with col1:
                                    st.metric("High First", f"{(high_first/len(first_break_types)*100):.2f}%")
                                with col2:
                                    st.metric("Low First", f"{(low_first/len(first_break_types)*100):.2f}%")
                else:
                    st.error("No data available for the selected period.")
    else:
        options_analysis(db)

def spot_analysis(db, index_type, selected_timeframe, show_actions=True):
    try:
        # Get available tables and filter out timeframe-specific tables
        tables = db.get_table_names()
        base_tables = [table.replace('_1min', '') for table in tables if table.endswith('_1min')]
        base_tables = sorted(list(set(base_tables)))
        if not base_tables:
            st.error("No data tables found in the database. Please check your database setup.")
            return
        # Do NOT display extra 'Analysis Controls', 'Selected Index', or 'Selected Timeframe' here.
        # The rest of the function uses index_type and selected_timeframe as provided
        
        st.markdown("#### Select Date Range")
        table_name = f"{index_type}_{selected_timeframe}"
        st.write('Constructed table name:', table_name)
        # Show the first few rows of the constructed table if it exists
        if table_name in tables:
            try:
                df_preview = db.get_index_data(index_type, (start_date, end_date), selected_timeframe)
                st.write(f'First rows of table {table_name}:', df_preview.head() if df_preview is not None else 'None')
            except Exception as e:
                st.write(f'Error loading table {table_name}:', str(e))
        start_date, end_date = db.get_available_dates(table_name)
        if start_date and end_date:
            start_date = start_date.date()
            end_date = end_date.date()
            date_range = st.date_input(
                "Select Date Range",
                value=(end_date - timedelta(days=30), end_date),
                min_value=start_date,
                max_value=end_date,
                label_visibility="collapsed"
            )
        else:
            st.error(f"No date range available for {index_type}")
            return
        
        if len(date_range) == 2:
            st.markdown("### Actions")
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("📊 View Data", use_container_width=True):
                    st.session_state['show_section'] = 'data'
            with col2:
                if st.button("🧮 Indicators", use_container_width=True):
                    st.session_state['show_section'] = 'indicators'

            show_section = st.session_state.get('show_section', None)

            if show_section == 'data':
                df = db.get_index_data(index_type, date_range, selected_timeframe)
                st.write('Loaded DataFrame head:', df.head() if df is not None else 'None')
                if df is not None and not df.empty:
                    # Calculate technical indicators (for other sections, not for table)
                    df = calculate_moving_averages(df)
                    macd_data = calculate_macd(df)
                    df = pd.concat([df, macd_data], axis=1)
                    supertrend_data = calculate_supertrend(df)
                    df = pd.concat([df, supertrend_data], axis=1)
                    
                    # Display the price chart with volume
                    st.plotly_chart(plot_price_chart(df), use_container_width=True)
                    
                    # Add data summary metrics
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Latest Price", f"{df['close'].iloc[-1]:.2f}")
                    with col2:
                        price_change = ((df['close'].iloc[-1] - df['open'].iloc[0]) / df['open'].iloc[0]) * 100
                        st.metric("Price Change", f"{price_change:.2f}%")
                    with col3:
                        st.metric("Volume", f"{df['volume'].iloc[-1]:,.0f}")
                    with col4:
                        st.metric("High/Low", f"{df['high'].max():.2f}/{df['low'].min():.2f}")
                    
                    # Display the data table with improved formatting
                    st.markdown("### Data Table")
                    # Format the datetime column for better readability
                    df['datetime'] = pd.to_datetime(df['datetime'])
                    df['datetime'] = df['datetime'].dt.strftime('%Y-%m-%d %H:%M:%S')
                    
                    # Create a container for the table with fixed height and scrolling
                    table_container = st.container()
                    with table_container:
                        st.dataframe(
                            df[['datetime', 'open', 'high', 'low', 'close', 'volume']].style.format({
                                'open': '{:.2f}',
                                'high': '{:.2f}',
                                'low': '{:.2f}',
                                'close': '{:.2f}',
                                'volume': '{:,.0f}'
                            }).background_gradient(subset=['close'], cmap='RdYlGn'),
                            use_container_width=True,
                            height=400  # Fixed height with scrolling
                        )
                else:
                    st.error("No data available for the selected period.")
            elif show_section == 'indicators':
                # Get full data for calculations
                table_name = f"{index_type}_daily"
                full_start_date, full_end_date = db.get_available_dates(table_name)
                full_df = db.get_index_data(index_type, (full_start_date, full_end_date), selected_timeframe)
                
                if full_df is None or full_df.empty:
                    st.error("No data available for indicators.")
                else:
                    # --- Indicator UI logic STARTS here ---
                    if 'show_indicator_list' not in st.session_state:
                        st.session_state['show_indicator_list'] = False
                    if 'selected_indicator' not in st.session_state:
                        st.session_state['selected_indicator'] = None
                    if 'indicator_params' not in st.session_state:
                        st.session_state['indicator_params'] = {}
                    if 'indicator_ui_active' not in st.session_state:
                        st.session_state['indicator_ui_active'] = False
                    # Indicator selection workflow
                    if not st.session_state['indicator_ui_active']:
                        st.markdown("#### Add Technical Indicator")
                        if not st.session_state['show_indicator_list']:
                            if st.button("Add Indicator"):
                                st.session_state['show_indicator_list'] = True
                        else:
                            indicator = st.selectbox("Select Indicator", ["SMA", "EMA", "MACD", "SuperTrend"], key="indicator_select")
                            st.session_state['selected_indicator'] = indicator
                            params = {}
                            if indicator == "EMA":
                                period = st.number_input("Enter EMA Period", min_value=1, max_value=200, value=20, key="ema_period")
                                params['period'] = period
                            elif indicator == "SMA":
                                period = st.number_input("Enter SMA Period", min_value=1, max_value=200, value=20, key="sma_period")
                                params['period'] = period
                            elif indicator == "SuperTrend":
                                period = st.number_input("SuperTrend Period", min_value=1, max_value=50, value=10, key="st_period")
                                multiplier = st.number_input("SuperTrend Multiplier", min_value=1.0, max_value=10.0, value=3.0, step=0.1, key="st_multiplier")
                                params['period'] = period
                                params['multiplier'] = multiplier
                            st.session_state['indicator_params'] = params
                            if st.button("Show Indicator", key="show_indicator_btn"):
                                st.session_state['show_indicator_list'] = False
                                st.session_state['indicator_ui_active'] = True
                    # After Show Indicator, show indicator/backtest UI/results and a Change Indicator button
                    if st.session_state['indicator_ui_active']:
                        if st.button("Change Indicator", key="change_indicator_btn"):
                            st.session_state['indicator_ui_active'] = False
                            st.session_state['show_indicator_list'] = False
                            st.session_state['selected_indicator'] = None
                            st.session_state['indicator_params'] = {}
                            st.session_state.pop('backtest_results', None)
                        indicator = st.session_state['selected_indicator']
                        params = st.session_state['indicator_params']
                        plot_cols = []
                        
                        # Calculate indicators on full dataset (before filtering for date range)
                        if indicator == "EMA":
                            period = params.get('period', 20)
                            full_df[f'ema_{period}'] = calculate_ema(full_df['close'], period)
                            plot_cols = [f'ema_{period}']
                        elif indicator == "SMA":
                            period = params.get('period', 20)
                            # Calculate SMA on the full dataset
                            full_df[f'sma_{period}'] = full_df['close'].rolling(window=period, min_periods=1).mean()
                            plot_cols = [f'sma_{period}']
                        elif indicator == "MACD":
                            macd_data = calculate_macd(full_df)
                            full_df = pd.concat([full_df, macd_data], axis=1)
                            plot_cols = ['macd_line', 'signal_line']
                        elif indicator == "SuperTrend":
                            period = params.get('period', 10)
                            multiplier = params.get('multiplier', 3.0)
                            supertrend_data = calculate_supertrend(full_df, period=period, multiplier=multiplier)
                            # Add all columns from supertrend_data to full_df for signals
                            full_df = pd.concat([full_df, supertrend_data], axis=1)
                            # Remove duplicate columns to avoid DataFrame instead of Series
                            full_df = full_df.loc[:, ~full_df.columns.duplicated()]
                            plot_cols = ['supertrend']
                        # Now filter for the selected date range
                        display_df = full_df[
                            (full_df['datetime'].dt.date >= date_range[0]) & 
                            (full_df['datetime'].dt.date <= date_range[1])
                        ].copy()
                        
                        # Display the chart
                        rr_values = [1.0, 1.5, 2.0, 3.0, 4.0, 5.0, 'Until Opposite Signal']
                        results_list = []
                        trades_by_rr = {}  # Store trades for each R:R value
                        
                        for rr_ratio in rr_values:
                            df_bt = full_df[(full_df['datetime'].dt.date >= date_range[0]) & (full_df['datetime'].dt.date <= date_range[1])].copy().reset_index(drop=True)
                            # Calculate indicators and signals for the backtest period
                            if indicator == "SuperTrend":
                                period = params.get('period', 10)
                                multiplier = params.get('multiplier', 3.0)
                                supertrend_data = calculate_supertrend(df_bt, period=period, multiplier=multiplier)
                                df_bt = pd.concat([df_bt, supertrend_data], axis=1)
                                df_bt = df_bt.loc[:, ~df_bt.columns.duplicated()]
                                signals = get_supertrend_signals(df_bt)
                                df_bt = pd.concat([df_bt, signals], axis=1)
                                signal_column = 'supertrend_cross'
                            elif indicator == "EMA":
                                period = params.get('period', 20)
                                df_bt[f'ema_{period}'] = calculate_ema(df_bt['close'], period)
                                df_bt['signal'] = np.where(df_bt['close'] > df_bt[f'ema_{period}'], 'Bullish', 'Bearish')
                                df_bt['signal_prev'] = df_bt['signal'].shift(1)
                                df_bt['ema_cross'] = np.where(
                                    (df_bt['signal'] != df_bt['signal_prev']) & (df_bt['signal'].notna()),
                                    df_bt['signal'],
                                    None
                                )
                                signal_column = 'ema_cross'
                            elif indicator == "SMA":
                                period = params.get('period', 20)
                                df_bt[f'sma_{period}'] = df_bt['close'].rolling(window=period, min_periods=1).mean()
                                df_bt['signal'] = np.where(df_bt['close'] > df_bt[f'sma_{period}'], 'Bullish', 'Bearish')
                                df_bt['signal_prev'] = df_bt['signal'].shift(1)
                                df_bt['sma_cross'] = np.where(
                                    (df_bt['signal'] != df_bt['signal_prev']) & (df_bt['signal'].notna()),
                                    df_bt['signal'],
                                    None
                                )
                                signal_column = 'sma_cross'
                            
                            trades = []
                            in_trade = False
                            entry_idx = None
                            entry_price = None
                            direction = None
                            equity = [0]
                            
                            for i in range(1, len(df_bt)):
                                signal = df_bt[signal_column].iloc[i]
                                if not in_trade and signal in ['Bullish', 'Bearish']:
                                    entry_idx = i
                                    entry_price = df_bt['open'].iloc[i]
                                    direction = 'long' if signal == 'Bullish' else 'short'
                                    in_trade = True
                                elif in_trade:
                                    # 1. Check for signal flip (close and immediately re-enter in opposite direction)
                                    flip = (direction == 'long' and signal == 'Bearish') or (direction == 'short' and signal == 'Bullish')
                                    # Set stop loss based on indicator at entry
                                    if indicator == "SuperTrend":
                                        sl = df_bt['supertrend'].iloc[entry_idx]
                                    elif indicator == "EMA":
                                        sl = df_bt[f'ema_{params["period"]}'].iloc[entry_idx]
                                    elif indicator == "SMA":
                                        sl = df_bt[f'sma_{params["period"]}'].iloc[entry_idx]
                                    if direction == 'long':
                                        tgt = entry_price + (rr_ratio if rr_ratio != 'Until Opposite Signal' else 0) * (entry_price - sl)
                                    else:
                                        tgt = entry_price - (rr_ratio if rr_ratio != 'Until Opposite Signal' else 0) * (sl - entry_price)
                                    exit_idx = None
                                    exit_price = None
                                    points = 0
                                    if flip:
                                        exit_idx = i
                                        exit_price = df_bt['open'].iloc[i]
                                        points = exit_price - entry_price if direction == 'long' else entry_price - exit_price
                                        trades.append({
                                            'entry_time': df_bt['datetime'].iloc[entry_idx],
                                            'exit_time': df_bt['datetime'].iloc[exit_idx],
                                            'direction': direction,
                                            'entry_price': entry_price,
                                            'exit_price': exit_price,
                                            'points': points
                                        })
                                        equity.append(equity[-1] + points)
                                        # Immediately open new trade in opposite direction
                                        entry_idx = i
                                        entry_price = df_bt['open'].iloc[i]
                                        direction = 'long' if signal == 'Bullish' else 'short'
                                        # in_trade remains True
                                    # 2. Check for stop loss
                                    elif direction == 'long' and df_bt['low'].iloc[i] <= sl:
                                        exit_idx = i
                                        exit_price = sl
                                        points = exit_price - entry_price
                                        trades.append({
                                            'entry_time': df_bt['datetime'].iloc[entry_idx],
                                            'exit_time': df_bt['datetime'].iloc[exit_idx],
                                            'direction': direction,
                                            'entry_price': entry_price,
                                            'exit_price': exit_price,
                                            'points': points
                                        })
                                        equity.append(equity[-1] + points)
                                        in_trade = False
                                    elif direction == 'short' and df_bt['high'].iloc[i] >= sl:
                                        exit_idx = i
                                        exit_price = sl
                                        points = entry_price - exit_price
                                        trades.append({
                                            'entry_time': df_bt['datetime'].iloc[entry_idx],
                                            'exit_time': df_bt['datetime'].iloc[exit_idx],
                                            'direction': direction,
                                            'entry_price': entry_price,
                                            'exit_price': exit_price,
                                            'points': points
                                        })
                                        equity.append(equity[-1] + points)
                                        in_trade = False
                                    # 3. Check for R:R target
                                    elif direction == 'long' and rr_ratio != 'Until Opposite Signal' and df_bt['high'].iloc[i] >= tgt:
                                        exit_idx = i
                                        exit_price = tgt
                                        points = exit_price - entry_price
                                        trades.append({
                                            'entry_time': df_bt['datetime'].iloc[entry_idx],
                                            'exit_time': df_bt['datetime'].iloc[exit_idx],
                                            'direction': direction,
                                            'entry_price': entry_price,
                                            'exit_price': exit_price,
                                            'points': points
                                        })
                                        equity.append(equity[-1] + points)
                                        in_trade = False
                                    elif direction == 'short' and rr_ratio != 'Until Opposite Signal' and df_bt['low'].iloc[i] <= tgt:
                                        exit_idx = i
                                        exit_price = tgt
                                        points = entry_price - exit_price
                                        trades.append({
                                            'entry_time': df_bt['datetime'].iloc[entry_idx],
                                            'exit_time': df_bt['datetime'].iloc[exit_idx],
                                            'direction': direction,
                                            'entry_price': entry_price,
                                            'exit_price': exit_price,
                                            'points': points
                                        })
                                        equity.append(equity[-1] + points)
                                        in_trade = False
                            # If still in trade at the end, close at last price
                            if in_trade:
                                exit_idx = len(df_bt) - 1
                                exit_price = df_bt['close'].iloc[exit_idx]
                                points = exit_price - entry_price if direction == 'long' else entry_price - exit_price
                                trades.append({
                                    'entry_time': df_bt['datetime'].iloc[entry_idx],
                                    'exit_time': df_bt['datetime'].iloc[exit_idx],
                                    'direction': direction,
                                    'entry_price': entry_price,
                                    'exit_price': exit_price,
                                    'points': points
                                })
                                equity.append(equity[-1] + points)
                            total_points = sum([t['points'] for t in trades])
                            win_trades = [t for t in trades if t['points'] > 0]
                            loss_trades = [t for t in trades if t['points'] <= 0]
                            win_rate = f"{(len(win_trades)/len(trades)*100):.2f}%" if trades else '0%'
                            expectancy = f"{(np.mean([t['points'] for t in trades]) if trades else 0):.2f}"
                            # Max Drawdown calculation
                            equity_curve = equity
                            max_dd = 0
                            peak = equity_curve[0]
                            for x in equity_curve:
                                if x > peak:
                                    peak = x
                                dd = peak - x
                                if dd > max_dd:
                                    max_dd = dd
                            results_list.append({
                                'R:R': rr_ratio,
                                'Win Rate': win_rate,
                                'Expectancy (pts)': expectancy,
                                'Max Drawdown (pts)': f"{max_dd:.2f}",
                                'Cumulative PnL (pts)': total_points,
                                'Number of Trades': len(trades),
                                'Winning Trades': len(win_trades),
                                'Losing Trades': len(loss_trades)
                            })
                            # Store trades for this R:R value (as string for selectbox compatibility)
                            trades_by_rr[str(rr_ratio)] = trades.copy()
                        # Display results in a simple table, no row highlighting
                        st.markdown('### Backtest Results (Points Only)')
                        results_df = pd.DataFrame(results_list)
                        st.dataframe(
                            results_df,
                            use_container_width=True,
                            height=400
                        )
                        # Always show R:R selectbox after backtest results
                        rr_options = list(trades_by_rr.keys()) if trades_by_rr else [str(r) for r in rr_values]
                        selected_rr = st.selectbox('Select R:R to display Trades History', rr_options, index=0)
                        trades_for_selected_rr = trades_by_rr.get(selected_rr, [])
                        st.markdown(f'### Trades History (R:R = {selected_rr})')
                        if trades_for_selected_rr:
                            trades_df = pd.DataFrame(trades_for_selected_rr)
                            trades_df['entry_time'] = trades_df['entry_time'].astype(str)
                            trades_df['exit_time'] = trades_df['exit_time'].astype(str)
                            st.dataframe(
                                trades_df[['entry_time', 'exit_time', 'direction', 'entry_price', 'exit_price', 'points']],
                                use_container_width=True,
                                height=400
                            )
                        else:
                            st.info('No trades for this R:R value.')
                    # --- Indicator UI logic ENDS here ---
        else:
            st.error(f"No date range available for {index_type}")
            return
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        st.error("Please check your database connection and try again.")

def options_analysis(db):
    st.markdown("""
        <div style='text-align: center; padding: 1rem;'>
            <h2 style='color: #1E88E5;'>Options Analysis</h2>
            <p style='color: #666;'>Select an options strategy to analyze</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Strategy selection
    strategy = st.selectbox(
        "Select Strategy",
        ["Straddle", "Strangle", "Iron Condor", "Butterfly"],
        label_visibility="collapsed"
    )
    
    # Index selection
    index_type = st.selectbox(
        "Select Index",
        ["NIFTY", "BANKNIFTY"],
        label_visibility="collapsed"
    )
    
    # Expiry date selection
    expiry_date = st.date_input(
        "Select Expiry Date",
        value=datetime.now().date() + timedelta(days=7),
        min_value=datetime.now().date(),
        label_visibility="collapsed"
    )
    
    # Strike price selection
    atm_strike = st.number_input(
        "ATM Strike Price",
        min_value=0,
        step=100,
        label_visibility="collapsed"
    )
    
    # Strategy-specific inputs
    if strategy == "Straddle":
        st.markdown("### Straddle Strategy")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📊 Calculate Straddle", use_container_width=True):
                st.info("Straddle calculation will be implemented soon!")
        with col2:
            if st.button("📈 View Payoff", use_container_width=True):
                st.info("Payoff chart will be implemented soon!")
    
    elif strategy == "Strangle":
        st.markdown("### Strangle Strategy")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📊 Calculate Strangle", use_container_width=True):
                st.info("Strangle calculation will be implemented soon!")
        with col2:
            if st.button("📈 View Payoff", use_container_width=True):
                st.info("Payoff chart will be implemented soon!")
    
    elif strategy == "Iron Condor":
        st.markdown("### Iron Condor Strategy")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📊 Calculate Iron Condor", use_container_width=True):
                st.info("Iron Condor calculation will be implemented soon!")
        with col2:
            if st.button("📈 View Payoff", use_container_width=True):
                st.info("Payoff chart will be implemented soon!")
    
    elif strategy == "Butterfly":
        st.markdown("### Butterfly Strategy")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📊 Calculate Butterfly", use_container_width=True):
                st.info("Butterfly calculation will be implemented soon!")
        with col2:
            if st.button("📈 View Payoff", use_container_width=True):
                st.info("Payoff chart will be implemented soon!")

def calculate_orb_statistics(day_df, orb_high, orb_low, market_start, range_minutes):
    """Calculate detailed ORB statistics for a single day"""
    orb_window = day_df[day_df['time'] >= market_start].head(range_minutes)
    after_orb = day_df[day_df['datetime'] > orb_window['datetime'].max()]
    
    # Calculate range statistics
    orb_range = ((orb_high - orb_low) / orb_low) * 100
    day_range = ((day_df['high'].max() - day_df['low'].min()) / orb_low) * 100
    close_price = day_df['close'].iloc[-1]
    
    # Calculate movement from range
    movement = 0
    if close_price > orb_high:
        movement = ((close_price - orb_high) / orb_high) * 100
    elif close_price < orb_low:
        movement = ((close_price - orb_low) / orb_low) * 100
        
    # Time analysis
    first_break_time = None
    break_direction = None
    
    for _, row in after_orb.iterrows():
        if first_break_time is None:
            if row['high'] > orb_high:
                first_break_time = row['datetime']
                break_direction = 'high'
                break
            elif row['low'] < orb_low:
                first_break_time = row['datetime']
                break_direction = 'low'
                break
    
    return {
        'orb_range': orb_range,
        'day_range': day_range,
        'movement': movement,
        'first_break_time': first_break_time,
        'break_direction': break_direction,
        'close_price': close_price
    }

if __name__ == "__main__":
    main() 