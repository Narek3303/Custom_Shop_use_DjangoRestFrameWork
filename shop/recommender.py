import redis
# import numpy
# import surprise
from django.conf import settings
from .models import Product, Review
# from sklearn.feature_extraction.text import TfidfVectorizer
# from sklearn.metrics.pairwise import cosine_similarity
# import pandas as pd
# from surprise import SVD, Dataset, Reader
# from surprise.model_selection import train_test_split
# from surprise import accuracy
from cart.models import CartItem

# Redis-ի կապի կառավարման բարելավում՝ connection pool
pool = redis.ConnectionPool(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    db=settings.REDIS_DB
)

r = redis.Redis(connection_pool=pool)


class Recommender:
    def get_product_key(self, id):
        return f'product:{id}:purchased_with'

    def products_bought(self, products):
        product_ids = [p.id for p in products]
        pipeline = r.pipeline()  # pipeline օգտագործել՝ միաժամանակյա հարցումների համար
        for product_id in product_ids:
            for with_id in product_ids:
                if product_id != with_id:
                    # Ավելացնում ենք 1 չափանիշը այն մասին, որ ապրանքները գնվել են միասին
                    pipeline.zincrby(self.get_product_key(product_id), 1, with_id)
                    # Սահմանում ենք TTL (24 ժամ)
                    pipeline.expire(self.get_product_key(product_id), 86400)  # 24 ժամ
        # Կատարում ենք հարցումները միաժամանակ
        pipeline.execute()

    def suggest_products_for(self, products, max_results=6):
        product_ids = [p.id for p in products]
        if len(products) == 1:
            # Միայն մեկ ապրանք
            suggestions = r.zrange(
                self.get_product_key(product_ids[0]), 0, -1, desc=True
            )[:max_results]
        else:
            # Մասշտաբված որոնում՝ մի քանի ապրանքներ
            flat_ids = ''.join([str(id) for id in product_ids])
            tmp_key = f'tmp_{flat_ids}'

            # Միավորում ենք բոլոր համապատասխան ստեղները
            keys = [self.get_product_key(id) for id in product_ids]
            r.zinterstore(tmp_key, keys)  # Միավորում ենք միայն համընկնող արժեքները

            # Հեռացնում ենք սկզբնական ապրանքները ժամանակավոր բանալիից
            r.zrem(tmp_key, *product_ids)

            # Ընդհանուր ցուցակը ստանում ենք ամենաբարձր արդյունքներով
            suggestions = r.zrange(tmp_key, 0, -1, desc=True)[:max_results]

            # Հեռացնում ենք ժամանակավոր բանալին
            r.delete(tmp_key)

        suggested_products_ids = [int(id) for id in suggestions]
        suggested_products = list(
            Product.objects.filter(id__in=suggested_products_ids)
        )
        suggested_products.sort(
            key=lambda x: suggested_products_ids.index(x.id)
        )

        return suggested_products

    def clear_purchases(self):
        pipeline = r.pipeline()  # pipeline օգտագործում ենք բազմակողմ հարցումներ
        product_ids = Product.objects.values_list('id', flat=True)

        # Մնացած հարցումները հավաքում ենք մեկ տեղում
        for product_id in product_ids:
            pipeline.delete(self.get_product_key(product_id))

        # Կատարում ենք բոլոր հարցումները միաժամանակ
        pipeline.execute()




# products = Product.objects.all()
# product_description = [product.description for product in products]
#
#
# vectorizer = TfidfVectorizer(stop_words='english')
# tfidf_matrix = vectorizer.fit_transform(product_description)
#
#
# cosine_sim = cosine_similarity(tfidf_matrix, tfidf_matrix)
#
#
# def get_similar_products(product_id, top_n=5):
#     idx = products.get(id=product_id).id
#     sim_scores = list(enumerate(cosine_sim[idx]))
#     sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
#     product_indices = [i[0] for i in sim_scores]
#     return [products[i] for i in product_indices]
#
#
# similar_products = get_similar_products(product_id=1, top_n=5)
#
# user_ratings = []  # [user_id, product_id, rating]
#
# # Մուտքագրեք տվյալները՝ Product-երի վարկանիշներով
# for review in Review.objects.all():
#     user_ratings.append([review.user.id, review.product.id, review.rating])
#
# # Մշակելու համար Surprise Dataset
# reader = Reader(rating_scale=(1, 5))  # assuming ratings are between 1 and 5
# data = Dataset.load_from_df(pd.DataFrame(user_ratings, columns=['userId', 'itemId', 'rating']), reader)
#
# # Տեսակավորումը
# trainset, testset = train_test_split(data, test_size=0.2)
#
# # SVD մոդելի ստեղծում
# model = SVD()
# model.fit(trainset)
#
# # Մոդելի արժեքավորման համար
# predictions = model.test(testset)
# print(f"RMSE: {accuracy.rmse(predictions)}")
#
#
# # Հարկավոր է առաջարկել անգնահատված ապրանքներ
# def recommend_products(user_id, top_n=5):
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
# # Օրինակ՝ ստանալ առաջարկվող ապրանքներ
# recommended_products = recommend_products(user_id=1, top_n=5)
#
#
# def hybrid_recommendation(user_id, product_id, top_n=5):
#     # Content-based filtering
#     content_based_recs = get_similar_products(product_id, top_n)
#
#     # Collaborative filtering
#     collaborative_based_recs = recommend_products(user_id, top_n)
#
#     # Կատարում ենք դրանց համադրումը՝ ընտրելով մի շարք լավագույն առաջարկներ
#     recommended_products = list(set(content_based_recs).union(set(collaborative_based_recs)))
#
#     return recommended_products[:top_n]
#
#
# # Օրինակ՝ ստանալ երկու մոտեցումների համադրությամբ առաջարկներ
# hybrid_recs = hybrid_recommendation(user_id=1, product_id=1, top_n=5)