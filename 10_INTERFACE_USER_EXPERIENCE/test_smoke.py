from pathlib import Path
r = Path(__file__).parents[1]
h = (r / 'src/index.html').read_text()
j = (r / 'src/app.js').read_text()
c = (r / 'src/styles.css').read_text()

# Required UI surfaces from PART10_COVERAGE.md must exist as real ids, not just be mentioned.
for x in ['id="input"', 'id="modal"', 'id="history"', 'id="settings"', 'id="diagnostics"',
          'id="historyList"', 'id="diag"']:
    assert x in h, f'missing UI element: {x}'

# Task panel must participate in the same show/hide system as the other pages,
# otherwise it stays visible under every other page (layout bug).
assert 'id="task" class="grid page active"' in h

# Backend contract vocabulary (10.22 / 10.23 / 10.31) must be present verbatim in the bridge code.
for x in ['TASK_CREATE', 'TASK_APPROVE', 'TASK_PAUSE', 'TASK_RESUME', 'TASK_CANCEL',
          'WAITING_FOR_APPROVAL', 'VERIFYING', 'COMPLETED', 'TASK_FINALIZED',
          'APP_STARTING', 'SETUP_REQUIRED', 'WAITING_FOR_USER', 'RECOVERING', 'FAILED']:
    assert x in j, f'missing state/command token: {x}'

for x in ['UI_BACKEND_DISCONNECTED', 'UI_COMMAND_INVALID', 'UI_EVENT_SYNC_FAILED',
          'HEALTH_CHECK_FAILED', 'APPROVAL_STATE_INVALID']:
    assert x in j, f'missing error code: {x}'

# Accessibility requirements (10.21): focus visibility and reduced-motion support must exist in CSS.
assert ':focus-visible' in c
assert 'reduce-motion' in c

assert (r / 'server.py').exists()
print('SMOKE TEST PASS')
