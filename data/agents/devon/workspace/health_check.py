import urllib.request
import urllib.error
import time
import socket

def health_check():
    # DNS resolution check
    try:
        socket.gethostbyname('google.com')
        dns_ok = True
    except Exception as e:
        dns_ok = False
        dns_error = str(e)

    # Server connectivity check
    try:
        start = time.time()
        response = urllib.request.urlopen('http://localhost:8000/health', timeout=5)
        response_time = time.time() - start
        return {
            'status': 'OK',
            'response_time': response_time,
            'dns_status': 'REOLVED' if dns_ok else 'UNRESOLVED',
        }
    except urllib.error.URLError as e:
        return {
            'status': 'ERROR',
            'error': str(e.reason),
            'dns_status': 'REOLVED' if dns_ok else 'UNRESOLVED',
        }
    except Exception as e:
        return {
            'status': 'ERROR',
            'error': str(e),
            'dns_status': 'REOLVED' if dns_ok else 'UNRESOLVED',
        }

if __name__ == '__main__':
    result = health_check()
    if result['status'] == 'OK':
        print(f"[\u001b[32mOK\u001b[0m] Service healthy. Response time: {result['response_time']:.2f}s")
    else:
        print(f"[\u001b[31mDOWN\u001b[0m] Service unavailable: {result['error']}")
    print(f"DNS resolution: {result['dns_status']}")
