import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from predict import DeviceFaultPredictor


MODELS = {
    'fridge': {
        'path': Path(__file__).resolve().parent / 'models' / 'smart_fridge_fault_classifier.pkl',
        'required_fields': [
            'internal_temp',
            'external_temp',
            'compressor_power',
            'door_open_duration',
            'humidity',
            'fan_speed',
            'vibration_level',
            'voltage',
        ],
    },
    'multi_device': {
        'path': Path(__file__).resolve().parent / 'models' / 'multi_device_fault_classifier.pkl',
        'required_fields': ['device_type'],
    },
}
HOST = '0.0.0.0'
PORT = 8000


def load_predictor(model_key):
    model_path = MODELS[model_key]['path']
    if not model_path.exists():
        raise FileNotFoundError(
            f'Model `{model_key}` not found at {model_path}. Train the model before starting the API.'
        )
    return DeviceFaultPredictor(str(model_path))


predictors = {}
for model_key in MODELS:
    try:
        predictors[model_key] = load_predictor(model_key)
    except FileNotFoundError:
        predictors[model_key] = None


def json_response(handler, status_code, payload):
    response = json.dumps(payload).encode('utf-8')
    handler.send_response(status_code)
    handler.send_header('Content-Type', 'application/json')
    handler.send_header('Content-Length', str(len(response)))
    handler.send_header('Access-Control-Allow-Origin', '*')
    handler.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
    handler.send_header('Access-Control-Allow-Headers', 'Content-Type')
    handler.end_headers()
    handler.wfile.write(response)


def parse_request_body(handler):
    content_length = int(handler.headers.get('Content-Length', '0'))
    raw_body = handler.rfile.read(content_length) if content_length > 0 else b'{}'
    return json.loads(raw_body.decode('utf-8'))


def validate_payload(payload, required_fields):
    missing = [field for field in required_fields if field not in payload]
    if missing:
        raise ValueError(f'Missing required fields: {missing}')

    cleaned = {}
    for key, value in payload.items():
        if value in (None, ''):
            continue

        if key == 'device_type':
            cleaned[key] = str(value)
        else:
            cleaned[key] = float(value)
    return cleaned


def get_predictor_or_error(model_key):
    predictor = predictors.get(model_key)
    if predictor is None:
        model_path = MODELS[model_key]['path']
        raise FileNotFoundError(f'Model `{model_key}` is not available at {model_path}.')
    return predictor


def build_prediction_response(model_key, cleaned_payload):
    predictor = get_predictor_or_error(model_key)
    result = predictor.predict_single(**cleaned_payload)
    probabilities = {
        label: float(score)
        for label, score in result['probabilities'].items()
    }
    confidence = max(probabilities.values()) if probabilities else 0.0

    return {
        'model': model_key,
        'prediction': result['prediction'],
        'confidence': confidence,
        'probabilities': probabilities,
        'suggestions': result['suggestions'],
        'input': cleaned_payload,
    }


class DiagnosticsRequestHandler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        json_response(self, 200, {'status': 'ok'})

    def do_GET(self):
        if self.path == '/health':
            json_response(
                self,
                200,
                {
                    'status': 'ok',
                    'models': {
                        model_key: {
                            'loaded': predictors[model_key] is not None,
                            'model_path': MODELS[model_key]['path'].name,
                            'supported_features': predictors[model_key].feature_names if predictors[model_key] else [],
                        }
                        for model_key in MODELS
                    },
                },
            )
            return

        if self.path == '/model-info':
            json_response(
                self,
                200,
                {
                    'models': {
                        model_key: {
                            'model_path': MODELS[model_key]['path'].name,
                            'features': predictors[model_key].feature_names if predictors[model_key] else [],
                            'classes': [str(label) for label in predictors[model_key].label_encoder.classes_] if predictors[model_key] else [],
                        }
                        for model_key in MODELS
                    },
                },
            )
            return

        json_response(self, 404, {'detail': 'Endpoint not found.'})

    def do_POST(self):
        if self.path not in {'/predict/fridge', '/predict/device'}:
            json_response(self, 404, {'detail': 'Endpoint not found.'})
            return

        try:
            payload = parse_request_body(self)
            if self.path == '/predict/fridge':
                cleaned_payload = validate_payload(payload, MODELS['fridge']['required_fields'])
                response = build_prediction_response('fridge', cleaned_payload)
            else:
                cleaned_payload = validate_payload(payload, MODELS['multi_device']['required_fields'])
                response = build_prediction_response('multi_device', cleaned_payload)

            json_response(self, 200, response)
        except json.JSONDecodeError:
            json_response(self, 400, {'detail': 'Invalid JSON payload.'})
        except FileNotFoundError as exc:
            json_response(self, 500, {'detail': str(exc)})
        except ValueError as exc:
            json_response(self, 400, {'detail': str(exc)})
        except Exception as exc:
            json_response(self, 500, {'detail': f'Prediction failed: {exc}'})

    def log_message(self, format, *args):
        return


if __name__ == '__main__':
    server = ThreadingHTTPServer((HOST, PORT), DiagnosticsRequestHandler)
    print(f'Starting diagnostics API on http://{HOST}:{PORT}')
    server.serve_forever()