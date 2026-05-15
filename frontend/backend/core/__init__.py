"""
Cyberdefence Platform v3.1 - Core Modules
Modular refactoring of scanning and analysis modules
"""

# Main scanning modules
from .recon import module_recon, clean_url, get_domain, save_db
from .vulnerability import module_vuln
from .defence import module_defence
from .siem import module_siem, generate_demo_events, SEVERITY_MAP
from .virustotal import module_virustotal
from .shodan import module_shodan
from .abuseipdb import module_abuseipdb

# Import get_latest from original monolith (not extracted to modules)
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from cyberdefence_platform_v31 import get_latest

__all__ = [
    # Main modules
    "module_recon",
    "module_vuln",
    "module_defence",
    "module_siem",
    "module_virustotal",
    "module_shodan",
    "module_abuseipdb",
    # Helper functions
    "clean_url",
    "get_domain",
    "save_db",
    "get_latest",
    "generate_demo_events",
    "SEVERITY_MAP",
]

__version__ = "3.1.0"
