"""
sap_connector.py  –  Arthrex SAP SSO connector for PyRFC
Author: Edwin Rodriguez (Arthrex IT SAP COE)
Date: 2025-10-22

Usage:
    from sap_connector import connect_sso
    conn = connect_sso()   # returns a live PyRFC Connection via SSO
"""

import os, getpass, struct, configparser, platform
from pyrfc import Connection

CONFIG_PATH = os.path.join(os.path.expanduser("~"), "sap_sso_config.ini")


# ---------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------
def _ensure_config():
    """Ensure sap_sso_config.ini exists or create silently with default partner."""
    cfg = configparser.ConfigParser()
    default_partner = "p/sapsso:CN=SMP"  # Arthrex default SAP SecureLogin identity
    if os.path.exists(CONFIG_PATH):
        cfg.read(CONFIG_PATH)
    if "SAP" not in cfg:
        cfg["SAP"] = {}
    if not cfg["SAP"].get("snc_partnername"):
        cfg["SAP"]["snc_partnername"] = default_partner
        with open(CONFIG_PATH, "w") as f:
            cfg.write(f)
        print(f"✅ Using default partner SNC '{default_partner}' "
              f"and created {CONFIG_PATH}")
    return cfg


def _detect_user_snc():
    """Return (snc_name, user_id) for current Windows user."""
    user = getpass.getuser().upper()
    org_units = "OU=SLS, O=ARTHREX, C=US"
    return f"p:CN={user}, {org_units}", user


def _find_crypto_lib():
    """Locate 64-bit SecureLogin sapcrypto.dll."""
    paths = [
        r"C:\Program Files\SAP\FrontEnd\SecureLogin\lib\sapcrypto.dll",
        r"C:\Program Files\SAP\FrontEnd\SecureLoginLibrary\sapcrypto.dll",
    ]
    for p in paths:
        if os.path.exists(p):
            return p
    raise FileNotFoundError("64-bit sapcrypto.dll not found. "
                            "Ensure 64-bit Secure Login Client is installed.")


def _check_dll_bitness(path):
    """Inspect DLL PE header for bitness."""
    with open(path, "rb") as f:
        f.seek(0x3C)
        pe_offset = struct.unpack("<I", f.read(4))[0]
        f.seek(pe_offset + 4)
        machine = struct.unpack("<H", f.read(2))[0]
        if machine == 0x8664:
            return "64"
        elif machine == 0x14C:
            return "32"
        return "Unknown"


def _validate_env(snc_partner, snc_lib):
    """Validate architecture and SNC partner format."""
    py_arch = platform.architecture()[0][:2]
    dll_arch = _check_dll_bitness(snc_lib)
    if dll_arch != py_arch:
        raise EnvironmentError(
            f"Architecture mismatch: Python {py_arch}-bit vs sapcrypto.dll {dll_arch}-bit."
        )

    lower = snc_partner.lower()
    if not (lower.startswith("p/sapsso:cn=")
            or (lower.startswith("p:cn=") and "," in snc_partner)):
        raise ValueError(
            f"Invalid SNC partner name '{snc_partner}'. "
            "Must be p/sapsso:CN=<SID> or full X.509 p:CN=<server>,OU=SAP,..."
        )


# ---------------------------------------------------------------------
# Public connector
# ---------------------------------------------------------------------
def connect_sso(host="vartsmpapp1", sysnr="00", client="100"):
    """
    Establish an SSO connection to SAP via Secure Login Client.
    Returns a live pyrfc.Connection object.
    """
    cfg = _ensure_config()
    snc_partner = cfg["SAP"]["snc_partnername"].strip()
    snc_myname, user_id = _detect_user_snc()
    snc_lib = _find_crypto_lib()
    _validate_env(snc_partner, snc_lib)

    params = dict(
        ashost=host,
        sysnr=sysnr,
        client=client,
        lang="EN",
        snc_mode="1",
        snc_qop="9",
        snc_lib=snc_lib,
        snc_partnername=snc_partner,
        snc_myname=snc_myname,
    )

    print(f"🔗 Connecting to SAP ({host}) as {user_id} via SSO ...")
    conn = Connection(**params)
    print("✅ SAP SSO connection established.")
    return conn
