from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views import View
from gradio_client import Client
import json
import requests

@method_decorator(csrf_exempt, name='dispatch')
class TranslationDetailsView(View):
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        host_header = request.headers.get('Host')
        print(f'Received Host header: {host_header}')
        
        hf_token = "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"
        headers = {
            "Authorization": "Bearer " + hf_token,
            "Content-Type": "application/json",
            "X-CSRFToken": request.headers.get('X-CSRFToken')
        }

        try:
            data = json.loads(request.body)
            translation_id = data.get('translationId')
            language_id = data.get('languageId')

            # Step 1: Call Spring Boot endpoint to fetch translation details
            spring_boot_url = "https://springlugha.drlugha.com/get_translation_details"
            response = requests.post(spring_boot_url, json={'translationId': translation_id, 'languageId': language_id}, headers=headers)
            translation_response = response.json()

            if response.status_code == 200:
                # Extract necessary data from translation_response
                source_text = translation_response.get('source_text')
                source_language_id = translation_response.get('source_language_id')
                target_language_id = translation_response.get('target_language_id')

                # Step 2: Use Gradio Client to initiate translation
                # Adjust the Client initialization according to Gradio's API
                client = Client("DrLugha/translate-api")  # Replace with your specific Gradio space name
                job = client.submit(source_text, api_name="/predict")

                # Wait for the job to complete and get the result
                result = job.result()

                # Handle the result
                translated_text = result['data']

                return JsonResponse({
                    'translated_text': translated_text,
                })
            else:
                return JsonResponse({
                    'error': 'Error fetching translation details',
                    'translation_response': translation_response
                }, status=response.status_code)
        except json.JSONDecodeError:
            return JsonResponse({
                'error': 'Invalid JSON format'
            }, status=400)
        except requests.RequestException as e:
            return JsonResponse({
                'error': 'Error fetching translation details from Spring Boot service',
                'message': str(e)
            }, status=500)
        except Exception as e:
            return JsonResponse({
                'error': 'Internal Server Error',
                'message': str(e),
            }, status=500)
