"""
Demand forecasting using time-series analysis.
Predicts future product demand based on historical patterns.
All data is fictional for educational purposes only.
"""

import pandas as pd
import numpy as np
import os
from datetime import datetime, timedelta
from collections import defaultdict
from utils import ensure_dir, save_json, print_banner, print_section


def prepare_timeseries_data(orders_df: pd.DataFrame, products_df: pd.DataFrame) -> pd.DataFrame:
    """Prepare time-series data for forecasting."""
    
    # Convert to datetime
    orders_df['order_date'] = pd.to_datetime(orders_df['order_date'])
    
    # Aggregate by product and week
    orders_df['year_week'] = orders_df['order_date'].dt.to_period('W')
    
    weekly_sales = orders_df.groupby(['product_id', 'year_week']).agg({
        'quantity': 'sum',
        'total_price': 'sum'
    }).reset_index()
    
    # Merge with product info
    weekly_sales = weekly_sales.merge(
        products_df[['product_id', 'name', 'category', 'subcategory', 'price']],
        on='product_id',
        how='left'
    )
    
    return weekly_sales


def create_features(timeseries_df: pd.DataFrame, product_id: str) -> pd.DataFrame:
    """Create features for forecasting."""
    
    # Filter to specific product
    product_data = timeseries_df[timeseries_df['product_id'] == product_id].copy()
    
    if len(product_data) < 4:
        return None
    
    # Sort by date
    product_data = product_data.sort_values('year_week')
    
    # Convert period to timestamp for calculations
    product_data['timestamp'] = product_data['year_week'].dt.to_timestamp()
    
    # Create lag features
    product_data['lag_1'] = product_data['quantity'].shift(1)
    product_data['lag_2'] = product_data['quantity'].shift(2)
    product_data['lag_4'] = product_data['quantity'].shift(4)
    
    # Rolling averages
    product_data['rolling_mean_4'] = product_data['quantity'].rolling(window=4, min_periods=1).mean()
    product_data['rolling_mean_8'] = product_data['quantity'].rolling(window=8, min_periods=1).mean()
    
    # Trend (simple linear)
    product_data['week_number'] = range(len(product_data))
    
    # Seasonal features (week of year)
    product_data['week_of_year'] = product_data['timestamp'].dt.isocalendar().week
    
    # Drop rows with NaN in lag features
    product_data = product_data.bfill().fillna(0)
    
    return product_data


def simple_moving_average_forecast(historical_data: pd.DataFrame, periods: int = 4) -> dict:
    """Simple moving average forecast (baseline)."""
    
    recent_sales = historical_data['quantity'].tail(periods).values
    
    if len(recent_sales) == 0:
        return {
            "forecast": 0,
            "confidence_low": 0,
            "confidence_high": 0,
            "method": "insufficient_data"
        }
    
    forecast = np.mean(recent_sales)
    std = np.std(recent_sales) if len(recent_sales) > 1 else forecast * 0.2
    
    return {
        "forecast": float(forecast),
        "confidence_low": float(max(0, forecast - 1.96 * std)),
        "confidence_high": float(forecast + 1.96 * std),
        "method": "moving_average"
    }


def linear_regression_forecast(feature_data: pd.DataFrame) -> dict:
    """Linear regression with trend and seasonality."""
    
    if len(feature_data) < 4:
        return None
    
    from sklearn.linear_model import LinearRegression
    
    # Features
    feature_cols = ['week_number', 'lag_1', 'rolling_mean_4']
    available_features = [col for col in feature_cols if col in feature_data.columns]
    
    if not available_features:
        return None
    
    X = feature_data[available_features].values
    y = feature_data['quantity'].values
    
    # Train model
    model = LinearRegression()
    model.fit(X, y)
    
    # Predict next period
    last_row = feature_data.iloc[-1]
    next_features = []
    
    for col in available_features:
        if col == 'week_number':
            next_features.append(last_row[col] + 1)
        elif col == 'lag_1':
            next_features.append(last_row['quantity'])
        elif col == 'rolling_mean_4':
            next_features.append(last_row['rolling_mean_4'])
        else:
            next_features.append(last_row[col])
    
    next_X = np.array([next_features])
    forecast = model.predict(next_X)[0]
    
    # Estimate confidence interval from residuals
    predictions = model.predict(X)
    residuals = y - predictions
    std_error = np.std(residuals)
    
    return {
        "forecast": float(max(0, forecast)),
        "confidence_low": float(max(0, forecast - 1.96 * std_error)),
        "confidence_high": float(forecast + 1.96 * std_error),
        "method": "linear_regression",
        "r2_score": float(model.score(X, y))
    }


def forecast_product_demand(
    product_id: str,
    timeseries_df: pd.DataFrame,
    products_df: pd.DataFrame,
    horizon: int = 4
) -> dict:
    """Forecast demand for a product."""
    
    product = products_df[products_df['product_id'] == product_id]
    if len(product) == 0:
        return None
    
    product = product.iloc[0]
    
    # Get historical data
    historical = timeseries_df[timeseries_df['product_id'] == product_id].copy()
    
    if len(historical) == 0:
        return {
            "product_id": product_id,
            "product_name": product['name'],
            "category": product['category'],
            "forecast": 0,
            "confidence_low": 0,
            "confidence_high": 0,
            "method": "no_history",
            "historical_average": 0,
            "weeks_of_data": 0
        }
    
    historical = historical.sort_values('year_week')
    
    # Create features
    feature_data = create_features(timeseries_df, product_id)
    
    # Try advanced method first
    forecast_result = None
    if feature_data is not None and len(feature_data) >= 4:
        forecast_result = linear_regression_forecast(feature_data)
    
    # Fall back to simple method
    if forecast_result is None:
        forecast_result = simple_moving_average_forecast(historical, periods=4)
    
    # Calculate historical stats
    historical_avg = historical['quantity'].mean()
    historical_std = historical['quantity'].std()
    
    # Determine trend
    if len(historical) >= 4:
        recent_avg = historical['quantity'].tail(4).mean()
        older_avg = historical['quantity'].head(4).mean()
        
        if recent_avg > older_avg * 1.1:
            trend = "increasing"
        elif recent_avg < older_avg * 0.9:
            trend = "decreasing"
        else:
            trend = "stable"
    else:
        trend = "insufficient_data"
    
    return {
        "product_id": product_id,
        "product_name": product['name'],
        "category": product['category'],
        "subcategory": product['subcategory'],
        "forecast": forecast_result['forecast'],
        "confidence_low": forecast_result['confidence_low'],
        "confidence_high": forecast_result['confidence_high'],
        "method": forecast_result['method'],
        "historical_average": float(historical_avg),
        "historical_std": float(historical_std) if historical_std == historical_std else 0,
        "trend": trend,
        "weeks_of_data": len(historical),
        "horizon_weeks": horizon
    }


def evaluate_forecast_accuracy(
    timeseries_df: pd.DataFrame,
    products_df: pd.DataFrame,
    test_weeks: int = 4
) -> dict:
    """Evaluate forecast accuracy on historical data."""
    
    print_section("Evaluating Forecast Accuracy")
    
    # Get products with sufficient history
    product_weeks = timeseries_df.groupby('product_id').size()
    test_products = product_weeks[product_weeks >= test_weeks + 8].index
    
    if len(test_products) == 0:
        print("  Insufficient data for evaluation")
        return {}
    
    # Sample products for testing
    test_sample = np.random.choice(test_products, size=min(50, len(test_products)), replace=False)
    
    errors = []
    naive_errors = []
    
    for product_id in test_sample:
        product_data = timeseries_df[timeseries_df['product_id'] == product_id].sort_values('year_week')
        
        # Split into train and test
        train_data = product_data.iloc[:-test_weeks]
        test_data = product_data.iloc[-test_weeks:]
        
        # Create train timeseries
        train_ts = timeseries_df[
            (timeseries_df['product_id'] == product_id) &
            (timeseries_df['year_week'].isin(train_data['year_week']))
        ]
        
        # Forecast
        feature_data = create_features(train_ts, product_id)
        if feature_data is not None and len(feature_data) >= 4:
            forecast_result = linear_regression_forecast(feature_data)
        else:
            forecast_result = simple_moving_average_forecast(train_data, periods=4)
        
        # Compare to actual
        actual = test_data['quantity'].mean()
        predicted = forecast_result['forecast']
        
        error = abs(actual - predicted)
        errors.append(error)
        
        # Naive forecast (last value)
        naive_forecast = train_data['quantity'].iloc[-1]
        naive_error = abs(actual - naive_forecast)
        naive_errors.append(naive_error)
    
    mae = np.mean(errors)
    naive_mae = np.mean(naive_errors)
    improvement = ((naive_mae - mae) / naive_mae * 100) if naive_mae > 0 else 0
    
    print(f"  Products tested: {len(test_sample)}")
    print(f"  Mean Absolute Error: {mae:.2f} units")
    print(f"  Naive forecast MAE: {naive_mae:.2f} units")
    print(f"  Improvement over naive: {improvement:.1f}%")
    
    return {
        "mae": float(mae),
        "naive_mae": float(naive_mae),
        "improvement_pct": float(improvement),
        "products_tested": len(test_sample)
    }


def main():
    """Main execution function."""
    
    print_banner("Demand Forecasting")
    
    # Load data
    if not os.path.exists("data/products.csv") or not os.path.exists("data/orders.csv"):
        print("Error: Data files not found. Run data_generator.py first.")
        return
    
    products_df = pd.read_csv("data/products.csv")
    orders_df = pd.read_csv("data/orders.csv")
    
    # Prepare time-series data
    print("\n1. Preparing time-series data...")
    timeseries_df = prepare_timeseries_data(orders_df, products_df)
    print(f"   ✓ Processed {len(timeseries_df)} product-week records")
    
    # Evaluate accuracy
    evaluation = evaluate_forecast_accuracy(timeseries_df, products_df)
    
    # Generate forecasts for top products
    print_section("Generating Demand Forecasts")
    
    # Get products with good history
    product_weeks = timeseries_df.groupby('product_id').size()
    forecast_products = product_weeks[product_weeks >= 8].index
    
    # Sample top products by sales
    top_products = timeseries_df.groupby('product_id')['quantity'].sum().sort_values(ascending=False).head(50).index
    forecast_products = [pid for pid in top_products if pid in forecast_products]
    
    print(f"Forecasting demand for {len(forecast_products)} products...")
    
    forecasts = []
    for i, product_id in enumerate(forecast_products[:30], 1):
        forecast = forecast_product_demand(product_id, timeseries_df, products_df, horizon=4)
        if forecast:
            forecasts.append(forecast)
        
        if i % 10 == 0:
            print(f"  Progress: {i}/{min(30, len(forecast_products))} forecasts generated")
    
    print(f"\n✓ Generated {len(forecasts)} forecasts")
    
    # Save results
    output_dir = "outputs/forecasts"
    ensure_dir(output_dir)
    
    save_json({
        "evaluation": evaluation,
        "forecasts": forecasts,
        "generated_at": datetime.now().isoformat()
    }, f"{output_dir}/demand_forecasts.json")
    
    print(f"✓ Saved results to {output_dir}/demand_forecasts.json")
    
    # Print examples
    print_section("Example Forecasts")
    
    for i, forecast in enumerate(forecasts[:5], 1):
        print(f"\nExample {i}:")
        print(f"Product: {forecast['product_name']}")
        print(f"Category: {forecast['category']}")
        print(f"Historical average: {forecast['historical_average']:.1f} units/week")
        print(f"Trend: {forecast['trend']}")
        print(f"Data points: {forecast['weeks_of_data']} weeks")
        print(f"\n4-Week Forecast:")
        print(f"  Predicted demand: {forecast['forecast']:.1f} units/week")
        print(f"  Confidence interval: {forecast['confidence_low']:.1f} - {forecast['confidence_high']:.1f}")
        print(f"  Method: {forecast['method']}")
        
        # Recommendation
        if forecast['forecast'] > forecast['historical_average'] * 1.2:
            print(f"  💡 Recommendation: Stock up (demand increasing)")
        elif forecast['forecast'] < forecast['historical_average'] * 0.8:
            print(f"  💡 Recommendation: Reduce orders (demand decreasing)")
        else:
            print(f"  💡 Recommendation: Maintain normal stock levels")
        
        print("-" * 60)
    
    # Category analysis
    print_section("Category-Level Insights")
    
    category_forecasts = defaultdict(list)
    for f in forecasts:
        category_forecasts[f['category']].append(f['forecast'])
    
    print("Average forecasted demand by category:")
    for category, values in sorted(category_forecasts.items()):
        avg_demand = np.mean(values)
        print(f"  {category}: {avg_demand:.1f} units/week")
    
    print("\n" + "=" * 60)
    print("  Demand forecasting complete!")
    print("=" * 60)
    print("\nKey Benefits Demonstrated:")
    print("  ✓ Automated demand prediction")
    print("  ✓ Trend detection")
    print("  ✓ Confidence intervals for planning")
    print("  ✓ Category-level insights")
    print("\nReminder: All forecasts based on fictional data")


if __name__ == "__main__":
    main()
