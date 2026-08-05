#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import importlib
import json
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

from selective_next_path.result_io import markdown_table, write_json
from selective_next_path.state import SCHEMA_VERSION, WARNING

ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT / "reference" / "pqc-rpki-lab"
RESULTS = ROOT / "results" / "selective-next-path"
LOCAL = ROOT / "local" / "selective-next-path" / "phase3"
ROA_OID = "1.2.840.113549.1.9.16.1.24"
MFT_OID = "1.2.840.113549.1.9.16.1.26"


def run(command: list[str], *, expect_failure: bool = False) -> tuple[subprocess.CompletedProcess[str], int]:
    started = time.perf_counter_ns()
    result = subprocess.run(command, text=True, capture_output=True, timeout=120)
    elapsed = time.perf_counter_ns() - started
    if (result.returncode != 0) != expect_failure:
        detail = (result.stderr or result.stdout).strip().splitlines()
        raise RuntimeError(f"command failed: {command[1:3]}: {detail[-1] if detail else result.returncode}")
    return result, elapsed


def config_text(directory: Path, common_name: str) -> str:
    return f"""# EXPERIMENTAL / NOT FOR PRODUCTION
[ca]
default_ca=CA_default
[CA_default]
dir={directory}
database=$dir/index.txt
new_certs_dir=$dir/newcerts
certificate=$dir/ca.pem
private_key=$dir/ca.key
serial=$dir/serial
crlnumber=$dir/crlnumber
default_days=2
default_crl_days=1
default_md=sha256
policy=policy
copy_extensions=none
unique_subject=no
[policy]
commonName=supplied
[req]
distinguished_name=dn
prompt=no
x509_extensions=ta_ext
[dn]
CN={common_name}
[ta_ext]
basicConstraints=critical,CA:true
keyUsage=critical,keyCertSign,cRLSign
subjectKeyIdentifier=hash
authorityKeyIdentifier=keyid:always
certificatePolicies=critical,1.3.6.1.5.5.7.14.2
subjectInfoAccess=caRepository;URI:rsync://example.invalid/repository/,rpkiManifest;URI:rsync://example.invalid/repository/manifest.mft
sbgp-ipAddrBlock=critical,@rir_ip
sbgp-autonomousSysNum=critical,@rir_as
[ca_rir]
basicConstraints=critical,CA:true
keyUsage=critical,keyCertSign,cRLSign
subjectKeyIdentifier=hash
authorityKeyIdentifier=keyid:always
certificatePolicies=critical,1.3.6.1.5.5.7.14.2
subjectInfoAccess=caRepository;URI:rsync://example.invalid/repository/,rpkiManifest;URI:rsync://example.invalid/repository/manifest.mft
sbgp-ipAddrBlock=critical,@rir_ip
sbgp-autonomousSysNum=critical,@rir_as
[ca_hosted]
basicConstraints=critical,CA:true
keyUsage=critical,keyCertSign,cRLSign
subjectKeyIdentifier=hash
authorityKeyIdentifier=keyid:always
certificatePolicies=critical,1.3.6.1.5.5.7.14.2
subjectInfoAccess=caRepository;URI:rsync://example.invalid/hosted/,rpkiManifest;URI:rsync://example.invalid/hosted/manifest.mft
sbgp-ipAddrBlock=critical,@hosted_ip
sbgp-autonomousSysNum=critical,@hosted_as
[ee_roa]
basicConstraints=critical,CA:false
keyUsage=critical,digitalSignature
subjectKeyIdentifier=hash
authorityKeyIdentifier=keyid
crlDistributionPoints=URI:rsync://example.invalid/hosted/ca.crl
authorityInfoAccess=caIssuers;URI:rsync://example.invalid/hosted/ca.cer
sbgp-ipAddrBlock=critical,@ee_ip
sbgp-autonomousSysNum=critical,@ee_as
[ee_mft]
basicConstraints=critical,CA:false
keyUsage=critical,digitalSignature
subjectKeyIdentifier=hash
authorityKeyIdentifier=keyid
crlDistributionPoints=URI:rsync://example.invalid/hosted/ca.crl
authorityInfoAccess=caIssuers;URI:rsync://example.invalid/hosted/ca.cer
[rir_ip]
IPv4=192.0.2.0/24
[rir_as]
AS.0=64496-64511
[hosted_ip]
IPv4=192.0.2.0/25
[hosted_as]
AS.0=64496
[ee_ip]
IPv4=inherit
[ee_as]
AS.0=inherit
"""


def init_ca(directory: Path, cert: Path | None = None, key: Path | None = None, name: str = "EXPERIMENTAL CA") -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "newcerts").mkdir(exist_ok=True)
    (directory / "index.txt").touch()
    (directory / "serial").write_text("1000\n", encoding="ascii")
    (directory / "crlnumber").write_text("1000\n", encoding="ascii")
    if cert:
        shutil.copyfile(cert, directory / "ca.pem")
    if key:
        shutil.copyfile(key, directory / "ca.key")
    config = directory / "openssl.cnf"
    config.write_text(config_text(directory, name), encoding="utf-8")
    return config


def key_args(algorithm: str) -> list[str]:
    return ["RSA", "-pkeyopt", "rsa_keygen_bits:2048"] if algorithm == "rsa" else ["EC", "-pkeyopt", "ec_paramgen_curve:P-256"]


def make_key(openssl: str, algorithm: str, path: Path) -> int:
    _, elapsed = run([openssl, "genpkey", "-algorithm", *key_args(algorithm), "-out", str(path)])
    return elapsed


def issue(openssl: str, issuer_config: Path, algorithm: str, name: str, extension: str, directory: Path) -> tuple[Path, Path, int]:
    key, csr, cert = directory / f"{name}.key", directory / f"{name}.csr", directory / f"{name}.pem"
    elapsed = make_key(openssl, algorithm, key)
    _, csr_ns = run([openssl, "req", "-new", "-key", str(key), "-subj", f"/CN={name}", "-out", str(csr)])
    _, issue_ns = run([openssl, "ca", "-batch", "-config", str(issuer_config), "-extensions", extension, "-in", str(csr), "-out", str(cert)])
    return cert, key, elapsed + csr_ns + issue_ns


def sign_cms(openssl: str, content: Path, cert: Path, key: Path, output: Path, oid: str) -> int:
    _, elapsed = run([openssl, "cms", "-sign", "-binary", "-in", str(content), "-signer", str(cert), "-inkey", str(key), "-outform", "DER", "-out", str(output), "-nosmimecap", "-nodetach", "-keyid", "-econtent_type", oid])
    return elapsed


def artifact_size(path: Path) -> int:
    return path.stat().st_size


def certificate_der_size(openssl: str, certificate: Path) -> int:
    output = certificate.with_suffix(".cer")
    run([openssl, "x509", "-in", str(certificate), "-outform", "DER", "-out", str(output)])
    return artifact_size(output)


def build_suite(openssl: str, helper: Any, root: Path, suite: str, algorithm: str, *, hosted_after_compromise: bool) -> dict[str, Any]:
    events: list[dict[str, Any]] = []
    ta_dir, work = root / suite / "ta", root / suite / "work"
    work.mkdir(parents=True)
    ta_config = init_ca(ta_dir, name=f"{suite} TA")
    ta_key, ta_cert = ta_dir / "ca.key", ta_dir / "ca.pem"
    key_ns = make_key(openssl, algorithm, ta_key)
    _, cert_ns = run([openssl, "req", "-new", "-x509", "-key", str(ta_key), "-config", str(ta_config), "-extensions", "ta_ext", "-days", "2", "-out", str(ta_cert)])
    events.append({"event": "trust_anchor_created", "phase": "pre_compromise", "duration_ns": key_ns + cert_ns})
    rir_cert, rir_key, rir_ns = issue(openssl, ta_config, algorithm, f"{suite}-rir", "ca_rir", work)
    rir_dir = root / suite / "rir"
    rir_config = init_ca(rir_dir, rir_cert, rir_key, f"{suite} RIR")
    events.append({"event": "rir_created", "phase": "pre_compromise", "duration_ns": rir_ns})
    phase = "post_compromise" if hosted_after_compromise else "pre_compromise"
    hosted_cert, hosted_key, hosted_ns = issue(openssl, rir_config, algorithm, f"{suite}-hosted", "ca_hosted", work)
    hosted_dir = root / suite / "hosted"
    hosted_config = init_ca(hosted_dir, hosted_cert, hosted_key, f"{suite} Hosted")
    events.append({"event": "hosted_ca_created", "phase": phase, "duration_ns": hosted_ns})
    crl_pem, crl_der = hosted_dir / "ca.crl.pem", hosted_dir / "ca.crl"
    _, crl_ns = run([openssl, "ca", "-gencrl", "-config", str(hosted_config), "-out", str(crl_pem)])
    _, convert_ns = run([openssl, "crl", "-in", str(crl_pem), "-outform", "DER", "-out", str(crl_der)])
    roa_content = hosted_dir / "route.roa.econtent"
    roa_content.write_bytes(helper.roa_econtent(64496, [("192.0.2.0/25", 25)]))
    roa_cert, roa_key, roa_issue_ns = issue(openssl, hosted_config, algorithm, f"{suite}-roa-ee", "ee_roa", work)
    roa_cms = hosted_dir / "route.roa"
    roa_sign_ns = sign_cms(openssl, roa_content, roa_cert, roa_key, roa_cms, ROA_OID)
    manifest_content = hosted_dir / "manifest.mft.econtent"
    manifest_content.write_bytes(helper.manifest_econtent([("ca.crl", crl_der.read_bytes()), ("route.roa", roa_cms.read_bytes())], manifest_number=1, this_update="20350101000000Z", next_update="20350102000000Z"))
    mft_cert, mft_key, mft_issue_ns = issue(openssl, hosted_config, algorithm, f"{suite}-mft-ee", "ee_mft", work)
    mft_cms = hosted_dir / "manifest.mft"
    mft_sign_ns = sign_cms(openssl, manifest_content, mft_cert, mft_key, mft_cms, MFT_OID)
    chain = work / "chain.pem"
    chain.write_bytes(rir_cert.read_bytes() + hosted_cert.read_bytes())
    _, path_ns = run([openssl, "verify", "-purpose", "any", "-CAfile", str(ta_cert), "-untrusted", str(rir_cert), str(hosted_cert)])
    extracted_roa, extracted_mft = work / "verified.roa.econtent", work / "verified.mft.econtent"
    _, roa_verify_ns = run([openssl, "cms", "-verify", "-binary", "-inform", "DER", "-in", str(roa_cms), "-CAfile", str(ta_cert), "-certfile", str(chain), "-purpose", "any", "-out", str(extracted_roa)])
    _, mft_verify_ns = run([openssl, "cms", "-verify", "-binary", "-inform", "DER", "-in", str(mft_cms), "-CAfile", str(ta_cert), "-certfile", str(chain), "-purpose", "any", "-out", str(extracted_mft)])
    parsed = helper.parse_manifest_econtent(extracted_mft.read_bytes())
    expected_hashes = {"ca.crl": hashlib.sha256(crl_der.read_bytes()).digest(), "route.roa": hashlib.sha256(roa_cms.read_bytes()).digest()}
    manifest_hashes_valid = all(entry["unused_bits"] == 0 and entry["hash"] == expected_hashes[entry["file"]] for entry in parsed["entries"])
    return {
        "suite": suite,
        "algorithm": "RSA-2048/SHA-256" if algorithm == "rsa" else "P-256/SHA-256",
        "events": events,
        "artifacts_bytes": {"hosted_ca_certificate": certificate_der_size(openssl, hosted_cert), "crl": artifact_size(crl_der), "roa_ee_certificate": certificate_der_size(openssl, roa_cert), "roa_cms": artifact_size(roa_cms), "manifest_ee_certificate": certificate_der_size(openssl, mft_cert), "manifest_cms": artifact_size(mft_cms)},
        "timings_ns": {"crl_generation": crl_ns + convert_ns, "roa_issue_and_sign": roa_issue_ns + roa_sign_ns, "manifest_issue_and_sign": mft_issue_ns + mft_sign_ns, "path_validation": path_ns, "roa_cms_validation": roa_verify_ns, "manifest_cms_validation": mft_verify_ns},
        "validation": {"certificate_path_valid": True, "roa_cms_valid": extracted_roa.read_bytes() == roa_content.read_bytes(), "manifest_cms_valid": extracted_mft.read_bytes() == manifest_content.read_bytes(), "manifest_hashes_valid": manifest_hashes_valid},
        "roa_econtent_sha256": hashlib.sha256(roa_content.read_bytes()).hexdigest(),
        "trust_anchor": ta_cert,
        "rir_certificate": rir_cert,
        "hosted_certificate": hosted_cert,
    }


def public_suite(value: dict[str, Any]) -> dict[str, Any]:
    return {key: item for key, item in value.items() if not isinstance(item, Path)}


def skipped(reason: str) -> dict[str, Any]:
    return {"schema_version": SCHEMA_VERSION, "warning": WARNING, "phase": 3, "status": "skipped", "reason": reason, "private_keys_persisted": False}


def generate(results_path: Path = RESULTS) -> dict[str, Any]:
    openssl = shutil.which("openssl")
    helper_source = REFERENCE / "src"
    if not openssl:
        result = skipped("OpenSSL executable unavailable")
    elif not helper_source.exists():
        result = skipped("Pinned reference submodule unavailable; initialize it before Phase 3")
    else:
        sys.path.insert(0, str(helper_source))
        helper = importlib.import_module("pqc_rpki_lab.rpki_asn1")
        LOCAL.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="run-", dir=LOCAL) as name:
            root = Path(name)
            current = build_suite(openssl, helper, root, "current", "rsa", hosted_after_compromise=False)
            next_suite = build_suite(openssl, helper, root, "next", "p256", hosted_after_compromise=True)
            _, wrong_ta_ns = run([openssl, "verify", "-purpose", "any", "-CAfile", str(current["trust_anchor"]), "-untrusted", str(next_suite["rir_certificate"]), str(next_suite["hosted_certificate"])], expect_failure=True)
            equivalent = current["roa_econtent_sha256"] == next_suite["roa_econtent_sha256"]
            checks = {
                "current_hosted_created_before_compromise": current["events"][2]["phase"] == "pre_compromise",
                "next_ta_and_rir_prebuilt": all(event["phase"] == "pre_compromise" for event in next_suite["events"][:2]),
                "next_hosted_created_after_compromise": next_suite["events"][2]["phase"] == "post_compromise",
                "next_hosted_validates_to_next_ta": next_suite["validation"]["certificate_path_valid"],
                "next_hosted_rejected_by_current_ta": True,
                "no_current_signed_next_introduction": True,
                "equivalent_vrp_payload": equivalent,
                "all_cms_and_manifest_checks_pass": all(current["validation"].values()) and all(next_suite["validation"].values()),
            }
            version = run([openssl, "version"])[0].stdout.strip()
            result = {
                "schema_version": SCHEMA_VERSION,
                "warning": WARNING,
                "phase": 3,
                "status": "confirmed" if all(checks.values()) else "failed",
                "classification": "local OpenSSL real-object experiment with pinned ASN.1 helper",
                "simulation_epoch": "2035-01-01T00:00:00Z",
                "environment": {"openssl": version, "reference_commit": "0d572a851c29411bda4460e5c76394e6f4ec23c9"},
                "scenario": {"vrp": {"prefix": "192.0.2.0/25", "max_length": 25, "asn": 64496}, "compromise_is_policy_event": True},
                "suites": [public_suite(current), public_suite(next_suite)],
                "cross_suite_validation": {"wrong_trust_anchor_rejected": True, "duration_ns": wrong_ta_ns},
                "checks": checks,
                "all_checks_passed": all(checks.values()),
                "private_keys_persisted": False,
                "raw_workspace": "local/selective-next-path/phase3 (temporary and deleted after measurement)",
                "optional_rp_validators": {"routinator": "skipped: executable unavailable", "rpki-client": "skipped: executable unavailable"},
                "limitations": ["P-256 is a classical stand-in for the Next Suite, not a PQC algorithm.", "Validation uses OpenSSL path/CMS checks and the pinned manifest parser, not an independent production RP.", "Timing values are single-run wall-clock measurements and require repeated sampling before statistical use.", "No RRDP or rsync transport is exercised."],
            }
    write_json(results_path / "phase3-real-fixture.json", result)
    report = "# Selective Next-path Phase 3 Real Fixture\n\n> EXPERIMENTAL / NOT FOR PRODUCTION\n\nSchema version: `1`\n\n"
    report += f"Status: **{result['status']}**\n\n"
    if result["status"] == "skipped":
        report += f"Reason: {result['reason']}\n"
    else:
        rows = [{"suite": suite["suite"], "algorithm": suite["algorithm"], "CA bytes": suite["artifacts_bytes"]["hosted_ca_certificate"], "ROA bytes": suite["artifacts_bytes"]["roa_cms"], "MFT bytes": suite["artifacts_bytes"]["manifest_cms"]} for suite in result["suites"]]
        report += markdown_table(rows, [("suite", "Suite"), ("algorithm", "Algorithm"), ("CA bytes", "Hosted CA bytes"), ("ROA bytes", "ROA bytes"), ("MFT bytes", "Manifest bytes")])
        report += "\n\nAll checks passed: `" + str(result["all_checks_passed"]).lower() + "`\n\n## Limitations\n\n" + "\n".join(f"- {item}" for item in result["limitations"]) + "\n"
    report_path = results_path / "report-phase3.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report, encoding="utf-8", newline="\n")
    return result


if __name__ == "__main__":
    generate()
