# gdpr/views.py
from django.shortcuts import get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from .models import GDPRConsent, DataSubjectRequest, DataInventory
from .utils import GDPRUtils
import json


class GDPRConsentView(View):
    """GET և POST հարցումների աջակցությամբ համաձայնության view"""

    def get(self, request):
        """Վերադարձնում է օգտատիրոջ ընթացիկ համաձայնությունները"""
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Authentication required'}, status=401)

        consents = GDPRConsent.objects.filter(user=request.user)
        consent_data = {
            consent.consent_type: consent.granted
            for consent in consents
        }

        return JsonResponse({
            'consents': consent_data,
            'required_consents': [choice[0] for choice in GDPRConsent.CONSENT_TYPES]
        })

    def post(self, request):
        """Թարմացնում է համաձայնությունները"""
        data = json.loads(request.body)
        consent_type = data.get('consent_type')
        granted = data.get('granted', False)
        version = data.get('version', '1.0')

        if not consent_type:
            return JsonResponse({'error': 'consent_type is required'}, status=400)

        consent, created = GDPRConsent.objects.update_or_create(
            user=request.user,
            consent_type=consent_type,
            defaults={
                'granted': granted,
                'version': version,
                'ip_address': self._get_client_ip(request),
                'user_agent': request.META.get('HTTP_USER_AGENT', '')
            }
        )

        return JsonResponse({
            'status': 'success',
            'consent': {
                'type': consent.consent_type,
                'granted': consent.granted,
                'timestamp': consent.timestamp.isoformat()
            }
        })

    def _get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        return x_forwarded_for.split(',')[0] if x_forwarded_for else request.META.get('REMOTE_ADDR')


class DataPortabilityAPIView(APIView):
    """
    Տվյալների պորտաբիլության API endpoint
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        zip_buffer = GDPRUtils.generate_data_portability_zip(request.user)
        response = HttpResponse(zip_buffer.getvalue(), content_type='application/zip')
        response['Content-Disposition'] = f'attachment; filename="gdpr_export_{request.user.id}.zip"'
        return response


class RightToBeForgottenAPIView(APIView):
    """
    Մոռացման իրավունքի API endpoint
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # Ստեղծում ենք հարցում
        dsr = DataSubjectRequest.objects.create(
            user=request.user,
            request_type='erasure',
            request_data={'reason': request.data.get('reason', 'User requested account deletion')}
        )

        # Կարող եք ավելացնել լրացուցիչ վավերացում այստեղ

        return Response({
            'status': 'request_received',
            'request_id': str(dsr.id),
            'message': 'Your request has been received and will be processed within 30 days'
        }, status=status.HTTP_202_ACCEPTED)


class GDPRAdminAPIView(APIView):
    """
    Ադմինիստրատորի GDPR API endpoint
    """
    permission_classes = [IsAuthenticated]

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_staff:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, request_id=None):
        if request_id:
            dsr = get_object_or_404(DataSubjectRequest, id=request_id)
            return Response(self._serialize_dsr(dsr))

        # Փնտրել բոլոր հարցումները
        status_filter = request.query_params.get('status')
        queryset = DataSubjectRequest.objects.all()

        if status_filter:
            queryset = queryset.filter(status=status_filter)

        return Response({
            'requests': [self._serialize_dsr(dsr) for dsr in queryset.order_by('-created_at')]
        })

    def post(self, request, request_id):
        dsr = get_object_or_404(DataSubjectRequest, id=request_id)
        action = request.data.get('action')

        if action == 'complete':
            if dsr.request_type == 'erasure':
                GDPRUtils.anonymize_user(dsr.user)
            dsr.complete({'message': 'Request completed by admin'})
            return Response({'status': 'completed'})

        elif action == 'reject':
            reason = request.data.get('reason', 'Request rejected by admin')
            dsr.reject(reason)
            return Response({'status': 'rejected', 'reason': reason})

        return Response({'error': 'Invalid action'}, status=400)

    def _serialize_dsr(self, dsr):
        return {
            'id': str(dsr.id),
            'user': {
                'id': dsr.user.id,
                'email': dsr.user.email
            },
            'request_type': dsr.request_type,
            'status': dsr.status,
            'created_at': dsr.created_at.isoformat(),
            'completed_at': dsr.completed_at.isoformat() if dsr.completed_at else None,
            'notes': dsr.notes
        }
