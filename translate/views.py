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
        
        hf_token = "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"  # Replace with your actual Hugging Face token
        headers = {
            "Authorization": f"Bearer {hf_token}",
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
                source_name = translation_response.get('source_name')
                source_abbreviation = translation_response.get('source_abbreviation')
                target_name = translation_response.get('target_name')
                target_abbreviation = translation_response.get('target_abbreviation')

                # Construct the src and tgt parameters
                src = f"{source_name} ({source_abbreviation})"
                tgt = f"{target_name} ({target_abbreviation})"

                # Step 2: Use Gradio Client to initiate translation
                client = Client("DrLugha/translate-api", hf_token=hf_token)  # Authenticate with the token
                result = client.predict(
                    src=src,
                    tgt=tgt,
                    text=source_text,
                    api_name="/predict"
                )

                # Debug print to inspect the result structure
                print("Prediction Result:", result)

                # Handle the result
                if isinstance(result, dict) and 'data' in result:
                    translated_text = result['data']
                else:
                    raise ValueError("Unexpected response format from translation API")

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
        except ValueError as e:
            return JsonResponse({
                'error': 'Error processing translation API response',
                'message': str(e)
            }, status=500)
        except Exception as e:
            return JsonResponse({
                'error': 'Internal Server Error',
                'message': str(e),
            }, status=500)
