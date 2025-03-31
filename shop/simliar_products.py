import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from .models import Product


def get_similar_products_ml(product, top_n=5):
    """Վերադարձնում է ML-ով գտած ամենանմանատիպ ապրանքները"""

    # Բոլոր ապրանքները բազայից
    all_products = Product.objects.exclude(id=product.id)

    # Եթե չկա ուրիշ ապրանք, վերադարձնենք դատարկ queryset
    if not all_products.exists():
        return Product.objects.none()

    # Ստեղծում ենք ցուցակ՝ կազմված այն դաշտերից, որոնք կհաշվեն նմանությունը
    product_texts = [
                        f"{product.name} {product.description} {product.category.name} {product.brand.name} {', '.join([color.name for color in product.colors.all()])} {', '.join([tag.name for tag in product.tags.all()])}"
                    ] + [
                        f"{p.name} {p.description} {p.category.name} {p.brand.name} {', '.join([color.name for color in p.colors.all()])} {', '.join([tag.name for tag in p.tags.all()])}"
                        for p in all_products
                    ]

    # Ստեղծում ենք TF-IDF vectorizer
    vectorizer = TfidfVectorizer(stop_words="english")
    tfidf_matrix = vectorizer.fit_transform(product_texts)

    # Գտնում ենք cosine similarity
    cosine_similarities = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:]).flatten()

    # Գնի նմանություն (մաքրված տարբերություն)
    price_differences = [
        abs(product.price - p.price) for p in all_products
    ]

    # Գնի ազդեցությունը կարող ենք դնել որպես փշոտ գործոն
    max_price_diff = max(price_differences)
    price_similarities = [1 - (price_diff / max_price_diff) if max_price_diff != 0 else 1 for price_diff in
                          price_differences]

    # Միավորում ենք Cosine Similarity- և գնի Similarity-ն
    final_similarities = [
        cosine_similarities[i] * float(price_similarities[i]) for i in range(len(cosine_similarities))
    ]

    # Ստանում ենք ամենաբարձր նմանություն ունեցող top_n ապրանքները
    similar_indices = np.argsort(final_similarities)[::-1][:top_n]
    similar_products = [all_products[int(i)] for i in similar_indices]

    return similar_products



