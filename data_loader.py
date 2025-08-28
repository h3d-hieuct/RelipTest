import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
import streamlit as st

class DataLoader:
    """
    Data loader class for the Productivity Monitoring System.
    Supports loading from CSV files, databases, or API endpoints.
    """
    
    def __init__(self):
        self.data_source = self._determine_data_source()
        
    def _determine_data_source(self):
        """Determine the appropriate data source based on available configuration."""
        # Check for CSV file
        if os.path.exists('production_data.csv'):
            return 'csv'
        
        # Check for database configuration
        db_config = {
            'host': os.getenv('DB_HOST'),
            'port': os.getenv('DB_PORT'),
            'database': os.getenv('DB_NAME'),
            'user': os.getenv('DB_USER'),
            'password': os.getenv('DB_PASSWORD')
        }
        
        if all(db_config.values()):
            return 'database'
        
        # Check for API configuration
        api_key = os.getenv('API_KEY')
        api_url = os.getenv('API_URL')
        
        if api_key and api_url:
            return 'api'
        
        # Default to empty state
        return 'empty'
    
    def get_production_data(self):
        """
        Load production data from the configured data source.
        Returns a pandas DataFrame with the required columns.
        """
        try:
            if self.data_source == 'csv':
                return self._load_from_csv()
            elif self.data_source == 'database':
                return self._load_from_database()
            elif self.data_source == 'api':
                return self._load_from_api()
            else:
                return self._get_empty_dataframe()
                
        except Exception as e:
            st.error(f"Error loading production data: {str(e)}")
            return self._get_empty_dataframe()
    
    def _load_from_csv(self):
        """Load data from CSV file."""
        try:
            df = pd.read_csv('production_data.csv')
            return self._validate_and_clean_data(df)
        except FileNotFoundError:
            st.error("production_data.csv file not found.")
            return self._get_empty_dataframe()
        except Exception as e:
            st.error(f"Error reading CSV file: {str(e)}")
            return self._get_empty_dataframe()
    
    def _load_from_database(self):
        """Load data from database using environment variables."""
        try:
            import psycopg2
            import sqlite3
            
            # Try PostgreSQL first
            try:
                import psycopg2.extras
                conn = psycopg2.connect(
                    host=os.getenv('DB_HOST'),
                    port=os.getenv('DB_PORT', 5432),
                    database=os.getenv('DB_NAME'),
                    user=os.getenv('DB_USER'),
                    password=os.getenv('DB_PASSWORD')
                )
                
                query = """
                SELECT 
                    production_date, line_name, product_group, production_qty,
                    defect_qty, work_hours, target_uph, actual_uph, company
                FROM production_view 
                WHERE production_date >= CURRENT_DATE - INTERVAL '30 days'
                ORDER BY production_date DESC, line_name
                """
                
                df = pd.read_sql(query, conn)
                conn.close()
                return self._validate_and_clean_data(df)
                
            except ImportError:
                # Fallback to SQLite
                if os.path.exists('production.db'):
                    conn = sqlite3.connect('production.db')
                    
                    query = """
                    SELECT 
                        production_date, line_name, product_group, production_qty,
                        defect_qty, work_hours, target_uph, actual_uph, company
                    FROM production_data 
                    WHERE production_date >= date('now', '-30 days')
                    ORDER BY production_date DESC, line_name
                    """
                    
                    df = pd.read_sql(query, conn)
                    conn.close()
                    return self._validate_and_clean_data(df)
                else:
                    st.error("Database file not found.")
                    return self._get_empty_dataframe()
                    
        except Exception as e:
            st.error(f"Database connection error: {str(e)}")
            return self._get_empty_dataframe()
    
    def _load_from_api(self):
        """Load data from API endpoint."""
        try:
            import requests
            
            api_url = os.getenv('API_URL')
            api_key = os.getenv('API_KEY')
            
            headers = {
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            }
            
            params = {
                'start_date': (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'),
                'end_date': datetime.now().strftime('%Y-%m-%d')
            }
            
            response = requests.get(api_url, headers=headers, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            if 'data' in data:
                df = pd.DataFrame(data['data'])
            else:
                df = pd.DataFrame(data)
                
            return self._validate_and_clean_data(df)
            
        except ImportError:
            st.error("requests library not available for API calls.")
            return self._get_empty_dataframe()
        except Exception as e:
            st.error(f"API connection error: {str(e)}")
            return self._get_empty_dataframe()
    
    def _validate_and_clean_data(self, df):
        """Validate and clean the loaded data."""
        if df.empty:
            return self._get_empty_dataframe()
        
        # Expected columns mapping (handle different naming conventions)
        column_mapping = {
            'production_date': 'Production_Date',
            'line_name': 'Line_Name', 
            'product_group': 'Product_Group',
            'production_qty': 'Production_Qty',
            'defect_qty': 'Defect_Qty',
            'work_hours': 'Work_Hours',
            'target_uph': 'Target_UPH',
            'actual_uph': 'Actual_UPH',
            'company': 'Company'
        }
        
        # Rename columns to standard format
        df.columns = [col.lower().replace(' ', '_') for col in df.columns]
        df = df.rename(columns=column_mapping)
        
        # Ensure required columns exist
        required_cols = list(column_mapping.values())
        missing_cols = [col for col in required_cols if col not in df.columns]
        
        if missing_cols:
            st.error(f"Missing required columns: {missing_cols}")
            return self._get_empty_dataframe()
        
        # Data type conversions and cleaning
        try:
            df['Production_Date'] = pd.to_datetime(df['Production_Date'])
            df['Production_Qty'] = pd.to_numeric(df['Production_Qty'], errors='coerce')
            df['Defect_Qty'] = pd.to_numeric(df['Defect_Qty'], errors='coerce')
            df['Work_Hours'] = pd.to_numeric(df['Work_Hours'], errors='coerce')
            df['Target_UPH'] = pd.to_numeric(df['Target_UPH'], errors='coerce')
            df['Actual_UPH'] = pd.to_numeric(df['Actual_UPH'], errors='coerce')
            
            # Remove rows with critical missing data
            df = df.dropna(subset=['Production_Date', 'Line_Name', 'Production_Qty', 'Target_UPH'])
            
            # Fill missing defect quantities with 0
            df['Defect_Qty'] = df['Defect_Qty'].fillna(0)
            
            # Calculate Actual UPH if missing
            mask_missing_actual = df['Actual_UPH'].isna()
            if mask_missing_actual.any():
                df.loc[mask_missing_actual, 'Actual_UPH'] = (
                    df.loc[mask_missing_actual, 'Production_Qty'] / 
                    df.loc[mask_missing_actual, 'Work_Hours']
                )
            
            # Remove invalid data
            df = df[df['Production_Qty'] > 0]
            df = df[df['Work_Hours'] > 0]
            df = df[df['Target_UPH'] > 0]
            
            return df.reset_index(drop=True)
            
        except Exception as e:
            st.error(f"Data validation error: {str(e)}")
            return self._get_empty_dataframe()
    
    def _get_empty_dataframe(self):
        """Return an empty DataFrame with the correct structure."""
        return pd.DataFrame(columns=[
            'Production_Date', 'Line_Name', 'Product_Group', 'Production_Qty',
            'Defect_Qty', 'Work_Hours', 'Target_UPH', 'Actual_UPH', 'Company'
        ])
    
    def get_data_source_info(self):
        """Return information about the current data source."""
        source_info = {
            'csv': 'Loading from production_data.csv file',
            'database': 'Loading from configured database',
            'api': 'Loading from API endpoint',
            'empty': 'No data source configured'
        }
        
        return {
            'source': self.data_source,
            'description': source_info.get(self.data_source, 'Unknown source')
        }
