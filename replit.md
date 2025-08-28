# Productivity Monitoring System

## Overview

A real-time production monitoring dashboard built with Streamlit that tracks manufacturing productivity metrics across multiple companies and production lines. The system focuses on Units Per Hour (UPH) performance analysis, achievement rate monitoring against targets, and defect tracking. It provides visual analytics for production managers to monitor efficiency, identify bottlenecks, and make data-driven decisions to optimize manufacturing operations.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture
- **Framework**: Streamlit web application with responsive layout
- **Visualization**: Plotly Express and Plotly Graph Objects for interactive charts and dashboards
- **Layout**: Wide layout with expandable sidebar for navigation and filtering
- **Caching**: Streamlit's built-in caching mechanism with 5-minute TTL for data refresh
- **State Management**: Session-based state management through Streamlit's native capabilities

### Backend Architecture
- **Data Processing**: Pandas-based data manipulation and analysis
- **Metrics Engine**: Custom utility functions for calculating KPIs including achievement rates, UPH variance, and defect rates
- **Data Abstraction**: Modular DataLoader class supporting multiple data source types
- **Error Handling**: Comprehensive exception handling with user-friendly error messages

### Data Storage Solutions
- **Multi-source Support**: Flexible data loading from CSV files, databases, or API endpoints
- **Fallback Strategy**: Automatic data source detection with graceful degradation to empty state
- **Schema**: Standardized production data schema with columns for Production_Date, Line_Name, Product_Group, Production_Qty, Defect_Qty, Work_Hours, Target_UPH, Actual_UPH, and Company

### Performance Monitoring
- **Key Metrics**: Target vs Actual UPH tracking, achievement rate calculations, defect rate monitoring
- **Real-time Updates**: Cached data loading with automatic refresh capabilities
- **Weighted Calculations**: Production quantity-weighted achievement rates for accurate performance assessment

## External Dependencies

### Core Libraries
- **Streamlit**: Web application framework for dashboard interface
- **Pandas**: Data manipulation and analysis
- **NumPy**: Numerical computing for statistical calculations
- **Plotly**: Interactive visualization library for charts and graphs

### Data Sources
- **CSV Files**: Local file-based data storage option
- **Database Integration**: Support for external database connections via environment variables
- **API Integration**: RESTful API data fetching capabilities with authentication

### Environment Configuration
- **Database**: Optional PostgreSQL or similar database connection
- **API Services**: External API integration with key-based authentication
- **File System**: Local CSV file support for standalone deployments