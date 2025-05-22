import os
import django
from collections import defaultdict

# Django setup (if running standalone script)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'yourproject.settings')
django.setup()

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel
from surprise import Dataset, Reader, SVD

from shop.models import Product, Review
from orders.models import OrderItem


def get_product_dataframe():
    """
    Ստեղծում է DataFrame ապրանքներից՝ ներառելով թե tag-երը, թե հիմնական դաշտերը
    """
    products = []
    for prod in Product.objects.filter(status=Product.Status.PUBLISHED, available=True):
        tags = prod.tags.names() if hasattr(prod, 'tags') else []
        tag_str = " ".join(tags)
        products.append({
            'product_id': prod.id,
            'name': prod.name,
            'tags': tag_str,
        })
    return pd.DataFrame(products)


def get_review_dataframe():
    """
    DataFrame ակնարկներից՝ user_id, product_id, rating
    """
    reviews = list(
        Review.objects.filter(status=Review.Status.APPROVED)
               .values('user_id', 'product_id', 'rating')
    )
    return pd.DataFrame(reviews)


def get_order_dataframe():
    """
    DataFrame պատվերների համար՝ յուրաքանչյուր row – order_item-ից
    """
    items = OrderItem.objects.values('order__user_id', 'product_id')
    # Անդրանում ենք որպեսզի user_id լինի ճիշտ դաշտի անունով
    df = pd.DataFrame.from_records(items)
    return df.rename(columns={'order__user_id': 'user_id'})


def hybrid_recommendation(user_id, top_n=5):
    """
    Հիբրիդ առաջարկության ֆունկցիա՝ օգտագործելով Content-Based, Collaborative և Popular մոտեցումներ
    """
    # Ստանում ենք DataFrame-ները
    product_df = get_product_dataframe()
    review_df = get_review_dataframe()
    order_df = get_order_dataframe()

    if product_df.empty:
        return Product.objects.none()

    # --- Content-based filtering ---
    tfidf = TfidfVectorizer(stop_words='english')
    tfidf_matrix = tfidf.fit_transform(product_df['tags'].fillna(''))
    cosine_sim = linear_kernel(tfidf_matrix, tfidf_matrix)

    purchased = order_df[order_df['user_id'] == user_id]['product_id'].tolist()
    content_scores = defaultdict(float)
    for pid in purchased:
        if pid in product_df['product_id'].values:
            idx = product_df.index[product_df['product_id'] == pid][0]
            for i, score in enumerate(cosine_sim[idx]):
                content_scores[product_df.at[i, 'product_id']] += score
    content_recs = [pid for pid, _ in sorted(content_scores.items(), key=lambda x: x[1], reverse=True)
                    if pid not in purchased][:top_n]

    # --- Collaborative filtering (SVD) ---
    if not review_df.empty:
        reader = Reader(rating_scale=(1, 5))
        data = Dataset.load_from_df(review_df[['user_id', 'product_id', 'rating']], reader)
        trainset = data.build_full_trainset()
        model = SVD()
        model.fit(trainset)

        all_pids = product_df['product_id'].tolist()
        reviewed = review_df[review_df['user_id'] == user_id]['product_id'].tolist()
        collab_scores = []
        for pid in all_pids:
            if pid not in reviewed:
                est = model.predict(user_id, pid).est
                collab_scores.append((pid, est))
        collab_recs = [pid for pid, _ in sorted(collab_scores, key=lambda x: x[1], reverse=True)][:top_n]
    else:
        collab_recs = []

    # --- Popular products ---
    pop_counts = order_df['product_id'].value_counts().head(top_n)
    popular_recs = pop_counts.index.tolist()

    # --- Միավորում և Unique ---
    combined = content_recs + collab_recs + popular_recs
    unique = list(dict.fromkeys(combined))[:top_n]

    return Product.objects.filter(id__in=unique)
