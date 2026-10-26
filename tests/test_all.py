"""
Tests for AI e-commerce demos.
All tests use fictional data only.
"""

import pytest
import pandas as pd
import numpy as np
import os
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from utils import Config, cosine_similarity, calculate_sentiment_score
from data_generator import generate_products, generate_customers, generate_orders, generate_reviews


class TestDataGeneration:
    """Test synthetic data generation."""
    
    def test_generate_products(self):
        """Test product generation."""
        products_df = generate_products(n=100)
        
        assert len(products_df) <= 100
        assert len(products_df) > 0
        assert 'product_id' in products_df.columns
        assert 'name' in products_df.columns
        assert 'price' in products_df.columns
        assert 'category' in products_df.columns
        
        # Check prices are positive
        assert (products_df['price'] > 0).all()
        
        # Check product IDs are unique
        assert len(products_df['product_id'].unique()) == len(products_df)
    
    def test_generate_customers(self):
        """Test customer generation."""
        customers_df = generate_customers(n=50)
        
        assert len(customers_df) == 50
        assert 'customer_id' in customers_df.columns
        assert 'email' in customers_df.columns
        
        # Check all emails contain @
        assert all('@' in email for email in customers_df['email'])
        
        # Check customer IDs are unique
        assert len(customers_df['customer_id'].unique()) == 50
    
    def test_generate_orders(self):
        """Test order generation."""
        products_df = generate_products(n=50)
        customers_df = generate_customers(n=20)
        orders_df = generate_orders(customers_df, products_df, n=100)
        
        # Orders can have multiple items, so total rows >= requested orders
        assert len(orders_df) >= 100
        assert 'order_id' in orders_df.columns
        assert 'customer_id' in orders_df.columns
        assert 'product_id' in orders_df.columns
        assert 'total_price' in orders_df.columns
        
        # Check all customers exist
        assert set(orders_df['customer_id']).issubset(set(customers_df['customer_id']))
        
        # Check all products exist
        assert set(orders_df['product_id']).issubset(set(products_df['product_id']))
        
        # Check prices are positive
        assert (orders_df['total_price'] > 0).all()
    
    def test_generate_reviews(self):
        """Test review generation."""
        products_df = generate_products(n=50)
        customers_df = generate_customers(n=20)
        orders_df = generate_orders(customers_df, products_df, n=100)
        reviews_df = generate_reviews(orders_df, products_df, customers_df, n=50)
        
        assert len(reviews_df) <= 50
        assert 'review_id' in reviews_df.columns
        assert 'rating' in reviews_df.columns
        assert 'review_text' in reviews_df.columns
        
        # Check ratings are in valid range
        assert (reviews_df['rating'] >= 1).all()
        assert (reviews_df['rating'] <= 5).all()
        
        # Check all reviews have text
        assert all(len(text) > 0 for text in reviews_df['review_text'])


class TestUtils:
    """Test utility functions."""
    
    def test_cosine_similarity(self):
        """Test cosine similarity calculation."""
        vec1 = [1, 0, 0]
        vec2 = [1, 0, 0]
        vec3 = [0, 1, 0]
        
        # Identical vectors
        assert abs(cosine_similarity(vec1, vec2) - 1.0) < 0.001
        
        # Orthogonal vectors
        assert abs(cosine_similarity(vec1, vec3)) < 0.001
        
        # Zero vector
        vec_zero = [0, 0, 0]
        assert cosine_similarity(vec1, vec_zero) == 0.0
    
    def test_calculate_sentiment_score(self):
        """Test sentiment scoring."""
        positive_text = "This is excellent and wonderful! Great quality, highly recommend!"
        negative_text = "Terrible product, waste of money. Very disappointed and would never buy again."
        neutral_text = "The item arrived on time."
        
        pos_score = calculate_sentiment_score(positive_text)
        neg_score = calculate_sentiment_score(negative_text)
        neu_score = calculate_sentiment_score(neutral_text)
        
        # Positive text should have positive score
        assert pos_score > 0
        
        # Negative text should have negative score
        assert neg_score < 0
        
        # Neutral text should be close to 0
        assert abs(neu_score) < 0.5
        
        # Scores should be in valid range
        assert -1.0 <= pos_score <= 1.0
        assert -1.0 <= neg_score <= 1.0
        assert -1.0 <= neu_score <= 1.0


class TestFallbackFunctions:
    """Test that fallback methods work without API."""
    
    def test_product_description_fallback(self):
        """Test fallback description generation."""
        from product_descriptions import generate_description_fallback
        
        product = {
            'product_id': 'P0001',
            'name': 'Modern Wood Coffee Table',
            'category': 'Living Room',
            'subcategory': 'Coffee Tables',
            'material': 'Wood',
            'style': 'Modern',
            'price': 199.99,
            'features': 'Dimensions: 48" W x 24" D x 18" H | Material: Wood | Weight: 45 lbs'
        }
        
        description = generate_description_fallback(product)
        
        assert len(description) > 100
        assert 'Modern' in description or 'modern' in description
        assert 'Wood' in description or 'wood' in description
    
    def test_sentiment_analysis_fallback(self):
        """Test fallback sentiment analysis."""
        from sentiment_analysis import analyze_reviews_fallback
        
        reviews = [
            {'rating': 5, 'review_text': 'Excellent quality! Love this product.'},
            {'rating': 4, 'review_text': 'Great value for the price.'},
            {'rating': 1, 'review_text': 'Terrible quality, broke immediately.'},
        ]
        
        analysis = analyze_reviews_fallback('Test Product', reviews)
        
        assert 'overall_sentiment' in analysis
        assert 'key_themes' in analysis
        assert 'summary' in analysis
        
        # Check sentiment percentages sum to ~100%
        sentiment = analysis['overall_sentiment']
        total = sentiment['positive'] + sentiment['negative'] + sentiment['neutral']
        assert abs(total - 100.0) < 1.0


class TestRecommendations:
    """Test recommendation engine."""
    
    def test_copurchase_matrix(self):
        """Test co-purchase matrix building."""
        from recommendations import build_copurchase_matrix
        
        orders_df = pd.DataFrame({
            'order_id': ['O1', 'O1', 'O2', 'O2', 'O3'],
            'product_id': ['P1', 'P2', 'P1', 'P3', 'P1']
        })
        
        matrix = build_copurchase_matrix(orders_df)
        
        # P1 and P2 were purchased together
        assert 'P1' in matrix
        assert 'P2' in matrix['P1']
        assert matrix['P1']['P2'] >= 1
        
        # Symmetric
        assert matrix['P2']['P1'] == matrix['P1']['P2']


class TestForecasting:
    """Test demand forecasting."""
    
    def test_moving_average_forecast(self):
        """Test simple moving average."""
        from demand_forecast import simple_moving_average_forecast
        
        data = pd.DataFrame({
            'quantity': [10, 12, 11, 13, 12]
        })
        
        forecast = simple_moving_average_forecast(data, periods=4)
        
        assert 'forecast' in forecast
        assert 'confidence_low' in forecast
        assert 'confidence_high' in forecast
        assert forecast['forecast'] > 0
        assert forecast['confidence_low'] <= forecast['forecast']
        assert forecast['forecast'] <= forecast['confidence_high']


def test_no_real_data():
    """Ensure no real data is present."""
    # Check that data files don't contain obvious real company names
    forbidden_terms = [
        'amazon', 'walmart', 'target', 'ikea', 'wayfair',
        'personal email', 'real address'
    ]
    
    data_dir = 'data'
    if os.path.exists(data_dir):
        for filename in os.listdir(data_dir):
            if filename.endswith('.csv'):
                filepath = os.path.join(data_dir, filename)
                with open(filepath, 'r') as f:
                    content = f.read().lower()
                    for term in forbidden_terms:
                        assert term not in content, f"Found forbidden term '{term}' in {filename}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
