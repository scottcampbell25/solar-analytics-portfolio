# Project Charter: Solar Output vs Weather Forecast Accuracy

## Project Overview
**Title**: Comparative Analysis of Weather Forecast Accuracy for Solar Power Prediction
**Duration**: 12 weeks (Jan - Mar 2025)
**Course Alignment**: ISM 680 (Modeling), ISM 681 (Dashboard), ISM 682 (Data Mart)

## Business Problem
Solar plant operators need accurate weather forecasts to predict power output for grid scheduling. Current forecasts from public APIs have unknown accuracy for solar-specific variables. This project quantifies forecast error and builds an improved prediction model.

## Objectives
1. Quantify forecast accuracy of NOAA and Tomorrow.io for solar-relevant variables
2. Build ML model combining weather forecasts with historical patterns
3. Create operational dashboard showing forecast confidence by lead time

## Data Sources
- **NREL PVDAQ**: 10-minute resolution PV output from 5 reference sites
- **NOAA Forecast API**: Hourly forecasts updated 4x daily
- **Tomorrow.io API**: Hourly forecasts with solar-specific variables

## Success Metrics
- Model RMSE < 15% for 1-hour ahead forecasts
- Dashboard updates automatically every hour
- Feature importance analysis identifies top 3 weather variables

## Deliverables
1. **ETL Pipeline**: Automated data collection from 3 APIs
2. **Feature Store**: PostgreSQL mart with 30+ engineered features
3. **Prediction Model**: XGBoost with 1-6 hour forecast horizons
4. **Power BI Dashboard**: Real-time accuracy tracking and alerts
5. **Technical Report**: 10-page analysis with business recommendations

## Timeline
- Week 1-2: Database setup and API integration
- Week 3-4: Historical data collection
- Week 5-6: Feature engineering
- Week 7-8: Model development
- Week 9-10: Dashboard creation
- Week 11-12: Documentation and presentation

## Risks & Mitigation
- **API Rate Limits**: Cache responses, use batch requests
- **Missing Data**: Implement forward-fill and interpolation
- **Model Overfitting**: Use time-based cross-validation

## Resources Required
- PostgreSQL database (local or cloud)
- Power BI Desktop license
- Python environment with ML libraries
- 100GB storage for historical data

## Stakeholders
- **Advisor**: Dr. [MIS Faculty Name]
- **Technical Reviewer**: [Peer Name]
- **Industry Context**: First Solar plant operations team (informal feedback only)
