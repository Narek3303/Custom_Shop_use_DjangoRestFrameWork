# gdpr/utils.py
from django.apps import apps
from django.db import models
from django.core.serializers import serialize
from django.core.files.base import ContentFile
import json
import zipfile
import io
from datetime import datetime


class GDPRUtils:
    @staticmethod
    def get_user_data(user):
        """
        Հավաքում է բոլոր տվյալները որոնք կապված են օգտատիրոջ հետ
        """
        data = {}
        models_to_include = [
            'auth.User',
            'auth.Group',
            'gdpr.GDPRConsent',
            'gdpr.DataSubjectRequest',
            # Ավելացրեք ձեր հավելյալ մոդելները այստեղ
        ]

        for model_path in models_to_include:
            app_label, model_name = model_path.split('.')
            model = apps.get_model(app_label, model_name)

            # Ստուգել եթե մոդելը User foreign key ունի
            for field in model._meta.get_fields():
                if isinstance(field, models.ForeignKey) and field.related_model == user.__class__:
                    queryset = model.objects.filter(**{field.name: user})
                    serialized_data = serialize('python', queryset)
                    data[model_path] = serialized_data
                    break

        return data

    @staticmethod
    def generate_data_portability_zip(user):
        """
        Ստեղծում է ZIP ֆայլ օգտատիրոջ բոլոր տվյալներով
        """
        data = GDPRUtils.get_user_data(user)

        # Ստեղծում ենք in-memory ZIP ֆայլ
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for model_path, model_data in data.items():
                file_name = f"{model_path.replace('.', '_')}.json"
                zip_file.writestr(file_name, json.dumps(model_data, indent=2))

            # Ավելացնում ենք README ֆայլ
            readme_content = f"""
            GDPR Data Portability Export
            ----------------------------
            User: {user.email}
            Generated at: {datetime.now().isoformat()}

            This archive contains all personal data we have stored about you.
            """
            zip_file.writestr('README.txt', readme_content.strip())

        zip_buffer.seek(0)
        return zip_buffer

    @staticmethod
    def anonymize_user(user):
        """
        Անանունացնում է օգտատիրոջ տվյալները (Right to be Forgotten)
        """
        # Anonymize User model
        user.email = f"anon_{user.id}@example.com"
        user.first_name = "Anonymous"
        user.last_name = "User"
        user.username = f"anon_{user.id}"
        user.save()

        # Ավելացրեք ձեր հատուկ մոդելների անանունացումը այստեղ
        # Օրինակ՝ Order, Profile, etc.

        return user