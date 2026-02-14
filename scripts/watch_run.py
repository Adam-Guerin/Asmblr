import argparse
import json
import time
from pathlib import Path

def read_run_state(run_dir: Path) -> dict | None:
    path = run_dir / 'run_state.json'
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except Exception:
        return None

def tail_progress(path: Path, offset: int) -> int:
    if not path.exists():
        return offset
    with path.open('r', encoding='utf-8', errors='ignore') as handle:
        handle.seek(offset)
        for line in handle:
            print(f'[progress] {line.rstrip()}')
        return handle.tell()

def format_state(state: dict) -> str:
    status = state.get('status', 'unknown')
    stage = state.get('stage', 'unknown')
    run_id = state.get('run_id', 'unknown')
    return f'status={status}, stage={stage}, run_id={run_id}'

def main() -> None:
    parser = argparse.ArgumentParser(description='Watch run_state and progress for completion')
    parser.add_argument('run_dir', type=Path, help='Path to the run directory')
    parser.add_argument('--poll-interval', type=float, default=5.0, help='Seconds between polls')
    args = parser.parse_args()
    run_dir = args.run_dir
    last_state = None
    last_offset = 0

    if not run_dir.exists():
        raise SystemExit(f'Run directory {run_dir} does not exist.')

    print('Watching', run_dir)
    try:
        while True:
            state = read_run_state(run_dir)
            if state and state != last_state:
                print('[state]', format_state(state))
                last_state = state
                if state.get('status') == 'completed':
                    print('Run completed at stage:', state.get('stage'))
                    break
            last_offset = tail_progress(run_dir / 'progress.log', last_offset)
            time.sleep(args.poll_interval)
    except KeyboardInterrupt:
        print('Interrupted.')

if __name__ == '__main__':
    main()
