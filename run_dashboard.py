"""
Small runner to launch dashboard on 0.0.0.0 for network access and debug disabled
"""
from dashboard import app
import argparse
import webbrowser
import socket


def find_local_ip():
    """Return the local IP address for the host."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Doesn't have to be reachable
        s.connect(('10.255.255.255', 1))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip


def main():
    parser = argparse.ArgumentParser(description='Run the People Analytics Dash app')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind (default 0.0.0.0)')
    parser.add_argument('--port', default=8050, type=int, help='Port to bind (default 8050)')
    parser.add_argument('--open', action='store_true', help='Open the browser to the URL after start')
    args = parser.parse_args()

    # Print quick access info
    local_ip = find_local_ip()
    print(f"Starting Dash app on host={args.host}:{args.port} (debug=False)")
    print(f"Local URLs: http://127.0.0.1:{args.port} or http://{local_ip}:{args.port}")

    if args.open:
        webbrowser.open(f"http://127.0.0.1:{args.port}")

    # Run (Dash v2.14+ uses app.run)
    app.run(host=args.host, port=args.port, debug=False)


if __name__ == '__main__':
    main()
