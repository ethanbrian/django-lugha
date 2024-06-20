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
                # Step 2: Prepare data payload for Hugging Face API
                data_payload = [
                    f"{translation_response['source_language_name']} ({translation_response['source_abbreviation']})",
                    f"{translation_response['target_name']} ({translation_response['target_abbreviation']})",
                    translation_response['source_text'],
                ]

                # Step 3: Call Hugging Face API to initiate translation
                initial_response = requests.post("https://drlugha-translate-api.hf.space/run/predict", headers=headers, json={"data": data_payload})
                initial_response_content = initial_response.json()

                if initial_response.status_code == 200:
                    # Step 4: Check if the response contains a task_id to indicate queuing
                    task_id = initial_response_content.get('task_id')
                    if task_id:
                        # Step 5: Poll for result asynchronously
                        return self.poll_for_result(task_id, headers, translation_response.get('translation_id'))
                    else:
                        return JsonResponse({'error': 'Unexpected response from Hugging Face API: no task_id found'})
                else:
                    return JsonResponse({
                        'error': 'Error from Hugging Face API',
                        'hugging_face_response_content': initial_response_content,
                    })
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

    def poll_for_result(self, task_id, headers, generated_translation_id):
        poll_url = f"https://drlugha-translate-api.hf.space/run/poll/{task_id}"
        for _ in range(30):  # Poll up to 30 times (example)
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
        return JsonResponse({'error': 'Timeout waiting for Hugging Face API response'})
