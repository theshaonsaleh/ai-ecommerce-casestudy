"""
Interactive dashboard for AI e-commerce case study.
All data is fictional for educational purposes only.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import os
import json
from datetime import datetime

# Page config
st.set_page_config(
    page_title="AI E-Commerce Case Study",
    page_icon="🛍️",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
.main-header {
    font-size: 2.5rem;
    font-weight: bold;
    color: #1f77b4;
}
.sub-header {
    font-size: 1.5rem;
    color: #555;
    margin-bottom: 20px;
}
.disclaimer {
    background-color: #fff3cd;
    padding: 15px;
    border-radius: 5px;
    border-left: 5px solid #ffc107;
    margin: 20px 0;
}
</style>
""", unsafe_allow_html=True)

# Load data
@st.cache_data
def load_data():
    """Load all datasets."""
    data = {}
    
    # Check if data files exist
    if os.path.exists('data/products.csv'):
        data['products'] = pd.read_csv('data/products.csv')
    
    if os.path.exists('data/customers.csv'):
        data['customers'] = pd.read_csv('data/customers.csv')
    
    if os.path.exists('data/orders.csv'):
        data['orders'] = pd.read_csv('data/orders.csv')
        data['orders']['order_date'] = pd.to_datetime(data['orders']['order_date'])
    
    if os.path.exists('data/reviews.csv'):
        data['reviews'] = pd.read_csv('data/reviews.csv')
        data['reviews']['review_date'] = pd.to_datetime(data['reviews']['review_date'])
    
    return data


@st.cache_data
def load_results():
    """Load AI results."""
    results = {}
    
    if os.path.exists('outputs/descriptions/descriptions.json'):
        with open('outputs/descriptions/descriptions.json', 'r') as f:
            results['descriptions'] = json.load(f)
    
    if os.path.exists('outputs/sentiment/sentiment_analysis.json'):
        with open('outputs/sentiment/sentiment_analysis.json', 'r') as f:
            results['sentiment'] = json.load(f)
    
    if os.path.exists('outputs/recommendations/recommendations.json'):
        with open('outputs/recommendations/recommendations.json', 'r') as f:
            results['recommendations'] = json.load(f)
    
    if os.path.exists('outputs/forecasts/demand_forecasts.json'):
        with open('outputs/forecasts/demand_forecasts.json', 'r') as f:
            results['forecasts'] = json.load(f)
    
    return results


def show_overview(data):
    """Show overview page."""
    st.markdown('<p class="main-header">🛍️ AI for E-Commerce: Interactive Dashboard</p>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="disclaimer">
        <strong>⚠️ Disclaimer:</strong> This is a personal learning project for educational purposes only. 
        All data is completely fictional. Not affiliated with any business.
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("### About This Project")
    st.write("""
    This dashboard demonstrates how AI can help online retail businesses through practical examples
    using **Northwind Home Goods**, a fictional online retailer. Explore four key AI applications:
    
    - 📝 **Product Descriptions**: LLM-powered content generation
    - 💬 **Sentiment Analysis**: Review insights and theme extraction
    - 🎯 **Recommendations**: Personalized product suggestions
    - 📈 **Demand Forecasting**: Predictive inventory planning
    """)
    
    if not data:
        st.warning("⚠️ No data found. Please run `python src/data_generator.py` first.")
        return
    
    # Key metrics
    st.markdown("### Dataset Overview")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if 'products' in data:
            st.metric("Products", f"{len(data['products']):,}")
        else:
            st.metric("Products", "N/A")
    
    with col2:
        if 'customers' in data:
            st.metric("Customers", f"{len(data['customers']):,}")
        else:
            st.metric("Customers", "N/A")
    
    with col3:
        if 'orders' in data:
            st.metric("Orders", f"{len(data['orders']):,}")
        else:
            st.metric("Orders", "N/A")
    
    with col4:
        if 'reviews' in data:
            st.metric("Reviews", f"{len(data['reviews']):,}")
        else:
            st.metric("Reviews", "N/A")
    
    # Charts
    if 'orders' in data and 'products' in data:
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Sales by Category")
            orders_products = data['orders'].merge(data['products'], on='product_id')
            category_sales = orders_products.groupby('category')['total_price'].sum().sort_values(ascending=False)
            
            fig = px.bar(
                x=category_sales.index,
                y=category_sales.values,
                labels={'x': 'Category', 'y': 'Total Sales ($)'},
                color=category_sales.values,
                color_continuous_scale='Blues'
            )
            fig.update_layout(showlegend=False, height=400)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.markdown("#### Sales Over Time")
            monthly_sales = data['orders'].groupby(data['orders']['order_date'].dt.to_period('M'))['total_price'].sum()
            
            fig = px.line(
                x=[str(p) for p in monthly_sales.index],
                y=monthly_sales.values,
                labels={'x': 'Month', 'y': 'Total Sales ($)'}
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)


def show_descriptions(results):
    """Show product descriptions page."""
    st.markdown('<p class="main-header">📝 Product Description Generator</p>', unsafe_allow_html=True)
    
    st.markdown("""
    This demo shows how LLMs can automatically generate engaging, SEO-friendly product descriptions
    at scale. The system can process hundreds of products in minutes while maintaining consistent
    tone and quality.
    """)
    
    if 'descriptions' not in results:
        st.warning("⚠️ No results found. Run `python src/product_descriptions.py` first.")
        return
    
    descriptions = results['descriptions']
    
    # Metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Descriptions Generated", len(descriptions))
    
    with col2:
        avg_words = np.mean([d['word_count'] for d in descriptions])
        st.metric("Avg Word Count", f"{avg_words:.0f}")
    
    with col3:
        llm_count = sum(1 for d in descriptions if d.get('method') == 'LLM')
        st.metric("LLM-Generated", f"{llm_count}/{len(descriptions)}")
    
    # Word count distribution
    st.markdown("#### Word Count Distribution")
    word_counts = [d['word_count'] for d in descriptions]
    fig = px.histogram(
        x=word_counts,
        nbins=20,
        labels={'x': 'Word Count', 'y': 'Frequency'}
    )
    fig.update_layout(height=300)
    st.plotly_chart(fig, use_container_width=True)
    
    # Examples
    st.markdown("#### Example Descriptions")
    
    for i, desc in enumerate(descriptions[:3]):
        with st.expander(f"📦 {desc['name']} (${desc['price']:.2f})"):
            st.markdown(f"**Category:** {desc['category']} - {desc['subcategory']}")
            st.markdown(f"**Method:** {desc['method']}")
            st.markdown(f"**Word Count:** {desc['word_count']}")
            st.markdown("---")
            st.markdown(desc['description'])


def show_sentiment(results, data):
    """Show sentiment analysis page."""
    st.markdown('<p class="main-header">💬 Review Sentiment Analysis</p>', unsafe_allow_html=True)
    
    st.markdown("""
    This demo extracts sentiment and themes from customer reviews, helping identify
    what customers love and what needs improvement.
    """)
    
    if 'sentiment' not in results:
        st.warning("⚠️ No results found. Run `python src/sentiment_analysis.py` first.")
        return
    
    sentiment_results = results['sentiment']
    
    # Overall metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Products Analyzed", len(sentiment_results))
    
    with col2:
        avg_positive = np.mean([r['analysis']['overall_sentiment']['positive'] for r in sentiment_results])
        st.metric("Avg Positive %", f"{avg_positive:.1f}%")
    
    with col3:
        total_reviews = sum(r['review_count'] for r in sentiment_results)
        st.metric("Total Reviews", total_reviews)
    
    # Sentiment distribution
    st.markdown("#### Sentiment Distribution Across Products")
    
    sentiment_data = []
    for r in sentiment_results:
        sentiment_data.append({
            'Product': r['product_name'][:30] + '...' if len(r['product_name']) > 30 else r['product_name'],
            'Positive': r['analysis']['overall_sentiment']['positive'],
            'Negative': r['analysis']['overall_sentiment']['negative'],
            'Neutral': r['analysis']['overall_sentiment']['neutral']
        })
    
    df_sentiment = pd.DataFrame(sentiment_data)
    
    fig = go.Figure()
    fig.add_trace(go.Bar(name='Positive', x=df_sentiment['Product'], y=df_sentiment['Positive'], marker_color='green'))
    fig.add_trace(go.Bar(name='Negative', x=df_sentiment['Product'], y=df_sentiment['Negative'], marker_color='red'))
    fig.add_trace(go.Bar(name='Neutral', x=df_sentiment['Product'], y=df_sentiment['Neutral'], marker_color='gray'))
    
    fig.update_layout(barmode='stack', height=400, xaxis_tickangle=-45)
    st.plotly_chart(fig, use_container_width=True)
    
    # Theme analysis
    st.markdown("#### Common Themes")
    
    all_themes = []
    for r in sentiment_results:
        for theme in r['analysis']['key_themes']:
            all_themes.append(theme['theme'])
    
    if all_themes:
        from collections import Counter
        theme_counts = Counter(all_themes)
        
        fig = px.bar(
            x=list(theme_counts.keys()),
            y=list(theme_counts.values()),
            labels={'x': 'Theme', 'y': 'Mentions'},
            color=list(theme_counts.values()),
            color_continuous_scale='Viridis'
        )
        fig.update_layout(showlegend=False, height=300)
        st.plotly_chart(fig, use_container_width=True)
    
    # Example analysis
    st.markdown("#### Example Analysis")
    
    for i, result in enumerate(sentiment_results[:2]):
        with st.expander(f"📦 {result['product_name']}"):
            col1, col2 = st.columns([1, 2])
            
            with col1:
                st.markdown("**Metrics**")
                st.metric("Reviews", result['review_count'])
                st.metric("Avg Rating", f"{result['average_rating']:.1f}/5.0")
            
            with col2:
                st.markdown("**Sentiment Breakdown**")
                analysis = result['analysis']
                st.write(f"🟢 Positive: {analysis['overall_sentiment']['positive']:.1f}%")
                st.write(f"🔴 Negative: {analysis['overall_sentiment']['negative']:.1f}%")
                st.write(f"⚪ Neutral: {analysis['overall_sentiment']['neutral']:.1f}%")
            
            st.markdown("**Summary**")
            st.info(analysis['summary'])
            
            if analysis.get('recommendation'):
                st.markdown("**Recommendation**")
                st.success(analysis['recommendation'])


def show_recommendations(results):
    """Show recommendations page."""
    st.markdown('<p class="main-header">🎯 Product Recommendations</p>', unsafe_allow_html=True)
    
    st.markdown("""
    This demo generates personalized product recommendations using collaborative filtering
    and content-based similarity.
    """)
    
    if 'recommendations' not in results:
        st.warning("⚠️ No results found. Run `python src/recommendations.py` first.")
        return
    
    rec_data = results['recommendations']
    
    # Evaluation metrics
    if 'evaluation' in rec_data:
        st.markdown("#### Recommendation Quality")
        
        eval_data = rec_data['evaluation']
        
        col1, col2, col3 = st.columns(3)
        
        methods = ['copurchase', 'similarity', 'hybrid']
        for i, (col, method) in enumerate(zip([col1, col2, col3], methods)):
            with col:
                if method in eval_data:
                    hit_rate = eval_data[method]['hit_rate']
                    st.metric(f"{method.capitalize()}", f"{hit_rate:.1f}% hit rate")
    
    # Example recommendations
    if 'customer_recommendations' in rec_data:
        st.markdown("#### Example Customer Recommendations")
        
        customer_recs = rec_data['customer_recommendations']
        
        for i, rec in enumerate(customer_recs[:3]):
            with st.expander(f"👤 Customer {rec['customer_id']}"):
                st.markdown(f"**Purchase History:** {rec['purchase_count']} products")
                st.markdown(f"**Recommendation Method:** {rec['method']}")
                
                st.markdown("**Top 5 Recommendations:**")
                
                for j, item in enumerate(rec['recommendations'][:5], 1):
                    st.markdown(f"{j}. **{item['product_name']}** - ${item['price']:.2f}")
                    st.markdown(f"   *Score: {item['score']:.3f} | {item['reason']}*")


def show_forecasts(results):
    """Show demand forecasting page."""
    st.markdown('<p class="main-header">📈 Demand Forecasting</p>', unsafe_allow_html=True)
    
    st.markdown("""
    This demo predicts future product demand using time-series analysis, helping optimize
    inventory management.
    """)
    
    if 'forecasts' not in results:
        st.warning("⚠️ No results found. Run `python src/demand_forecast.py` first.")
        return
    
    forecast_data = results['forecasts']
    
    # Evaluation metrics
    if 'evaluation' in forecast_data:
        st.markdown("#### Forecast Accuracy")
        
        eval_data = forecast_data['evaluation']
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Products Tested", eval_data.get('products_tested', 0))
        
        with col2:
            mae = eval_data.get('mae', 0)
            st.metric("Mean Absolute Error", f"{mae:.1f} units")
        
        with col3:
            improvement = eval_data.get('improvement_pct', 0)
            st.metric("Improvement vs Naive", f"{improvement:.1f}%")
    
    # Forecasts
    if 'forecasts' in forecast_data:
        forecasts = forecast_data['forecasts']
        
        st.markdown("#### Demand Forecasts by Category")
        
        # Category breakdown
        category_forecasts = {}
        for f in forecasts:
            cat = f['category']
            if cat not in category_forecasts:
                category_forecasts[cat] = []
            category_forecasts[cat].append(f['forecast'])
        
        cat_names = list(category_forecasts.keys())
        cat_avgs = [np.mean(vals) for vals in category_forecasts.values()]
        
        fig = px.bar(
            x=cat_names,
            y=cat_avgs,
            labels={'x': 'Category', 'y': 'Avg Forecast (units/week)'},
            color=cat_avgs,
            color_continuous_scale='Blues'
        )
        fig.update_layout(showlegend=False, height=400)
        st.plotly_chart(fig, use_container_width=True)
        
        # Example forecasts
        st.markdown("#### Example Forecasts")
        
        for i, forecast in enumerate(forecasts[:3]):
            with st.expander(f"📦 {forecast['product_name']}"):
                col1, col2 = st.columns([1, 2])
                
                with col1:
                    st.markdown("**Historical**")
                    st.metric("Avg Demand", f"{forecast['historical_average']:.1f} units/week")
                    st.metric("Trend", forecast['trend'])
                    st.metric("Data Points", f"{forecast['weeks_of_data']} weeks")
                
                with col2:
                    st.markdown("**4-Week Forecast**")
                    st.metric("Predicted", f"{forecast['forecast']:.1f} units/week")
                    st.write(f"Confidence Interval: {forecast['confidence_low']:.1f} - {forecast['confidence_high']:.1f}")
                    st.write(f"Method: {forecast['method']}")
                
                # Visualization
                historical_vals = [forecast['historical_average']] * 4
                forecast_vals = [forecast['forecast']] * 4
                
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=[1, 2, 3, 4],
                    y=historical_vals,
                    name='Historical Avg',
                    line=dict(color='blue', dash='dash')
                ))
                fig.add_trace(go.Scatter(
                    x=[1, 2, 3, 4],
                    y=forecast_vals,
                    name='Forecast',
                    line=dict(color='red')
                ))
                fig.update_layout(
                    xaxis_title='Week',
                    yaxis_title='Units',
                    height=300
                )
                st.plotly_chart(fig, use_container_width=True)


# Main app
def main():
    """Main dashboard."""
    
    # Sidebar navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.radio(
        "Select Page",
        ["Overview", "Product Descriptions", "Sentiment Analysis", "Recommendations", "Demand Forecasting"]
    )
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("### About")
    st.sidebar.info("""
    **Personal learning project**
    
    All data is fictional.
    Not affiliated with any business.
    
    Created for educational purposes.
    """)
    
    # Load data
    data = load_data()
    results = load_results()
    
    # Route to pages
    if page == "Overview":
        show_overview(data)
    elif page == "Product Descriptions":
        show_descriptions(results)
    elif page == "Sentiment Analysis":
        show_sentiment(results, data)
    elif page == "Recommendations":
        show_recommendations(results)
    elif page == "Demand Forecasting":
        show_forecasts(results)


if __name__ == "__main__":
    main()
