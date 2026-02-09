"""Command-line interface for the claims processing agent."""

import argparse
import json
import sys
from pathlib import Path
from typing import Optional

from src.processor import ClaimProcessor


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Autonomous Insurance Claims Processing Agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process a single document
  python cli.py --file claim_document.txt

  # Process multiple documents
  python cli.py --folder ./claims/

  # Process with output file
  python cli.py --file claim.pdf --output result.json

  # Process and display result
  python cli.py --file claim.txt --display
        """,
    )

    parser.add_argument(
        "--file",
        type=str,
        help="Path to a single claim document",
    )
    parser.add_argument(
        "--folder",
        type=str,
        help="Path to folder containing multiple claim documents",
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Output file path for results (JSON)",
    )
    parser.add_argument(
        "--display",
        action="store_true",
        help="Display results in console",
    )
    parser.add_argument(
        "--format",
        choices=["json", "pretty"],
        default="json",
        help="Output format (default: json)",
    )

    args = parser.parse_args()

    # Validate arguments
    if not args.file and not args.folder:
        parser.print_help()
        print("\nError: Please provide either --file or --folder", file=sys.stderr)
        sys.exit(1)

    # Initialize processor
    processor = ClaimProcessor()

    # Process documents
    if args.file:
        results = process_single_file(processor, args.file, args)
    else:
        results = process_folder(processor, args.folder, args)

    # Handle output
    if args.display:
        display_results(results, args.format)

    if args.output:
        save_results(results, args.output)
        print(f"\n✓ Results saved to: {args.output}")

    if not args.display and not args.output:
        display_results(results, args.format)


def process_single_file(processor: ClaimProcessor, file_path: str, args) -> list:
    """Process a single file."""
    try:
        print(f"Processing: {file_path}...")
        result = processor.process_file(file_path)
        print(f"✓ Successfully processed: {file_path}")
        return [result]
    except FileNotFoundError:
        print(f"Error: File not found: {file_path}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error processing {file_path}: {str(e)}", file=sys.stderr)
        sys.exit(1)


def process_folder(processor: ClaimProcessor, folder_path: str, args) -> list:
    """Process all documents in a folder."""
    try:
        folder = Path(folder_path)
        if not folder.exists():
            print(f"Error: Folder not found: {folder_path}", file=sys.stderr)
            sys.exit(1)

        # Find all relevant files
        file_patterns = ["*.txt", "*.pdf", "*.md"]
        files = []
        for pattern in file_patterns:
            files.extend(folder.glob(pattern))

        if not files:
            print(f"Error: No claim documents found in: {folder_path}", file=sys.stderr)
            sys.exit(1)

        print(f"Found {len(files)} claim document(s)")
        results = processor.process_batch([str(f) for f in files])
        print(f"✓ Successfully processed {len(results)} document(s)")
        return results
    except Exception as e:
        print(f"Error processing folder: {str(e)}", file=sys.stderr)
        sys.exit(1)


def display_results(results: list, format: str = "json") -> None:
    """Display results to console."""
    print("\n" + "=" * 80)
    print("CLAIM PROCESSING RESULTS")
    print("=" * 80 + "\n")

    for i, result in enumerate(results, 1):
        print(f"--- Claim #{i} ---")
        if format == "pretty":
            display_result_pretty(result)
        else:
            print(json.dumps(result.to_json_dict(), indent=2))
        print()


def display_result_pretty(result) -> None:
    """Display result in pretty format."""
    print(f"Recommended Route: {result.recommended_route.upper()}")
    print(f"Confidence Score: {result.confidence_score:.1%}")
    print(f"\nReasoning: {result.routing_reasoning}")

    if result.flags:
        print(f"\nFlags Raised:")
        for flag in result.flags:
            print(f"  • {flag}")

    print(f"\nMissing Fields ({len(result.missing_fields)}):")
    if result.missing_fields:
        for field in result.missing_fields:
            print(f"  ⚠  {field}")
    else:
        print("  ✓ All mandatory fields present")

    print(f"\nExtracted Fields Summary:")
    extracted = result.extracted_fields
    if extracted.get("policy_info", {}).get("policy_number"):
        print(f"  Policy: {extracted['policy_info']['policy_number']}")
    if extracted.get("policy_info", {}).get("policyholder_name"):
        print(f"  Policyholder: {extracted['policy_info']['policyholder_name']}")
    if extracted.get("incident_info", {}).get("incident_date"):
        print(f"  Incident Date: {extracted['incident_info']['incident_date']}")
    if extracted.get("asset_details", {}).get("estimated_damage"):
        print(f"  Estimated Damage: ${extracted['asset_details']['estimated_damage']:,.2f}")


def save_results(results: list, output_path: str) -> None:
    """Save results to file."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    output = [result.to_json_dict() for result in results]

    with open(path, "w") as f:
        json.dump(output, f, indent=2)


if __name__ == "__main__":
    main()
