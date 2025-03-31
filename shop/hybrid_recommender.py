# import redis
# import numpy as np
# import pandas as pd
# from django.conf import settings
# from sklearn.feature_extraction.text import TfidfVectorizer
# from sklearn.metrics.pairwise import cosine_similarity
# from surprise import SVD, Dataset, Reader
# from surprise.model_selection import train_test_split
# from surprise import accuracy
# from cart.models import CartItem
# from .models import Product, Review
#
#
#
#
# # Content-based filtering. TF-IDF vectorizer & Cosine Similarity
# def get_similar_products(product_id, top_n=5):
#     products = Product.objects.all()
#     product_description = [product.description for product in products]
#
#     vectorizer = TfidfVectorizer(stop_words='english')
#     tfidf_matrix = vectorizer.fit_transform(product_description)
#     cosine_sim = cosine_similarity(tfidf_matrix, tfidf_matrix)
#
#     idx = products.get(id=product_id).id
#     sim_scores = list(enumerate(cosine_sim[idx]))
#     sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
#     product_indices = [i[0] for i in sim_scores]
#
#     return [products[i] for i in product_indices[:top_n]]
#
#
# # Collaborative filtering using Surprise SVD
# def get_collaborative_recommendations(user_id, top_n=5):
#     user_ratings = []  # [user_id, product_id, rating]
#
#     for review in Review.objects.all():
#         user_ratings.append([review.user.id, review.product.id, review.rating])
#
#     reader = Reader(rating_scale=(1, 5))  # assuming ratings are between 1 and 5
#     data = Dataset.load_from_df(pd.DataFrame(user_ratings, columns=['userId', 'itemId', 'rating']), reader)
#
#     trainset, testset = train_test_split(data, test_size=0.2)
#
#     model = SVD()
#     model.fit(trainset)
#
#     predictions = model.test(testset)
#     print(f"RMSE: {accuracy.rmse(predictions)}")
#
#     # Get unseen products
#     all_products = Product.objects.all()
#     unseen_products = [product.id for product in all_products if
#                        not CartItem.objects.filter(user=user_id, product=product).exists()]
#
#     predictions = [model.predict(user_id, product_id) for product_id in unseen_products]
#     predictions.sort(key=lambda x: x.est, reverse=True)
#
#     top_predictions = predictions[:top_n]
#     recommended_product_ids = [pred[0] for pred in top_predictions]
#
#     return Product.objects.filter(id__in=recommended_product_ids)
#
#
# # Hybrid Recommendation
# def hybrid_recommendation(user_id, product_id, top_n=5):
#     # Content-based filtering
#     content_based_recs = get_similar_products(product_id, top_n)
#
#     # Collaborative filtering
#     collaborative_based_recs = get_collaborative_recommendations(user_id, top_n)
#
#     # Combine both recommendations
#     recommended_products = list(set(content_based_recs).union(set(collaborative_based_recs)))
#
#     return recommended_products[:top_n]
#
#
# # Example usage:
# # Assuming user_id=1 and product_id=1
# recommended_products = hybrid_recommendation(user_id=1, product_id=1, top_n=5)
# for product in recommended_products:
#     print(product.name)  # Or any other attribute to display