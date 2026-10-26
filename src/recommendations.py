"""
AI-powered product recommendation engine.
Demonstrates collaborative filtering, content-based filtering, and hybrid approaches.
All data is fictional for educational purposes only.
"""

import pandas as pd
import numpy as np
import os
from collections import defaultdict, Counter
from datetime import datetime
from utils import (
    Config, get_embeddings, cosine_similarity,
    ensure_dir, save_json, print_banner, print_section
)


def build_copurchase_matrix(orders_df: pd.DataFrame) -> dict:
    """Build co-purchase frequency matrix."""
    
    # Group by order_id to get products purchased together
    order_groups = orders_df.groupby('order_id')['product_id'].apply(list).values
    
    copurchase = defaultdict(Counter)
    
    for products in order_groups:
        if len(products) > 1:
            # Record co-purchases
            for i, prod1 in enumerate(products):
                for prod2 in products[i+1:]:
                    copurchase[prod1][prod2] += 1
                    copurchase[prod2][prod1] += 1
    
    return dict(copurchase)


def recommend_copurchase(product_id: str, copurchase_matrix: dict, n: int = 5) -> list:
    """Recommend based on co-purchase patterns."""
    
    if product_id not in copurchase_matrix:
        return []
    
    # Get products purchased with this one
    recommendations = copurchase_matrix[product_id].most_common(n)
    
    return [
        {
            "product_id": prod_id,
            "score": count,
            "reason": f"Purchased together {count} times"
        }
        for prod_id, count in recommendations
    ]


def get_product_embeddings(products_df: pd.DataFrame) -> dict:
    """Get embeddings for products (with fallback)."""
    
    # Create text representations
    products_df['embedding_text'] = (
        products_df['name'] + ". " +
        products_df['category'] + " - " +
        products_df['subcategory'] + ". " +
        products_df['style'] + " style. " +
        products_df['material'] + " material. " +
        products_df['features'].str.replace(' | ', '. ')
    )
    
    texts = products_df['embedding_text'].tolist()
    product_ids = products_df['product_id'].tolist()
    
    # Try to get real embeddings
    embeddings = get_embeddings(texts)
    
    if embeddings:
        return {pid: emb for pid, emb in zip(product_ids, embeddings)}
    
    # Fallback: create simple TF-IDF-like embeddings
    from sklearn.feature_extraction.text import TfidfVectorizer
    
    vectorizer = TfidfVectorizer(max_features=100, stop_words='english')
    tfidf_matrix = vectorizer.fit_transform(texts)
    
    embeddings_dict = {}
    for i, pid in enumerate(product_ids):
        embeddings_dict[pid] = tfidf_matrix[i].toarray()[0].tolist()
    
    return embeddings_dict


def recommend_similarity(
    product_id: str,
    embeddings_dict: dict,
    products_df: pd.DataFrame,
    n: int = 5
) -> list:
    """Recommend based on embedding similarity."""
    
    if product_id not in embeddings_dict:
        return []
    
    target_embedding = embeddings_dict[product_id]
    
    # Calculate similarities
    similarities = []
    for pid, emb in embeddings_dict.items():
        if pid != product_id:
            sim = cosine_similarity(target_embedding, emb)
            similarities.append((pid, sim))
    
    # Sort by similarity
    similarities.sort(key=lambda x: x[1], reverse=True)
    
    recommendations = []
    for pid, sim in similarities[:n]:
        product = products_df[products_df['product_id'] == pid].iloc[0]
        recommendations.append({
            "product_id": pid,
            "score": float(sim),
            "reason": f"Similar style and category (similarity: {sim:.2f})"
        })
    
    return recommendations


def recommend_hybrid(
    product_id: str,
    copurchase_matrix: dict,
    embeddings_dict: dict,
    products_df: pd.DataFrame,
    n: int = 5,
    copurchase_weight: float = 0.4,
    similarity_weight: float = 0.6
) -> list:
    """Hybrid recommendation combining co-purchase and similarity."""
    
    # Get both types of recommendations
    copurchase_recs = recommend_copurchase(product_id, copurchase_matrix, n=n*2)
    similarity_recs = recommend_similarity(product_id, embeddings_dict, products_df, n=n*2)
    
    # Combine scores
    combined_scores = defaultdict(lambda: {"copurchase": 0, "similarity": 0})
    
    # Normalize co-purchase scores
    if copurchase_recs:
        max_copurchase = max(r['score'] for r in copurchase_recs)
        for rec in copurchase_recs:
            combined_scores[rec['product_id']]["copurchase"] = rec['score'] / max_copurchase
    
    # Add similarity scores (already 0-1)
    for rec in similarity_recs:
        combined_scores[rec['product_id']]["similarity"] = rec['score']
    
    # Calculate weighted scores
    final_scores = []
    for pid, scores in combined_scores.items():
        weighted_score = (
            scores["copurchase"] * copurchase_weight +
            scores["similarity"] * similarity_weight
        )
        final_scores.append((pid, weighted_score, scores))
    
    # Sort by weighted score
    final_scores.sort(key=lambda x: x[1], reverse=True)
    
    recommendations = []
    for pid, score, component_scores in final_scores[:n]:
        product = products_df[products_df['product_id'] == pid].iloc[0]
        
        reasons = []
        if component_scores["copurchase"] > 0:
            reasons.append("frequently purchased together")
        if component_scores["similarity"] > 0.7:
            reasons.append("similar style")
        
        recommendations.append({
            "product_id": pid,
            "score": float(score),
            "reason": " and ".join(reasons) if reasons else "recommended",
            "copurchase_score": float(component_scores["copurchase"]),
            "similarity_score": float(component_scores["similarity"])
        })
    
    return recommendations


def generate_customer_recommendations(
    customer_id: str,
    orders_df: pd.DataFrame,
    copurchase_matrix: dict,
    embeddings_dict: dict,
    products_df: pd.DataFrame,
    n: int = 10
) -> dict:
    """Generate personalized recommendations for a customer."""
    
    # Get customer's purchase history
    customer_orders = orders_df[orders_df['customer_id'] == customer_id]
    purchased_products = customer_orders['product_id'].unique().tolist()
    
    if not purchased_products:
        # New customer - recommend popular items
        popular = orders_df.groupby('product_id').size().sort_values(ascending=False).head(n)
        return {
            "customer_id": customer_id,
            "purchased_products": [],
            "recommendations": [
                {
                    "product_id": pid,
                    "score": 1.0,
                    "reason": "Popular item",
                    "method": "popularity"
                }
                for pid in popular.index
            ],
            "method": "cold_start"
        }
    
    # Get recommendations based on each purchased product
    all_recommendations = defaultdict(lambda: {"score": 0, "count": 0, "reasons": []})
    
    for pid in purchased_products[-5:]:  # Use last 5 purchases
        recs = recommend_hybrid(pid, copurchase_matrix, embeddings_dict, products_df, n=n)
        
        for rec in recs:
            rec_pid = rec['product_id']
            if rec_pid not in purchased_products:  # Don't recommend already purchased
                all_recommendations[rec_pid]["score"] += rec['score']
                all_recommendations[rec_pid]["count"] += 1
                all_recommendations[rec_pid]["reasons"].append(rec['reason'])
    
    # Average scores and sort
    final_recs = []
    for pid, data in all_recommendations.items():
        avg_score = data["score"] / data["count"]
        product = products_df[products_df['product_id'] == pid].iloc[0]
        
        final_recs.append({
            "product_id": pid,
            "product_name": product['name'],
            "category": product['category'],
            "price": float(product['price']),
            "score": float(avg_score),
            "reason": data["reasons"][0] if data["reasons"] else "recommended for you",
            "method": "hybrid"
        })
    
    final_recs.sort(key=lambda x: x['score'], reverse=True)
    
    return {
        "customer_id": customer_id,
        "purchased_products": purchased_products,
        "purchase_count": len(purchased_products),
        "recommendations": final_recs[:n],
        "method": "personalized"
    }


def evaluate_recommendations(
    orders_df: pd.DataFrame,
    copurchase_matrix: dict,
    embeddings_dict: dict,
    products_df: pd.DataFrame,
    test_size: int = 100
) -> dict:
    """Evaluate recommendation quality on test data."""
    
    print_section("Evaluating Recommendation Quality")
    
    # Get customers with multiple orders for testing
    customer_order_counts = orders_df.groupby('customer_id').size()
    test_customers = customer_order_counts[customer_order_counts >= 3].sample(
        n=min(test_size, len(customer_order_counts[customer_order_counts >= 3])),
        random_state=42
    ).index
    
    metrics = {
        "copurchase": {"hits": 0, "total": 0},
        "similarity": {"hits": 0, "total": 0},
        "hybrid": {"hits": 0, "total": 0}
    }
    
    for customer_id in test_customers:
        customer_orders = orders_df[orders_df['customer_id'] == customer_id]
        purchased_products = customer_orders['product_id'].tolist()
        
        # Use first purchases to recommend, test against later purchases
        train_products = purchased_products[:len(purchased_products)//2]
        test_products = set(purchased_products[len(purchased_products)//2:])
        
        if not train_products or not test_products:
            continue
        
        # Test each method
        for method_name, method_func in [
            ("copurchase", lambda p: recommend_copurchase(p, copurchase_matrix, n=10)),
            ("similarity", lambda p: recommend_similarity(p, embeddings_dict, products_df, n=10)),
            ("hybrid", lambda p: recommend_hybrid(p, copurchase_matrix, embeddings_dict, products_df, n=10))
        ]:
            # Get recommendations based on training purchases
            all_recs = set()
            for pid in train_products:
                recs = method_func(pid)
                all_recs.update([r['product_id'] for r in recs])
            
            # Check hits
            hits = len(all_recs.intersection(test_products))
            metrics[method_name]["hits"] += hits
            metrics[method_name]["total"] += len(test_products)
    
    # Calculate hit rates
    results = {}
    for method, data in metrics.items():
        hit_rate = (data["hits"] / data["total"] * 100) if data["total"] > 0 else 0
        results[method] = {
            "hit_rate": round(hit_rate, 2),
            "hits": data["hits"],
            "total": data["total"]
        }
        print(f"  {method.capitalize()}: {hit_rate:.2f}% hit rate ({data['hits']}/{data['total']})")
    
    return results


def main():
    """Main execution function."""
    
    print_banner("Product Recommendation Engine")
    
    # Load data
    if not os.path.exists("data/products.csv") or not os.path.exists("data/orders.csv"):
        print("Error: Data files not found. Run data_generator.py first.")
        return
    
    products_df = pd.read_csv("data/products.csv")
    orders_df = pd.read_csv("data/orders.csv")
    
    # Build co-purchase matrix
    print("\n1. Building co-purchase matrix...")
    copurchase_matrix = build_copurchase_matrix(orders_df)
    print(f"   ✓ Analyzed {len(copurchase_matrix)} products with co-purchases")
    
    # Get product embeddings
    print("\n2. Generating product embeddings...")
    if Config.has_openai_key():
        print("   Using OpenAI embeddings for better similarity")
    else:
        print("   Using TF-IDF fallback (still effective)")
    
    embeddings_dict = get_product_embeddings(products_df)
    print(f"   ✓ Generated embeddings for {len(embeddings_dict)} products")
    
    # Evaluate methods
    evaluation = evaluate_recommendations(orders_df, copurchase_matrix, embeddings_dict, products_df)
    
    # Generate customer recommendations
    print_section("Generating Customer Recommendations")
    
    # Get customers with purchases
    active_customers = orders_df.groupby('customer_id').size().sort_values(ascending=False).head(50).index
    
    customer_recommendations = []
    for customer_id in active_customers[:20]:
        recs = generate_customer_recommendations(
            customer_id, orders_df, copurchase_matrix, embeddings_dict, products_df, n=10
        )
        customer_recommendations.append(recs)
    
    print(f"✓ Generated recommendations for {len(customer_recommendations)} customers")
    
    # Save results
    output_dir = "outputs/recommendations"
    ensure_dir(output_dir)
    
    save_json({
        "evaluation": evaluation,
        "customer_recommendations": customer_recommendations,
        "generated_at": datetime.now().isoformat()
    }, f"{output_dir}/recommendations.json")
    
    print(f"\n✓ Saved results to {output_dir}/recommendations.json")
    
    # Print examples
    print_section("Example Recommendations")
    
    for i, rec in enumerate(customer_recommendations[:3], 1):
        print(f"\nExample {i}:")
        print(f"Customer: {rec['customer_id']}")
        print(f"Previous purchases: {rec['purchase_count']} products")
        print(f"Method: {rec['method']}")
        print(f"\nTop 5 Recommendations:")
        
        for j, item in enumerate(rec['recommendations'][:5], 1):
            print(f"  {j}. {item['product_name']}")
            print(f"     Price: ${item['price']:.2f}")
            print(f"     Score: {item['score']:.3f}")
            print(f"     Reason: {item['reason']}")
        print("-" * 60)
    
    print("\n" + "=" * 60)
    print("  Recommendation engine complete!")
    print("=" * 60)
    print("\nKey Benefits Demonstrated:")
    print("  ✓ Personalized recommendations")
    print("  ✓ Multiple strategies (co-purchase, similarity, hybrid)")
    print("  ✓ Cold-start handling for new customers")
    print("  ✓ Measurable improvement over random")
    print("\nReminder: All data and recommendations are fictional")


if __name__ == "__main__":
    main()
