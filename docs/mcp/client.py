#!/usr/bin/env python3
"""Small synchronous FontLab MCP stdio client (Python 3.10+, stdlib only).
One request in flight; no retries. Closing this client stops only its bridge.
Example: python3 client.py '/Applications/FontLab 9.app/Contents/MacOS/fontlab-mcp'
"""
from __future__ import annotations
import argparse
from collections import deque
import json
from pathlib import Path
import queue
import subprocess
import threading
import time
from typing import Any


class RPCError(RuntimeError):
    def __init__(self, response: dict):
        self.response = response
        super().__init__(str(response.get('error')))


class ToolError(RuntimeError):
    def __init__(self, name: str, payload: Any, envelope: dict):
        self.name, self.payload, self.envelope = name, payload, envelope
        super().__init__(f'{name}: {payload}')


def decode_result(envelope: dict) -> Any:
    """FontLab returns JSON as text content, not structuredContent."""
    texts = [item['text'] for item in envelope.get('content', [])
             if item.get('type') == 'text' and isinstance(item.get('text'), str)]
    if len(texts) == 1:
        try:
            return json.loads(texts[0])
        except json.JSONDecodeError:
            return texts[0]
    return '\n'.join(texts) if texts else envelope


class Client:
    def __init__(self, bridge: str | Path, timeout: float = 75):
        if timeout <= 0: raise ValueError('timeout must be positive')
        self.timeout = timeout
        self._proc = subprocess.Popen([str(bridge)], stdin=subprocess.PIPE,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
            encoding='utf-8', bufsize=1)
        self._responses: queue.Queue = queue.Queue()
        self._stderr = deque(maxlen=20)
        self._lock = threading.Lock()
        self._next_id = 1
        self._closed = False
        threading.Thread(target=self._read_stdout, daemon=True).start()
        threading.Thread(target=self._read_stderr, daemon=True).start()
        try:
            self.request('initialize', {'protocolVersion':'2024-11-05',
                'capabilities':{}, 'clientInfo':{'name':'fontlab-reference-client','version':'1.0'}})
            self.notify('notifications/initialized', {})
        except Exception:
            self.close()
            raise

    def _read_stdout(self):
        try:
            for line in self._proc.stdout:
                if line.strip(): self._responses.put(json.loads(line))
        except Exception as exc:
            self._responses.put(exc)
        finally:
            self._proc.stdout.close()
            self._responses.put(EOFError('FontLab bridge stdout closed'))

    def _read_stderr(self):
        try:
            for line in self._proc.stderr:
                self._stderr.append(line[:4096])
        finally:
            self._proc.stderr.close()

    def _write(self, message: dict):
        if self._closed: raise RuntimeError('Client is closed')
        self._proc.stdin.write(json.dumps(message, ensure_ascii=False, allow_nan=False) + '\n')
        self._proc.stdin.flush()

    def notify(self, method: str, params: dict | None = None):
        with self._lock:
            self._write({'jsonrpc':'2.0', 'method':method, 'params':params or {}})

    def request(self, method: str, params: dict | None = None) -> dict:
        with self._lock:
            request_id = self._next_id
            self._next_id += 1
            deadline = time.monotonic() + self.timeout
            self._write({'jsonrpc':'2.0', 'id':request_id, 'method':method, 'params':params or {}})
            while True:
                try:
                    reply = self._responses.get(timeout=max(0, deadline - time.monotonic()))
                except queue.Empty:
                    self.close()
                    raise TimeoutError('FontLab response deadline exceeded. Outcome unknown; inspect state before retrying.') from None
                if isinstance(reply, Exception): raise reply
                if not isinstance(reply, dict): raise RuntimeError('Expected JSON-RPC response object')
                if 'id' not in reply: continue  # A future notification, not our response.
                if reply['id'] != request_id:
                    raise RuntimeError(f'Unexpected response ID: {reply["id"]}')
                if 'error' in reply: raise RPCError(reply)
                if 'result' not in reply: raise RuntimeError('Response lacks result/error')
                return reply['result']

    def tools(self) -> list[dict]:
        # Also proves the application is reachable and authenticated.
        return self.request('tools/list')['tools']

    def call(self, name: str, **arguments) -> Any:
        envelope = self.request('tools/call', {'name':name, 'arguments':arguments})
        payload = decode_result(envelope)
        if envelope.get('isError') or (isinstance(payload, dict) and
                (payload.get('success') is False or payload.get('status') == 'error')):
            raise ToolError(name, payload, envelope)
        return payload

    def close(self):
        if self._closed: return
        self._closed = True
        try:
            self._proc.stdin.close()
        except (BrokenPipeError, OSError):
            pass
        try:
            self._proc.wait(timeout=2)
        except subprocess.TimeoutExpired:
            self._proc.kill()
            self._proc.wait(timeout=2)
        # Reader threads own stdout/stderr until EOF; do not block closing them
        # here while one is inside readline.

    def __enter__(self): return self
    def __exit__(self, *_): self.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('bridge', help='Absolute path to the matching fontlab-mcp executable')
    args = parser.parse_args()
    try:
        with Client(args.bridge) as client:
            print(json.dumps({'tools':[t['name'] for t in client.tools()],
                              'open_fonts':client.call('list_fonts')}, ensure_ascii=False, indent=2))
    except (OSError, RuntimeError, ValueError, EOFError) as exc:
        parser.exit(1, f'Connection check failed: {exc}\nCheck the bridge path, running FontLab, and external MCP access setting.\n')

if __name__ == '__main__': main()
