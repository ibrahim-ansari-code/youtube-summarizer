#!/usr/bin/env python
import argparse
import os
import sys
import inspect
from dotenv import load_dotenv

# Ensure package imports work when running as a script
_current_file = inspect.getfile(inspect.currentframe())
_current_dir = os.path.dirname(os.path.abspath(_current_file))
_parent_dir = os.path.dirname(_current_dir)
sys.path.insert(0, _parent_dir)

from crew import YouTubeSummarizer

load_dotenv()


def main():
    parser = argparse.ArgumentParser(
        description="Summarize a YouTube video and optionally publish to Google Docs"
    )
    parser.add_argument("--url", required=True, help="YouTube video URL")
    parser.add_argument(
        "--lang",
        default=None,
        help="Preferred transcript language code (e.g., en, es, fr). Defaults to best available.",
    )
    parser.add_argument(
        "--gdocs",
        action="store_true",
        help="If set, publish the approved summary to Google Docs",
    )
    parser.add_argument(
        "--title",
        default=None,
        help="Optional Google Docs title to use when publishing",
    )

    args = parser.parse_args()

    inputs = {
        "youtube_url": args.url,
        "language": args.lang,
        "publish_to_gdocs": args.gdocs,
        "gdocs_title": args.title,
    }

    print("Starting summarization pipeline...")
    crew = YouTubeSummarizer().crew()
    crew.kickoff(inputs=inputs)

    print("Done. Outputs:")
    print("- transcript.md (raw transcript)")
    print("- SUMMARY.md (approved summary)")
    if args.gdocs:
        print("- Google Doc created (see task output for URL)")


if __name__ == "__main__":
    main()

