import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date
import numpy as np
from data_loader import DataLoader
from utils import calculate_metrics, format_number, get_status_color

# Page configuration
st.set_page_config(
    page_title="Productivity Monitoring System",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize data loader
@st.cache_data(ttl=300)  # Cache for 5 minutes
def load_data():
    loader = DataLoader()
    return loader.get_production_data()

def main():
    # Header
    st.title("📊 Productivity Monitoring System")
    
    # Load data
    try:
        df = load_data()
        
        if df.empty:
            st.error("No production data available. Please check your data source configuration.")
            st.info("Expected data columns: Production_Date, Line_Name, Product_Group, Production_Qty, Defect_Qty, Work_Hours, Target_UPH, Actual_UPH, Company")
            return
            
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        st.info("Please ensure your data source is properly configured and accessible.")
        return

    # System Overview Section
    with st.expander("System Overview", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("""
            **Key Functions:**
            • Real-time monitoring by company and line
            • Achievement rate management vs target UPH
            • Data-first integration with Cursor AI visualization
            • Continuous feedback system for productivity improvement
            """)
        with col2:
            st.markdown("""
            **Key Metrics:**
            • Production Data: Line Name, Product Group
            • Production & Defect Quantity, Working Hours
            • Target UPH vs Actual UPH comparison
            • Company-wide performance analytics
            """)

    # Sidebar filters
    st.sidebar.header("🔍 Filters")
    
    # Date filter
    date_range = st.sidebar.date_input(
        "Production Date Range",
        value=(df['Production_Date'].min(), df['Production_Date'].max()),
        min_value=df['Production_Date'].min(),
        max_value=df['Production_Date'].max()
    )
    
    # Line Name filter
    line_options = ["All Lines"] + sorted(df['Line_Name'].unique().tolist())
    selected_lines = st.sidebar.selectbox("Line Name", line_options)
    
    # Product Group filter
    product_options = ["All Products"] + sorted(df['Product_Group'].unique().tolist())
    selected_product = st.sidebar.selectbox("Product Group", product_options)
    
    # Company filter
    company_options = ["All Companies"] + sorted(df['Company'].unique().tolist())
    selected_company = st.sidebar.selectbox("Company", company_options)

    # Apply filters
    filtered_df = df.copy()
    
    # Date filter
    if isinstance(date_range, tuple) and len(date_range) == 2:
        filtered_df = filtered_df[
            (filtered_df['Production_Date'] >= pd.to_datetime(date_range[0])) &
            (filtered_df['Production_Date'] <= pd.to_datetime(date_range[1]))
        ]
    
    # Other filters
    if selected_lines != "All Lines":
        filtered_df = filtered_df[filtered_df['Line_Name'] == selected_lines]
    if selected_product != "All Products":
        filtered_df = filtered_df[filtered_df['Product_Group'] == selected_product]
    if selected_company != "All Companies":
        filtered_df = filtered_df[filtered_df['Company'] == selected_company]

    if filtered_df.empty:
        st.warning("No data available for the selected filters. Please adjust your selection.")
        return

    # Calculate metrics
    metrics = calculate_metrics(filtered_df)
    
    # KPI Section
    st.subheader("Key Performance Indicators")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Target UPH",
            value=f"{metrics['avg_target_uph']:.0f}",
            delta=None,
            help="Lines per hour average"
        )
    
    with col2:
        st.metric(
            label="Actual UPH", 
            value=f"{metrics['avg_actual_uph']:.0f}",
            delta=f"{metrics['uph_variance']:.1f}%",
            delta_color="normal" if metrics['uph_variance'] >= 0 else "inverse",
            help="Current performance"
        )
    
    with col3:
        st.metric(
            label="Total Production",
            value=format_number(metrics['total_production']),
            help="Units today"
        )
        
    with col4:
        achievement_rate = metrics['overall_achievement_rate']
        st.metric(
            label="Achievement Rate",
            value=f"{achievement_rate:.1f}%",
            delta=f"{achievement_rate - 100:.1f}%",
            delta_color="normal" if achievement_rate >= 100 else "inverse",
            help="Overall performance vs target"
        )

    # Charts Section
    st.subheader("Performance Analytics")
    
    chart_col1, chart_col2 = st.columns(2)
    
    with chart_col1:
        st.subheader("📊 Target vs Actual UPH by Line")
        
        # Group by line for comparison
        line_summary = filtered_df.groupby('Line_Name').agg({
            'Target_UPH': 'mean',
            'Actual_UPH': 'mean'
        }).reset_index()
        
        fig_bar = go.Figure()
        
        fig_bar.add_trace(go.Bar(
            name='Target UPH',
            x=line_summary['Line_Name'],
            y=line_summary['Target_UPH'],
            marker_color='lightblue',
            text=line_summary['Target_UPH'].round(0),
            textposition='auto'
        ))
        
        fig_bar.add_trace(go.Bar(
            name='Actual UPH',
            x=line_summary['Line_Name'],
            y=line_summary['Actual_UPH'],
            marker_color='darkgreen',
            text=line_summary['Actual_UPH'].round(0),
            textposition='auto'
        ))
        
        fig_bar.update_layout(
            barmode='group',
            xaxis_title='Production Line',
            yaxis_title='Units Per Hour',
            height=400,
            showlegend=True
        )
        
        st.plotly_chart(fig_bar, use_container_width=True)
    
    with chart_col2:
        st.subheader("🥧 UPH Achievement Rate by Line")
        
        # Calculate achievement rates by line
        line_achievement = filtered_df.groupby('Line_Name').apply(
            lambda x: (x['Actual_UPH'].sum() / x['Target_UPH'].sum() * 100)
        ).reset_index(name='Achievement_Rate')
        
        # Color coding based on achievement
        colors = ['#2ecc71' if rate >= 100 else '#f39c12' if rate >= 90 else '#e74c3c' 
                 for rate in line_achievement['Achievement_Rate']]
        
        fig_pie = go.Figure(data=[go.Pie(
            labels=line_achievement['Line_Name'],
            values=line_achievement['Achievement_Rate'],
            hole=0.4,
            marker=dict(colors=colors),
            textinfo='label+percent',
            textposition='auto'
        )])
        
        fig_pie.update_layout(
            title_text="Achievement Rate Distribution",
            height=400,
            showlegend=True,
            annotations=[dict(text='Achievement<br>Rate', x=0.5, y=0.5, font_size=16, showarrow=False)]
        )
        
        st.plotly_chart(fig_pie, use_container_width=True)

    # Anomaly Detection Section
    st.subheader("🚨 Production Anomaly Detection")
    
    # Identify anomalies
    anomalies = filtered_df[
        (filtered_df['Actual_UPH'] < filtered_df['Target_UPH'] * 0.8) |  # 20% below target
        (filtered_df['Defect_Qty'] / filtered_df['Production_Qty'] > 0.05)  # 5% defect rate
    ]
    
    if not anomalies.empty:
        st.warning(f"⚠️ {len(anomalies)} anomalies detected requiring attention")
        
        anomaly_summary = anomalies.groupby('Line_Name').agg({
            'Production_Date': 'count',
            'Actual_UPH': 'mean',
            'Target_UPH': 'mean'
        }).rename(columns={'Production_Date': 'Anomaly_Count'}).reset_index()
        
        for _, row in anomaly_summary.iterrows():
            achievement = (row['Actual_UPH'] / row['Target_UPH']) * 100
            st.error(f"Line {row['Line_Name']}: {row['Anomaly_Count']} anomalies, {achievement:.1f}% achievement rate")
    else:
        st.success("✅ No production anomalies detected in the selected period")

    # Detailed Data Table
    st.subheader("📋 Production Data Details")
    
    # Add calculated columns
    display_df = filtered_df.copy()
    display_df['Achievement_Rate'] = (display_df['Actual_UPH'] / display_df['Target_UPH'] * 100).round(1)
    display_df['Defect_Rate'] = (display_df['Defect_Qty'] / display_df['Production_Qty'] * 100).round(2)
    
    # Reorder columns for better display
    columns_order = [
        'Production_Date', 'Line_Name', 'Product_Group', 'Production_Qty', 
        'Defect_Qty', 'Work_Hours', 'Target_UPH', 'Actual_UPH', 
        'Achievement_Rate', 'Defect_Rate', 'Company'
    ]
    
    display_df = display_df[columns_order]
    
    # Format display
    display_df['Production_Date'] = display_df['Production_Date'].dt.strftime('%Y-%m-%d')
    display_df['Achievement_Rate'] = display_df['Achievement_Rate'].astype(str) + '%'
    display_df['Defect_Rate'] = display_df['Defect_Rate'].astype(str) + '%'
    
    st.dataframe(
        display_df,
        use_container_width=True,
        height=400,
        column_config={
            "Production_Date": st.column_config.TextColumn("Date"),
            "Line_Name": st.column_config.TextColumn("Line"),
            "Product_Group": st.column_config.TextColumn("Product"),
            "Production_Qty": st.column_config.NumberColumn("Production", format="%d"),
            "Defect_Qty": st.column_config.NumberColumn("Defects", format="%d"),
            "Work_Hours": st.column_config.NumberColumn("Hours", format="%.1f"),
            "Target_UPH": st.column_config.NumberColumn("Target UPH", format="%.0f"),
            "Actual_UPH": st.column_config.NumberColumn("Actual UPH", format="%.0f"),
            "Achievement_Rate": st.column_config.TextColumn("Achievement"),
            "Defect_Rate": st.column_config.TextColumn("Defect Rate"),
            "Company": st.column_config.TextColumn("Company")
        }
    )
    
    # Summary Statistics
    st.subheader("📊 Summary Statistics")
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Production Summary**")
        summary_stats = {
            "Total Lines": filtered_df['Line_Name'].nunique(),
            "Total Companies": filtered_df['Company'].nunique(),
            "Average Production per Line": f"{filtered_df['Production_Qty'].mean():.0f} units",
            "Average Defect Rate": f"{(filtered_df['Defect_Qty'].sum() / filtered_df['Production_Qty'].sum() * 100):.2f}%",
            "Total Work Hours": f"{filtered_df['Work_Hours'].sum():.1f} hours"
        }
        
        for key, value in summary_stats.items():
            st.write(f"• **{key}**: {value}")
    
    with col2:
        st.write("**Performance Summary**")
        performance_stats = {
            "Lines Above Target": len(filtered_df[filtered_df['Actual_UPH'] >= filtered_df['Target_UPH']]),
            "Lines Below Target": len(filtered_df[filtered_df['Actual_UPH'] < filtered_df['Target_UPH']]),
            "Best Performing Line": filtered_df.loc[filtered_df['Actual_UPH'].idxmax(), 'Line_Name'],
            "Highest Achievement Rate": f"{((filtered_df['Actual_UPH'] / filtered_df['Target_UPH']).max() * 100):.1f}%",
            "Lowest Achievement Rate": f"{((filtered_df['Actual_UPH'] / filtered_df['Target_UPH']).min() * 100):.1f}%"
        }
        
        for key, value in performance_stats.items():
            st.write(f"• **{key}**: {value}")

    # Auto-refresh option
    st.sidebar.markdown("---")
    auto_refresh = st.sidebar.checkbox("Enable Auto-refresh (30s)")
    if auto_refresh:
        import time
        time.sleep(30)
        st.rerun()

if __name__ == "__main__":
    main()
