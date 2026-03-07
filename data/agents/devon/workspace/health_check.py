import urllib.request
import urllib.error
import time

def health_check():
    try:
        start = time.time()
        response = urllib.request.urlopen('http://localhost:8000/health', timeout=5)
        response_time = time.time() - start
        return {'status': 'OK', 'response_time': response_time}
    except urllib.error.URLError as e:
        return {'status': 'ERROR', 'error': str(e.reason)}
    except Exception as e:
        return {'status': 'ERROR', 'error': str(e)}

if __name__ == '__main__':
    result = health_check()
    if result['status'] == 'OK':
        print(f"[\u001b[32mOK\u001b[0m] Service healthy. Response time: {result['response_time']:.2f}s")
    else:
        print(f"[\u001b[31mDOWN\u001b[0m] Service unavailable: {result['error']}")
