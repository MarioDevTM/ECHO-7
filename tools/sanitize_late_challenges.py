"""Make unplaytested late-game service additions non-blocking.

The previous remodeling scripts created 55 extra mandatory door conditions based
only on schema checks. Until a real playthrough has established reachability,
those conditions are unsafe to use as campaign gates. Preserve all geometry and
interactive side challenges as optional exploration, with an optional log reward.
The original authored exit dependencies remain authoritative.

Idempotent: only this script can safely follow the old late-game generators.
"""
from __future__ import annotations
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
LEVELS = ROOT / 'data' / 'levels'
BASE = json.loads((ROOT / 'docs' / 'BASELINE_ARCHIVE_FINGERPRINTS.json').read_text())


def sanitize(n: int) -> dict:
    path = LEVELS / f'level_{n:02}.json'
    data = json.loads(path.read_text(encoding='utf-8'))
    original_links = BASE['late_game'][str(n)]['doors'][0]['required_links']
    final_door = data['doors'][0]
    added = [s for s in final_door['required_links'] if s not in original_links]
    optional = added or data.get('side_challenge_policy', {}).get('optional_signals', [])
    final_door['required_links'] = list(original_links)
    extra_signals = set(added)
    data['hint_route'] = [s for s in data.get('hint_route', []) if s not in extra_signals]
    for s in added:
        data.get('hint_notes', {}).pop(s, None)
    data['solution_steps'] = [s for s in data.get('solution_steps', [])
                              if 'SERVICE DETOUR' not in s.upper() and
                              'upper validation' not in s.lower() and
                              'auxiliary feeder' not in s.lower() and
                              'elevated service' not in s.lower() and
                              'elevated diagnostics' not in s.lower() and
                              'isolation valve' not in s.lower() and
                              'record its new state' not in s.lower() and
                              'upper inspection' not in s.lower()]
    if ' // SERVICE DETOUR:' in data.get('subtitle', ''):
        data['subtitle'] = data['subtitle'].split(' // SERVICE DETOUR:')[0].rstrip()
    side = data.get('secondary_validation_1', {})
    side_sig = side.get('signal') or f'sector_{n:02}_validated'
    relay = next((r for r in data.get('latching_relays', []) if r['link_id'] == side_sig), None)
    if relay is not None:
        log_id = f'service_challenge_{n:02}'
        if not any(o['id'] == log_id for o in data.get('collectibles', [])):
            data.setdefault('collectibles', []).append({
                'id': log_id,
                'x': relay['x'] + 12,
                'y': relay['y'] - 42,
                'title': f'Optional Diagnostics {n:02}',
                'text': 'Optional master circuit cleared. The standard exit never depends on this side challenge.',
                'required_links': [side_sig],
                'optional_investigation': True,
            })
    data['side_challenge_policy'] = {
        'campaign_blocking': False,
        'optional_signals': optional,
        'reason': 'Not proven traversable in the Pygame engine; preserve main progression.',
    }
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    return {'level': n, 'removed_unverified_exit_prerequisites': optional,
            'original_exit_prerequisites': original_links}


def main():
    summary = [sanitize(n) for n in range(25, 80)]
    (ROOT / 'docs' / 'OPTIONAL_CHALLENGE_SAFETY_REPORT.json').write_text(
        json.dumps(summary, indent=2) + '\n', encoding='utf-8')
    print(f'Converted unverified gate extensions to optional tasks in {len(summary)} levels.')


if __name__ == '__main__':
    main()
