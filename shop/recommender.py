import redis
from django.conf import settings
from .models import Product

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
