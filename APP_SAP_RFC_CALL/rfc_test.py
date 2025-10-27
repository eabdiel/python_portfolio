"""
SAP SSO Team Connection & RFC Tester (Auto-Setup)
Author: Edwin Rodriguez (Arthrex IT SAP COE)
Date: 2025-10-22

Features
--------
✔ Auto-detects SSO user (Secure Login Client)
✔ Accepts both 'p:' and 'p/sapsso:' SNC partner formats
✔ Validates sapcrypto.dll bitness vs Python
✔ Auto-creates sap_sso_config.ini with default 'p/sapsso:CN=SMP'
✔ Tests connectivity (STFC_CONNECTION)
✔ Tests RFC_READ_TABLE on USR01 using the same SSO user
"""

import os, getpass, struct, configparser, platform
from pyrfc import (
    Connection,
    CommunicationError,
    LogonError,
    ABAPRuntimeError,
    ABAPApplicationError,
)

CONFIG_PATH = os.path.join(os.path.expanduser("~"), "sap_sso_config.ini")

# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------
def ensure_config():
    """Ensure sap_sso_config.ini exists or create silently with default."""
    cfg = configparser.ConfigParser()
    default_partner = "p/sapsso:CN=SMP"  # Arthrex SMP system
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


def detect_user_snc():
    """Derive SNC identity and user ID from Windows login."""
    user = getpass.getuser().upper()
    org_units = "OU=SLS, O=ARTHREX, C=US"
    snc = f"p:CN={user}, {org_units}"
    print(f"👤 Detected SNC identity: {snc}")
    return snc, user


def find_crypto_lib():
    """Locate 64-bit SecureLogin sapcrypto.dll."""
    paths = [
        r"C:\Program Files\SAP\FrontEnd\SecureLogin\lib\sapcrypto.dll",
        r"C:\Program Files\SAP\FrontEnd\SecureLoginLibrary\sapcrypto.dll",
    ]
    for p in paths:
        if os.path.exists(p):
            return p
    raise FileNotFoundError("⚠️ 64-bit sapcrypto.dll not found. "
                            "Ensure 64-bit Secure Login Client is installed.")


def check_dll_bitness(path):
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


def validate_environment(snc_partner, snc_lib):
    """Validate DLL bitness & SNC name syntax."""
    py_arch = platform.architecture()[0][:2]
    dll_arch = check_dll_bitness(snc_lib)
    print(f"🧠 Python arch: {py_arch}-bit | DLL arch: {dll_arch}-bit")

    if dll_arch != py_arch:
        raise EnvironmentError(
            f"❌ Architecture mismatch: Python {py_arch}-bit vs "
            f"sapcrypto.dll {dll_arch}-bit.\n→ Use matching 64-bit versions."
        )

    lower = snc_partner.lower()
    if not (lower.startswith("p/sapsso:cn=") or (lower.startswith("p:cn=") and "," in snc_partner)):
        raise ValueError(
            f"❌ Invalid SNC partner name '{snc_partner}'\n"
            f"→ Must be one of:\n"
            f"   • p/sapsso:CN=<SID>      (SecureLogin format)\n"
            f"   • p:CN=<server>, OU=SAP, O=ARTHREX, C=US  (X.509 format)"
        )

# ---------------------------------------------------------------------
# RFC Test: USR01 read
# ---------------------------------------------------------------------
def test_usr01(conn, user_id):
    """Simple RFC_READ_TABLE query on USR01 using current user ID."""
    print(f"\n📋 Checking USR01 for user '{user_id}' ...")
    try:
        result = conn.call(
            "RFC_READ_TABLE",
            QUERY_TABLE="USR01",
            DELIMITER="|",
            ROWCOUNT=5,
            OPTIONS=[{"TEXT": f"BNAME = '{user_id}'"}],
        )
        cols = [f["FIELDNAME"] for f in result["FIELDS"]]
        rows = [r["WA"].split("|") for r in result["DATA"]]
        if not rows:
            print("⚠️  No records found — verify user ID or RFC_READ_TABLE access.")
        else:
            for row in rows:
                print(dict(zip(cols, row)))
    except Exception as e:
        print(f"❌ RFC_READ_TABLE error: {e}")

# ---------------------------------------------------------------------
# Connection test
# ---------------------------------------------------------------------
def connect_sso(host="vartsmpapp1", sysnr="00", client="100"):
    cfg = ensure_config()
    snc_partner = cfg["SAP"]["snc_partnername"].strip()
    snc_myname, user_id = detect_user_snc()
    snc_lib = find_crypto_lib()

    validate_environment(snc_partner, snc_lib)

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

    print("\n🔗 Attempting SAP SSO connection...")
    try:
        conn = Connection(**params)
        print("✅ Connected successfully via SSO!")
        print(conn.call("STFC_CONNECTION"))
        test_usr01(conn, user_id)
    except (CommunicationError, LogonError) as e:
        print(f"❌ Communication/Logon Error:\n{e}")
    except (ABAPApplicationError, ABAPRuntimeError) as e:
        print(f"❌ ABAP Error:\n{e}")
    except Exception as e:
        print(f"❌ Unknown Error:\n{e}")

# ---------------------------------------------------------------------
if __name__ == "__main__":
    print("=== SAP PyRFC Team SSO Tester (Auto-Setup) ===")
    try:
        connect_sso("vartsmpapp1", "00", "100")
    except Exception as e:
        print(f"\n💡 Pre-check failed:\n{e}")
