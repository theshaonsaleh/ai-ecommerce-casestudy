"""
Generate synthetic e-commerce data for AI demonstrations.
All data is completely fictional for educational purposes only.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from faker import Faker
import random
import os

fake = Faker()
Faker.seed(42)
random.seed(42)
np.random.seed(42)


# Product categories and attributes
CATEGORIES = {
    "Living Room": ["Sofas", "Coffee Tables", "Floor Lamps", "Area Rugs", "Wall Art", "Throw Pillows"],
    "Bedroom": ["Bed Frames", "Nightstands", "Dressers", "Table Lamps", "Bedding Sets", "Curtains"],
    "Kitchen": ["Cookware Sets", "Cutting Boards", "Utensil Sets", "Storage Containers", "Dish Racks"],
    "Dining": ["Dining Tables", "Dining Chairs", "Tableware Sets", "Placemats", "Candle Holders"],
    "Outdoor": ["Patio Furniture", "Planters", "Garden Lights", "Outdoor Cushions", "Fire Pits"],
    "Decor": ["Vases", "Picture Frames", "Decorative Bowls", "Sculptures", "Mirrors"],
}

MATERIALS = ["Wood", "Metal", "Glass", "Ceramic", "Cotton", "Linen", "Bamboo", "Stainless Steel", "Plastic", "Rattan"]

ADJECTIVES = ["Modern", "Rustic", "Contemporary", "Vintage", "Minimalist", "Classic", "Industrial", "Scandinavian", "Bohemian", "Traditional"]

REVIEW_TEMPLATES_POSITIVE = [
    "Love this {product}! {positive_aspect}. {recommendation}",
    "Excellent quality. {positive_aspect}. Very happy with my purchase.",
    "{positive_aspect}. Looks exactly as pictured. {recommendation}",
    "Great {product}! {positive_aspect}. Worth every penny.",
    "Perfect addition to my {room}. {positive_aspect}. Highly satisfied."
]

REVIEW_TEMPLATES_NEGATIVE = [
    "Disappointed with this {product}. {negative_aspect}. {complaint}",
    "Not what I expected. {negative_aspect}. Returning it.",
    "{negative_aspect}. Quality is not great for the price.",
    "Had issues with this {product}. {negative_aspect}. Customer service was unhelpful.",
    "Would not recommend. {negative_aspect}. {complaint}"
]

REVIEW_TEMPLATES_NEUTRAL = [
    "It's okay. {neutral_aspect}. Does the job.",
    "Decent {product}. {neutral_aspect}. Nothing special but functional.",
    "{neutral_aspect}. Average quality for the price.",
    "Mixed feelings. {neutral_aspect}. Could be better."
]

POSITIVE_ASPECTS = [
    "Beautiful design and sturdy construction",
    "Exactly what I was looking for",
    "Great quality and fast shipping",
    "Easy to assemble and looks fantastic",
    "Perfect size and color",
    "Exceeded my expectations",
    "Very well made and durable",
    "Love the modern look"
]

NEGATIVE_ASPECTS = [
    "Arrived damaged",
    "Smaller than expected",
    "Poor quality materials",
    "Difficult to assemble",
    "Color doesn't match the photo",
    "Broke after a few weeks",
    "Not worth the price",
    "Cheap feeling"
]

NEUTRAL_ASPECTS = [
    "Good for the price",
    "Works as described",
    "Nothing fancy but functional",
    "Average quality",
    "Takes some time to assemble"
]

RECOMMENDATIONS = [
    "Would definitely recommend!",
    "Will be buying more from this store",
    "5 stars!",
    "Highly recommend to anyone looking for quality"
]

COMPLAINTS = [
    "Would not buy again",
    "Waste of money",
    "Expected better quality",
    "Very disappointed"
]


def generate_products(n=500):
    """Generate fictional product catalog."""
    products = []
    product_id = 1
    
    for main_category, subcategories in CATEGORIES.items():
        for subcategory in subcategories:
            # Generate multiple products per subcategory
            num_products = random.randint(5, 15)
            
            for _ in range(num_products):
                adjective = random.choice(ADJECTIVES)
                material = random.choice(MATERIALS)
                
                name = f"{adjective} {material} {subcategory}"
                if random.random() < 0.3:
                    name = f"{subcategory} ({material})"
                
                price = round(random.uniform(15, 500), 2)
                stock = random.randint(0, 200)
                
                # Create feature list
                features = []
                if "Table" in subcategory or "Sofa" in subcategory or "Chair" in subcategory:
                    features.append(f"Dimensions: {random.randint(20, 80)}\" W x {random.randint(20, 40)}\" D x {random.randint(20, 40)}\" H")
                
                features.append(f"Material: {material}")
                features.append(f"Weight: {random.randint(5, 100)} lbs")
                
                if random.random() < 0.5:
                    features.append("Easy assembly required")
                else:
                    features.append("Fully assembled")
                
                if random.random() < 0.3:
                    features.append("Limited edition")
                
                products.append({
                    "product_id": f"P{product_id:04d}",
                    "name": name,
                    "category": main_category,
                    "subcategory": subcategory,
                    "price": price,
                    "material": material,
                    "style": adjective,
                    "stock": stock,
                    "features": " | ".join(features),
                    "created_date": fake.date_between(start_date="-2y", end_date="today")
                })
                
                product_id += 1
                
                if product_id > n:
                    return pd.DataFrame(products)
    
    return pd.DataFrame(products)


def generate_customers(n=1000):
    """Generate fictional customer profiles."""
    customers = []
    
    for i in range(1, n + 1):
        # Generate completely fictional names
        first_name = fake.first_name()
        last_name = fake.last_name()
        
        customers.append({
            "customer_id": f"C{i:05d}",
            "first_name": first_name,
            "last_name": last_name,
            "email": f"{first_name.lower()}.{last_name.lower()}{random.randint(1, 999)}@example.com",
            "signup_date": fake.date_between(start_date="-3y", end_date="today"),
            "country": "US",
            "state": fake.state_abbr(),
            "city": fake.city()
        })
    
    return pd.DataFrame(customers)


def generate_orders(customers_df, products_df, n=5000):
    """Generate fictional order history."""
    orders = []
    order_id = 1
    
    # Some customers are more active than others (Pareto distribution)
    customer_weights = np.random.pareto(2, len(customers_df))
    customer_weights = customer_weights / customer_weights.sum()
    
    for _ in range(n):
        customer_idx = np.random.choice(len(customers_df), p=customer_weights)
        customer = customers_df.iloc[customer_idx]
        
        # Order date after customer signup
        signup_date = pd.to_datetime(customer["signup_date"])
        order_date = fake.date_between(
            start_date=signup_date,
            end_date="today"
        )
        
        # Random number of items (1-5, weighted toward 1-2)
        num_items = random.choices([1, 2, 3, 4, 5], weights=[40, 30, 15, 10, 5])[0]
        
        selected_products = products_df.sample(n=num_items)
        
        for _, product in selected_products.iterrows():
            quantity = random.choices([1, 2, 3], weights=[70, 25, 5])[0]
            
            orders.append({
                "order_id": f"O{order_id:06d}",
                "customer_id": customer["customer_id"],
                "product_id": product["product_id"],
                "order_date": order_date,
                "quantity": quantity,
                "unit_price": product["price"],
                "total_price": round(product["price"] * quantity, 2)
            })
            
            order_id += 1
    
    return pd.DataFrame(orders)


def generate_reviews(orders_df, products_df, customers_df, n=2000):
    """Generate fictional customer reviews."""
    reviews = []
    
    # Sample orders that could have reviews (not too recent)
    recent_date = datetime.now() - timedelta(days=7)
    eligible_orders = orders_df[pd.to_datetime(orders_df["order_date"]) < recent_date]
    
    if len(eligible_orders) < n:
        n = len(eligible_orders)
    
    sampled_orders = eligible_orders.sample(n=n, replace=False)
    
    for idx, order in sampled_orders.iterrows():
        product = products_df[products_df["product_id"] == order["product_id"]].iloc[0]
        customer = customers_df[customers_df["customer_id"] == order["customer_id"]].iloc[0]
        
        # Determine sentiment (weighted toward positive)
        sentiment_type = random.choices(
            ["positive", "negative", "neutral"],
            weights=[60, 25, 15]
        )[0]
        
        if sentiment_type == "positive":
            template = random.choice(REVIEW_TEMPLATES_POSITIVE)
            rating = random.choices([4, 5], weights=[30, 70])[0]
            text = template.format(
                product=product["subcategory"].lower(),
                positive_aspect=random.choice(POSITIVE_ASPECTS),
                recommendation=random.choice(RECOMMENDATIONS),
                room=product["category"].lower()
            )
        elif sentiment_type == "negative":
            template = random.choice(REVIEW_TEMPLATES_NEGATIVE)
            rating = random.choices([1, 2], weights=[60, 40])[0]
            text = template.format(
                product=product["subcategory"].lower(),
                negative_aspect=random.choice(NEGATIVE_ASPECTS),
                complaint=random.choice(COMPLAINTS)
            )
        else:
            template = random.choice(REVIEW_TEMPLATES_NEUTRAL)
            rating = 3
            text = template.format(
                product=product["subcategory"].lower(),
                neutral_aspect=random.choice(NEUTRAL_ASPECTS)
            )
        
        review_date = order["order_date"] + timedelta(days=random.randint(3, 30))
        
        reviews.append({
            "review_id": f"R{len(reviews) + 1:05d}",
            "product_id": product["product_id"],
            "customer_id": customer["customer_id"],
            "order_id": order["order_id"],
            "rating": rating,
            "review_text": text,
            "review_date": review_date,
            "verified_purchase": True
        })
    
    return pd.DataFrame(reviews)


def main():
    """Generate all synthetic data files."""
    print("=" * 60)
    print("  Generating Fictional E-Commerce Data")
    print("  Personal learning project - all data is fictional")
    print("=" * 60)
    
    # Create data directory
    os.makedirs("data", exist_ok=True)
    
    print("\n1. Generating products...")
    products_df = generate_products(n=500)
    products_df.to_csv("data/products.csv", index=False)
    print(f"   ✓ Created {len(products_df)} fictional products")
    
    print("\n2. Generating customers...")
    customers_df = generate_customers(n=1000)
    customers_df.to_csv("data/customers.csv", index=False)
    print(f"   ✓ Created {len(customers_df)} fictional customers")
    
    print("\n3. Generating orders...")
    orders_df = generate_orders(customers_df, products_df, n=5000)
    orders_df.to_csv("data/orders.csv", index=False)
    print(f"   ✓ Created {len(orders_df)} fictional orders")
    
    print("\n4. Generating reviews...")
    reviews_df = generate_reviews(orders_df, products_df, customers_df, n=2000)
    reviews_df.to_csv("data/reviews.csv", index=False)
    print(f"   ✓ Created {len(reviews_df)} fictional reviews")
    
    print("\n" + "=" * 60)
    print("  Data Generation Complete!")
    print("=" * 60)
    
    # Print summary statistics
    print("\nDataset Summary:")
    print(f"  Products: {len(products_df)}")
    print(f"  Customers: {len(customers_df)}")
    print(f"  Orders: {len(orders_df)}")
    print(f"  Reviews: {len(reviews_df)}")
    print(f"  Categories: {len(CATEGORIES)}")
    print(f"  Date range: {orders_df['order_date'].min()} to {orders_df['order_date'].max()}")
    print(f"  Total revenue: ${orders_df['total_price'].sum():,.2f} (fictional)")
    print(f"  Avg order value: ${orders_df.groupby('order_id')['total_price'].sum().mean():,.2f}")
    print(f"  Avg rating: {reviews_df['rating'].mean():.2f}/5.0")
    
    print("\n✓ All data saved to data/ directory")
    print("\nReminder: All data is completely fictional and for educational purposes only.")


if __name__ == "__main__":
    main()
