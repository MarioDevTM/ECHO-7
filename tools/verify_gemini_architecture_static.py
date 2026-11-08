"""Compatibility entry point for verifying the Gemini architectural cleanup build."""
from pathlib import Path
import runpy
runpy.run_path(str(Path(__file__).with_name('verify_cleanup_integration.py')), run_name='__main__')
