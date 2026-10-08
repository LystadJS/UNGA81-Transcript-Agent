"""Offline synthetic diagnostic export; no production-corpus or network access."""
import argparse
import json
from pathlib import Path

from fixtures import make_panel
from framework import compare, to_interchange_v1, write_exports


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True, help='New directory; overwrite prohibited')
    parser.add_argument('--motion', action='store_true', help='Known fictional target movement')
    parser.add_argument('--no-roster-change', action='store_true')
    parser.add_argument('--reference-map', action='store_true', help='Pinned transform, no alignment')
    parser.add_argument('--seed', type=int, default=30092026)
    args = parser.parse_args()
    panel = make_panel(motion=args.motion, roster=not args.no_roster_change,
                       fit_policy='transformed_reference' if args.reference_map else 'full_refit')
    result = compare(panel, 'p0', 'p1', anchor_ids=[f'A{i}' for i in range(6)], bootstrap_seed=args.seed)
    envelope = to_interchange_v1(panel, result)
    paths = write_exports(args.output, result, envelope)
    print(json.dumps({'schema': result['schema'], 'files': paths,
                      'within_actor_change': result['high_dimensional']['mean_within_actor_distance'],
                      'roster_sensitive_population_change': result['high_dimensional']['all_actor_centroid_distance'],
                      'uncertainty': result['uncertainty']['status'], 'publication_eligible': False}, indent=2))


if __name__ == '__main__':
    main()
