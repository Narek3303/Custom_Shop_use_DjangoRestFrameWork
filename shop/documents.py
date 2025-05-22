# # products/documents.py
# from django_elasticsearch_dsl import Document, Index, fields
# from django_elasticsearch_dsl.registries import registry
# from .models import Product, Brand, Size, Color
#
# # Ստեղծում ենք Index՝ Products-ի համար
# product_index = Index('products')  # Մեկ index՝ բոլոր ապրանքների համար
#
# # Ստեղծում ենք Document՝ Product մոդելի համար
# @registry.register_document
# class ProductDocument(Document):
#     class Index:
#         name = 'products'  # Սա կլինի մեր index-ի անունը
#
#     class Django:
#         model = Product  # Մոդելը, որի վրա աշխատում ենք
#         fields = [
#             'id', 'name', 'description',  # Դաշտերը, որոնք կգտնվեն index-ում
#         ]
#         related_models = [Brand, Size, Color, ]  # Եթե ունես կապված մոդելներ, այստեղ ավելացրու
#
#     brand = fields.ObjectField(properties={
#         'name': fields.TextField(),
#     })
