from erp.models import ERPIntegration  # Փոխարինել from .models-ից
from erp.services import ERPSyncService
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status


class ERPSyncView(APIView):
    def post(self, request, integration_id):
        try:
            integration = ERPIntegration.objects.get(pk=integration_id)
            service = ERPSyncService(integration)

            # Կարող եք սինխրոնիզացնել բոլոր մոդելները կամ ըստ պարամետրերի
            model_name = request.data.get('model')
            if model_name:
                mapping = ERPObjectMapping.objects.get(
                    integration=integration,
                    django_model=model_name
                )
                log = service.sync_model(mapping)
            else:
                logs = []
                for mapping in integration.erpobjectmapping_set.all():
                    logs.append(service.sync_model(mapping))
                return Response({'logs': [log.id for log in logs]})

            return Response({
                'status': log.status,
                'records': log.record_count,
                'details': log.details
            })
        except ERPIntegration.DoesNotExist:
            return Response(
                {'error': 'ERP integration not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

