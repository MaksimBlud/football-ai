"""Read-only, aggregate-only product model/market benchmark, never a strategy."""
import argparse
import json

from product_market_benchmark import build_product_market_benchmark
from report_product_reliability import fetch_lifecycle_events


def main() -> None:
    cli = argparse.ArgumentParser(description="EPL frozen-model vs paired non-closing market benchmark")
    cli.add_argument("--model-sha256", required=True,
                     help="Exact frozen 1X2 model SHA256 (never pool artifacts)")
    args = cli.parse_args()
    from database import supabase

    events = fetch_lifecycle_events(supabase)
    report = build_product_market_benchmark(
        events, league="EPL", model_sha256=args.model_sha256
    )
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    print("PASS: READ-ONLY PRODUCT 1X2 MODEL/MARKET BENCHMARK COMPLETE")


if __name__ == "__main__":
    main()
