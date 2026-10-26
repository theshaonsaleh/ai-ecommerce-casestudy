"""
AI-powered sentiment analysis and theme extraction from customer reviews.
All data is fictional for educational purposes only.
"""

import pandas as pd
import os
import json
from collections import Counter
from datetime import datetime
from utils import (
    Config, call_openai_chat, calculate_sentiment_score,
    ensure_dir, save_json, print_banner, print_section
)


def analyze_reviews_with_llm(product_name: str, reviews: list) -> dict:
    """Analyze reviews using LLM."""
    
    reviews_text = "\n\n".join([
        f"Rating: {r['rating']}/5\n{r['review_text']}"
        for r in reviews[:20]  # Limit to 20 reviews to stay within token limits
    ])
    
    prompt = f"""Analyze the following customer reviews for: {product_name}

Reviews:
{reviews_text}

Provide a structured analysis:

1. Overall Sentiment: Calculate the percentage breakdown (positive/negative/neutral)
2. Key Themes: Identify 3-5 main themes mentioned (e.g., quality, value, durability, design, shipping)
3. Specific Issues: List any specific problems or complaints mentioned
4. Positive Highlights: What customers love most
5. Actionable Summary: 2-3 sentence summary with recommendations

Format your response as JSON:
{{
  "overall_sentiment": {{"positive": X, "negative": Y, "neutral": Z}},
  "key_themes": [{{"theme": "quality", "mentions": N, "sentiment": "positive/negative/mixed", "keywords": ["sturdy", "well-made"]}}],
  "issues": ["issue 1", "issue 2"],
  "highlights": ["highlight 1", "highlight 2"],
  "summary": "actionable summary text",
  "recommendation": "recommended action"
}}"""

    response = call_openai_chat(
        prompt,
        system_message="You are an expert at analyzing customer feedback and extracting actionable insights.",
        temperature=0.3,
        max_tokens=800
    )
    
    if response:
        try:
            # Try to extract JSON from response
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end]
                return json.loads(json_str)
        except:
            pass
    
    return None


def analyze_reviews_fallback(product_name: str, reviews: list) -> dict:
    """Analyze reviews using simple keyword-based method (fallback)."""
    
    if not reviews:
        return {
            "overall_sentiment": {"positive": 0, "negative": 0, "neutral": 100},
            "key_themes": [],
            "issues": [],
            "highlights": [],
            "summary": "No reviews available.",
            "recommendation": "Gather customer feedback."
        }
    
    # Calculate sentiment from ratings
    ratings = [r['rating'] for r in reviews]
    positive = sum(1 for r in ratings if r >= 4) / len(ratings) * 100
    negative = sum(1 for r in ratings if r <= 2) / len(ratings) * 100
    neutral = sum(1 for r in ratings if r == 3) / len(ratings) * 100
    
    # Extract themes using keyword matching
    theme_keywords = {
        "quality": ["quality", "sturdy", "well-made", "durable", "construction", "craftsmanship"],
        "value": ["price", "worth", "value", "affordable", "expensive", "cheap"],
        "design": ["beautiful", "look", "style", "design", "aesthetic", "color"],
        "size": ["size", "large", "small", "dimension", "bigger", "smaller"],
        "shipping": ["shipping", "delivery", "arrived", "packaging", "damaged"],
        "assembly": ["assembly", "assemble", "install", "instructions", "setup"],
        "durability": ["broke", "broken", "lasted", "wear", "tear", "damage"]
    }
    
    all_text = " ".join([r['review_text'].lower() for r in reviews])
    
    themes = []
    for theme, keywords in theme_keywords.items():
        count = sum(all_text.count(keyword) for keyword in keywords)
        if count > 0:
            # Determine sentiment for this theme
            theme_reviews = [r for r in reviews if any(kw in r['review_text'].lower() for kw in keywords)]
            if theme_reviews:
                theme_ratings = [r['rating'] for r in theme_reviews]
                avg_rating = sum(theme_ratings) / len(theme_ratings)
                
                if avg_rating >= 4:
                    sentiment = "positive"
                elif avg_rating <= 2:
                    sentiment = "negative"
                else:
                    sentiment = "mixed"
                
                themes.append({
                    "theme": theme,
                    "mentions": count,
                    "sentiment": sentiment,
                    "keywords": keywords[:3]
                })
    
    # Sort themes by mentions
    themes.sort(key=lambda x: x['mentions'], reverse=True)
    themes = themes[:5]
    
    # Extract issues (from negative reviews)
    negative_reviews = [r for r in reviews if r['rating'] <= 2]
    issues = []
    if negative_reviews:
        issue_keywords = {
            "damaged": ["damaged", "broke", "broken"],
            "size": ["small", "smaller", "large", "larger"],
            "quality": ["cheap", "poor", "bad quality"],
            "shipping": ["late", "delayed", "damaged in shipping"]
        }
        
        for issue, keywords in issue_keywords.items():
            if any(any(kw in r['review_text'].lower() for kw in keywords) for r in negative_reviews):
                count = sum(1 for r in negative_reviews if any(kw in r['review_text'].lower() for kw in keywords))
                if count > 0:
                    issues.append(f"{issue.capitalize()} concerns ({count} mentions)")
    
    # Extract highlights (from positive reviews)
    positive_reviews = [r for r in reviews if r['rating'] >= 4]
    highlights = []
    if positive_reviews:
        highlight_keywords = {
            "Quality craftsmanship": ["quality", "well-made", "sturdy"],
            "Great value": ["worth", "value", "price"],
            "Beautiful design": ["beautiful", "look", "design"],
            "Easy assembly": ["easy", "simple", "assembly"]
        }
        
        for highlight, keywords in highlight_keywords.items():
            if any(any(kw in r['review_text'].lower() for kw in keywords) for r in positive_reviews):
                highlights.append(highlight)
    
    highlights = highlights[:3]
    
    # Generate summary
    avg_rating = sum(ratings) / len(ratings)
    
    if avg_rating >= 4.0:
        summary = f"Customers are highly satisfied with this {product_name}. "
        summary += f"Most reviews are positive ({positive:.0f}%). "
        if themes:
            summary += f"Key strengths include {themes[0]['theme']}. "
    elif avg_rating <= 2.5:
        summary = f"Customer satisfaction is low for this {product_name}. "
        summary += f"Significant negative feedback ({negative:.0f}%). "
        if issues:
            summary += f"Main concerns: {issues[0]}. "
    else:
        summary = f"Mixed customer feedback for this {product_name}. "
        summary += f"Average rating of {avg_rating:.1f}/5. "
    
    # Recommendation
    if avg_rating >= 4.0:
        recommendation = "Maintain quality standards and consider highlighting customer favorites in marketing."
    elif avg_rating <= 2.5:
        recommendation = "Address quality concerns urgently. Consider product improvements or better supplier sourcing."
    else:
        recommendation = "Investigate mixed feedback to identify specific improvement areas."
    
    return {
        "overall_sentiment": {
            "positive": round(positive, 1),
            "negative": round(negative, 1),
            "neutral": round(neutral, 1)
        },
        "key_themes": themes,
        "issues": issues[:3],
        "highlights": highlights,
        "summary": summary,
        "recommendation": recommendation
    }


def analyze_product_reviews(products_df: pd.DataFrame, reviews_df: pd.DataFrame, sample_size: int = 20):
    """Analyze reviews for sample products."""
    
    print_banner("Review Sentiment Analysis")
    
    if Config.has_openai_key():
        print("✓ OpenAI API detected - using GPT-4 for analysis")
    else:
        print("⚠ No OpenAI API key - using keyword-based fallback")
        print("  (Still produces useful insights!)")
    
    # Get products with multiple reviews
    review_counts = reviews_df.groupby('product_id').size()
    products_with_reviews = review_counts[review_counts >= 3].index.tolist()
    
    # Sample products
    sample_products = products_df[products_df['product_id'].isin(products_with_reviews)].sample(
        n=min(sample_size, len(products_with_reviews)),
        random_state=42
    )
    
    print(f"\nAnalyzing reviews for {len(sample_products)} products...")
    
    results = []
    llm_success = 0
    fallback_used = 0
    
    for idx, (_, product) in enumerate(sample_products.iterrows(), 1):
        product_reviews = reviews_df[reviews_df['product_id'] == product['product_id']]
        
        reviews_list = product_reviews.to_dict('records')
        
        # Try LLM first
        analysis = analyze_reviews_with_llm(product['name'], reviews_list)
        
        if analysis:
            method = "LLM"
            llm_success += 1
        else:
            analysis = analyze_reviews_fallback(product['name'], reviews_list)
            method = "Keyword"
            fallback_used += 1
        
        result = {
            "product_id": product['product_id'],
            "product_name": product['name'],
            "category": product['category'],
            "review_count": len(reviews_list),
            "average_rating": float(product_reviews['rating'].mean()),
            "analysis": analysis,
            "method": method,
            "analyzed_at": datetime.now().isoformat()
        }
        
        results.append(result)
        
        if idx % 5 == 0:
            print(f"  Progress: {idx}/{len(sample_products)} products analyzed")
    
    print(f"\n✓ Analyzed {len(results)} products")
    print(f"  - LLM analysis: {llm_success}")
    print(f"  - Keyword analysis: {fallback_used}")
    
    return results


def save_results(results: list):
    """Save sentiment analysis results."""
    output_dir = "outputs/sentiment"
    ensure_dir(output_dir)
    
    # Save full results
    save_json(results, f"{output_dir}/sentiment_analysis.json")
    print(f"\n✓ Saved results to {output_dir}/sentiment_analysis.json")
    
    # Save summary CSV
    summary_data = []
    for r in results:
        summary_data.append({
            "product_id": r['product_id'],
            "product_name": r['product_name'],
            "review_count": r['review_count'],
            "average_rating": r['average_rating'],
            "positive_pct": r['analysis']['overall_sentiment']['positive'],
            "negative_pct": r['analysis']['overall_sentiment']['negative'],
            "neutral_pct": r['analysis']['overall_sentiment']['neutral'],
            "method": r['method']
        })
    
    df = pd.DataFrame(summary_data)
    df.to_csv(f"{output_dir}/sentiment_summary.csv", index=False)
    print(f"✓ Saved summary to {output_dir}/sentiment_summary.csv")
    
    return df


def print_examples(results: list, n: int = 3):
    """Print example analyses."""
    print_section("Example Sentiment Analyses")
    
    import random
    samples = random.sample(results, min(n, len(results)))
    
    for i, result in enumerate(samples, 1):
        print(f"\nExample {i}:")
        print(f"Product: {result['product_name']}")
        print(f"Category: {result['category']}")
        print(f"Reviews: {result['review_count']}")
        print(f"Average Rating: {result['average_rating']:.2f}/5.0")
        print(f"Method: {result['method']}")
        
        analysis = result['analysis']
        
        print(f"\nOverall Sentiment:")
        print(f"  Positive: {analysis['overall_sentiment']['positive']:.1f}%")
        print(f"  Negative: {analysis['overall_sentiment']['negative']:.1f}%")
        print(f"  Neutral: {analysis['overall_sentiment']['neutral']:.1f}%")
        
        if analysis['key_themes']:
            print(f"\nKey Themes:")
            for theme in analysis['key_themes'][:3]:
                print(f"  • {theme['theme'].capitalize()}: {theme['mentions']} mentions ({theme['sentiment']})")
        
        if analysis['issues']:
            print(f"\nIssues Identified:")
            for issue in analysis['issues']:
                print(f"  • {issue}")
        
        if analysis['highlights']:
            print(f"\nPositive Highlights:")
            for highlight in analysis['highlights']:
                print(f"  • {highlight}")
        
        print(f"\nSummary: {analysis['summary']}")
        print(f"Recommendation: {analysis['recommendation']}")
        print("-" * 60)


def analyze_overall_trends(results: list):
    """Analyze trends across all products."""
    print_section("Overall Trends")
    
    total_reviews = sum(r['review_count'] for r in results)
    avg_rating = sum(r['average_rating'] * r['review_count'] for r in results) / total_reviews
    
    print(f"Total products analyzed: {len(results)}")
    print(f"Total reviews: {total_reviews}")
    print(f"Overall average rating: {avg_rating:.2f}/5.0")
    
    # Sentiment breakdown
    avg_positive = sum(r['analysis']['overall_sentiment']['positive'] for r in results) / len(results)
    avg_negative = sum(r['analysis']['overall_sentiment']['negative'] for r in results) / len(results)
    avg_neutral = sum(r['analysis']['overall_sentiment']['neutral'] for r in results) / len(results)
    
    print(f"\nAverage sentiment distribution:")
    print(f"  Positive: {avg_positive:.1f}%")
    print(f"  Negative: {avg_negative:.1f}%")
    print(f"  Neutral: {avg_neutral:.1f}%")
    
    # Most common themes
    all_themes = []
    for r in results:
        for theme in r['analysis']['key_themes']:
            all_themes.append(theme['theme'])
    
    if all_themes:
        theme_counts = Counter(all_themes)
        print(f"\nMost common themes across products:")
        for theme, count in theme_counts.most_common(5):
            print(f"  {theme.capitalize()}: {count} products")


def main():
    """Main execution function."""
    
    # Load data
    if not os.path.exists("data/products.csv") or not os.path.exists("data/reviews.csv"):
        print("Error: Data files not found. Run data_generator.py first.")
        return
    
    products_df = pd.read_csv("data/products.csv")
    reviews_df = pd.read_csv("data/reviews.csv")
    
    # Analyze reviews
    results = analyze_product_reviews(products_df, reviews_df, sample_size=20)
    
    # Save results
    summary_df = save_results(results)
    
    # Print examples
    print_examples(results, n=3)
    
    # Analyze trends
    analyze_overall_trends(results)
    
    print("\n" + "=" * 60)
    print("  Sentiment analysis complete!")
    print("=" * 60)
    print("\nKey Benefits Demonstrated:")
    print("  ✓ Automated theme extraction")
    print("  ✓ Actionable insights from reviews")
    print("  ✓ Trend identification across products")
    print("  ✓ Fallback ensures always functional")
    print("\nReminder: All reviews and products are fictional")


if __name__ == "__main__":
    main()
