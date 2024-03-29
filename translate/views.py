from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views import View
import requests
import json

@method_decorator(csrf_exempt, name='dispatch')
class TranslationDetailsView(View):
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        # Log the Host header value
        host_header = request.headers.get('Host')
        print(f'Received Host header: {host_header}')
        # Replace 'your_hf_token' with your actual Hugging Face API token
        hf_token = "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"
        headers = {
            "Authorization": "Bearer " + hf_token,
            "Content-Type": "application/json",
            "X-CSRFToken": request.headers.get('X-CSRFToken')  # Include CSRF token in headers
        }

        try:
            # Extract translationId and languageId from the request body
            data = json.loads(request.body)
            translation_id = data.get('translationId')
            language_id = data.get('languageId')

            # Make an HTTP POST request to fetch translation details dynamically
            spring_boot_url = "https://springlugha.drlugha.com/get_translation_details"
            response = requests.post(spring_boot_url, json={'translationId': translation_id, 'languageId': language_id}, headers=headers)
            translation_response = response.json()
            print(translation_response)

            # Check if the request was successful
            if response.status_code == 200:
                # Constructing the data payload for the Hugging Face API request
                data_payload = [
                    f"{translation_response['source_language_name']} ({translation_response['source_abbreviation']})",
                    f"{translation_response['target_name']} ({translation_response['target_abbreviation']})",
                    translation_response['source_text'],
                ]

                hf_response = requests.post("https://drlugha-translate-api.hf.space/run/predict", headers=headers, json={
                    "data": data_payload
                })

                # Check the status code and response content from Hugging Face API
                if hf_response.status_code == 200:
                    hugging_face_response_content = hf_response.json()
                    translated_text = hugging_face_response_content.get('data', [''])[0].strip()

                    return JsonResponse({
                        'hugging_face_status_code': hf_response.status_code,
                        'translated_text': translated_text,
                        'generated_translation_id': translation_response.get('translation_id'),
                    })
                else:
                    return JsonResponse({
                        'error': 'Error from Hugging Face API',
                        'hugging_face_response_content': hf_response.json(),
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


# class VoiceResponseView(View):
#     def dispatch(self, request, *args, **kwargs):
#         return super().dispatch(request, *args, **kwargs)

#     def post(self, request, *args, **kwargs):
#               # Log the Host header value
#         host_header = request.headers.get('Host')
#         print(f'Received Host header: {host_header}')
#         # Replace 'your_hf_token' with your actual Hugging Face API token
#         hf_token = "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"
#         headers = {
#             "Authorization": "Bearer " + hf_token,
#             "Content-Type": "application/json",
#             "X-CSRFToken": request.headers.get('X-CSRFToken')  # Include CSRF token in headers
#         }

#         try:
#             # Extract translationId and languageId from the request body
#             data = json.loads(request.body)
#             translation_id = data.get('translationId')
#             language_id = data.get('languageId')

#             # Make an HTTP POST request to fetch translation details dynamically
#             spring_boot_url = "https://springapi.drlugha.com/get_translation_details"
#             response = requests.post(spring_boot_url, json={'translationId': translation_id, 'languageId': language_id}, headers=headers)
#             translation_response = response.json()
#             print(translation_response)

#         # Check if the request was successful
#         if response.status_code == 200:
#             # Constructing the data payload for the Hugging Face API request
#             data_payload = [
#                 f"{translation_response['source_language_name']} ({translation_response['source_abbreviation']})",
#                 f"{translation_response['target_name']} ({translation_response['target_abbreviation']})",
#                 translation_response['source_text'],
#             ]

#             hf_response = requests.post("https://drlugha-translate-api.hf.space/run/predict", headers=headers, json={
#                 "data": data_payload
#             })

#             # Check the status code and response content from Hugging Face API
#             if hf_response.status_code == 200:
#                 hugging_face_response_content = hf_response.json()
#                 encoded_audio = hugging_face_response_content.get('data', [''])[0].strip()

#                 # Decode the base64 audio data
#                 decoded_audio = base64.b64decode(encoded_audio)

#                 # Save the audio file
#                 audio_file_path = "temp.wav"
#                 with open(audio_file_path, "wb") as wav_file:
#                     wav_file.write(decoded_audio)

#                 # Return the audio file in the response
#                 with open(audio_file_path, "rb") as audio_file:
#                     response = HttpResponse(audio_file.read(), content_type="audio/wav")
#                     response['Content-Disposition'] = 'attachment; filename="translated_audio.wav"'
#                     return response

#             else:
#                 return JsonResponse({
#                     'error': 'Error from Hugging Face API',
#                     'hugging_face_response_content': hf_response.json(),
#                 })

#         else:
#             return JsonResponse({
#                 'error': 'Error fetching translation details',
#                 'translation_response': translation_response
#             })