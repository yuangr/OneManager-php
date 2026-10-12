from pathlib import Path
from tempfile import TemporaryDirectory
import http.server
import ssl
import subprocess
import threading
import unittest

ROOT = Path(__file__).resolve().parents[1]

class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"fixture-ok")
    def log_message(self, *args):
        pass

class VerifiedCloudTransportTests(unittest.TestCase):
    def test_real_shared_clients_verify_certificate_and_hostname(self):
        with TemporaryDirectory() as temp:
            cert = Path(temp) / "cert.pem"
            key = Path(temp) / "key.pem"
            subprocess.run(["openssl", "req", "-x509", "-newkey", "rsa:2048", "-nodes", "-days", "1", "-subj", "/CN=localhost", "-addext", "subjectAltName=DNS:localhost", "-keyout", str(key), "-out", str(cert)], check=True, capture_output=True)
            server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
            context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            context.load_cert_chain(cert, key)
            server.socket = context.wrap_socket(server.socket, server_side=True)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                for function in ("curl", "no_return_curl"):
                    cases = [(None, "localhost", "failure"), (cert, "localhost", "success"), (cert, "127.0.0.1", "failure")]
                    for ca, host, result in cases:
                        with self.subTest(function=function, trusted=ca is not None, host=host):
                            args = ["php"]
                            if ca:
                                args += ["-d", "curl.cainfo=" + str(ca)]
                            args += [str(ROOT / "tests/tls_client.php"), function, f"https://{host}:{server.server_port}/", result]
                            process = subprocess.run(args, capture_output=True, text=True, timeout=15)
                            self.assertEqual(process.returncode, 0, process.stderr)
            finally:
                server.shutdown()
                thread.join(timeout=5)
                server.server_close()

if __name__ == "__main__":
    unittest.main()
