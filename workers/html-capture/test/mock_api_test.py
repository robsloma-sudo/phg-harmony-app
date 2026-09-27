"""Run worker.py against a local mock of menu-render-worker-api: one job, then empty."""
import json, os, subprocess, sys, threading, time
from http.server import BaseHTTPRequestHandler, HTTPServer
HERE = os.path.dirname(os.path.abspath(__file__)); got = {}
class H(BaseHTTPRequestHandler):
    jobs = [{'status': 'job', 'page_id': 7, 'document_id': 1, 'page_number': 1, 'source_url': 'file://' + HERE + '/fixtures/tabs.html', 'target_width': 1400, 'jpeg_quality': 85}]
    def log_message(self, *a): pass
    def do_POST(self):
        n = int(self.headers.get('content-length') or 0); body = self.rfile.read(n)
        got.setdefault('tokens', set()).add(self.headers.get('x-worker-token'))
        if 'action=claim_html' in self.path: r = H.jobs.pop(0) if H.jobs else {'status': 'empty'}
        elif 'action=complete_html' in self.path: got['complete'] = (self.path, len(body), body[:3]); r = {'status': 'ready'}
        else: got['fail'] = body; r = {'status': 'retry'}
        b = json.dumps(r).encode(); self.send_response(200); self.send_header('content-type', 'application/json'); self.end_headers(); self.wfile.write(b)
srv = HTTPServer(('127.0.0.1', 0), H); threading.Thread(target=srv.serve_forever, daemon=True).start()
env = dict(os.environ, PHG_WORKER_API_URL=f'http://127.0.0.1:{srv.server_port}/functions/v1/menu-render-worker-api', PHG_WORKER_TOKEN='t0k', PHG_IDLE_SECONDS='1', NO_PROXY='127.0.0.1', no_proxy='127.0.0.1')
p = subprocess.Popen([sys.executable, os.path.join(HERE, '..', 'worker.py')], env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
t0 = time.time()
while 'complete' not in got and 'fail' not in got and time.time() - t0 < 90: time.sleep(0.5)
time.sleep(1); p.terminate(); out = p.communicate(timeout=10)[0]
print(out[-600:]); print('complete:', got.get('complete'), 'fail:', got.get('fail'), 'tokens:', got.get('tokens'))
ok = got.get('complete') and got['complete'][2] == b'\xff\xd8\xff' and 'page_id=7' in got['complete'][0] and 'height=' in got['complete'][0] and got['tokens'] == {'t0k'}
print('PASS' if ok else 'FAIL'); sys.exit(0 if ok else 1)
