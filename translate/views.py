from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views import View
import requests
import json
import time

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
                # Step 2: Queue the translation task using Hugging Face API
                queue_response = self.queue_translation_task(translation_response, headers)
                if queue_response.get('task_id'):
                    # Step 3: Poll for result asynchronously
                    return self.poll_for_result(queue_response['task_id'], headers, translation_response.get('translation_id'))
                else:
                    return JsonResponse({'error': 'Failed to queue translation task'})
            else:
                return JsonResponse({
                    'error': 'Error fetching translation details',
                    'translation_response': translation_response
                })
        except Exception as e:
            return JsonResponse({
                'error': 'Internal Server Error',
                'message': str(e),
            })

    def queue_translation_task(self, translation_response, headers):
        data_payload = {
            'source_text': translation_response['source_text'],
            'source_language_id': translation_response['source_language_id'],
            'target_language_id': translation_response['target_language_id']
        }

        queue_url = "https://drlugha-translate-api.hf.space/run/queue"
        queue_response = requests.post(queue_url, json=data_payload, headers=headers)
        return queue_response.json()

    def poll_for_result(self, task_id, headers, generated_translation_id):
        poll_url = f"https://drlugha-translate-api.hf.space/run/poll/{task_id}"
        for _ in range(30):  # Poll up to 30 times (adjust based on your requirement)
            time.sleep(2)  # Wait for 2 seconds before polling again
            poll_response = requests.get(poll_url, headers=headers)
            poll_response_content = poll_response.json()
            if poll_response_content.get('status') == 'completed':
                result = poll_response_content.get('data', [''])[0].strip()
                return JsonResponse({
                    'hugging_face_status_code': poll_response.status_code,
                    'translated_text': result,
                    'generated_translation_id': generated_translation_id,
                })
            elif poll_response_content.get('status') == 'failed':
                return JsonResponse({
                    'error': 'Translation failed',
                    'details': poll_response_content.get('error_message', 'Unknown error'),
                })

        return JsonResponse({'error': 'Timeout waiting for Hugging Face API response'})
