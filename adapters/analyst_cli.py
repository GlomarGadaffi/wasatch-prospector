import os
import sys
import argparse
import logging
from adapters.analyst import MirkwoodAnalyst

# Configure logging
logging.basicConfig(
    level=logging.WARNING, # Keep it clean for terminal outputs
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)


def print_table(results: list):
    """Gorgeously prints structured rows in a clean ASCII terminal format."""
    if not results:
        print("\n[ No results returned by the query ]")
        return
        
    keys = list(results[0].keys())
    # Determine max width for each column
    col_widths = {k: len(k) for k in keys}
    for row in results:
        for k in keys:
            val_str = str(row[k])
            if len(val_str) > col_widths[k]:
                col_widths[k] = len(val_str)

    # Clean up very long columns
    for k in col_widths:
        if col_widths[k] > 40:
            col_widths[k] = 40

    # Print header
    header_str = " | ".join(k.ljust(col_widths[k])[:col_widths[k]] for k in keys)
    separator = "-+-".join("-" * col_widths[k] for k in keys)
    print("\n" + header_str)
    print(separator)

    # Print rows
    for row in results:
        row_cells = []
        for k in keys:
            val_str = str(row[k]).replace("\n", " ")
            if len(val_str) > col_widths[k]:
                val_str = val_str[:col_widths[k] - 3] + "..."
            row_cells.append(val_str.ljust(col_widths[k]))
        print(" | ".join(row_cells))
    print(f"\n[ Returned {len(results)} rows ]\n")


def main():
    parser = argparse.ArgumentParser(description="Mirkwood AI Analyst - Natural Language to SQL CLI Engine")
    parser.add_argument("question", type=str, help="Natural language question to query against Mirkwood fused logs")
    parser.add_argument("--db", type=str, default="mirkwood.db", help="Path to Mirkwood SQLite database file")
    args = parser.parse_args()

    # Ensure API Key is present
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        print("Error: Missing Gemini API Key.", file=sys.stderr)
        print("Please set the GEMINI_API_KEY or GOOGLE_API_KEY environment variable.", file=sys.stderr)
        print("Example: export GEMINI_API_KEY=\"AIzaSy...\"", file=sys.stderr)
        sys.exit(1)

    print("-" * 70)
    print(f"Mirkwood AI Analyst - Query: '{args.question}'")
    print("-" * 70)

    try:
        analyst = MirkwoodAnalyst(args.db, api_key)
        res = analyst.query(args.question)
        
        if not res["success"]:
            print(f"\nFailed to execute query: {res['error']}", file=sys.stderr)
            if res.get("sql"):
                print(f"Generated SQL: {res['sql']}", file=sys.stderr)
            sys.exit(1)
            
        print(f"SQL GENERATED:\n  {res['sql']}")
        print("\nQUERY RESULTS:")
        print_table(res["results"])
        
    except Exception as e:
        print(f"\nAn error occurred: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
