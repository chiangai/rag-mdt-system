import logging

from app.agents import embedding
from config.settings import settings


def test_tls_verify_default_true():
    original_verify = settings.llm.ark_ssl_verify
    original_bundle = settings.llm.ark_ca_bundle
    try:
        settings.llm.ark_ssl_verify = True
        settings.llm.ark_ca_bundle = ""
        assert embedding._resolve_tls_verify() is True
    finally:
        settings.llm.ark_ssl_verify = original_verify
        settings.llm.ark_ca_bundle = original_bundle


def test_tls_verify_uses_ca_bundle():
    original_verify = settings.llm.ark_ssl_verify
    original_bundle = settings.llm.ark_ca_bundle
    try:
        settings.llm.ark_ssl_verify = True
        settings.llm.ark_ca_bundle = "C:/certs/custom-ca.pem"
        assert embedding._resolve_tls_verify() == "C:/certs/custom-ca.pem"
    finally:
        settings.llm.ark_ssl_verify = original_verify
        settings.llm.ark_ca_bundle = original_bundle


def test_tls_verify_false_logs_warning(caplog):
    original_verify = settings.llm.ark_ssl_verify
    original_bundle = settings.llm.ark_ca_bundle
    try:
        settings.llm.ark_ssl_verify = False
        settings.llm.ark_ca_bundle = ""
        with caplog.at_level(logging.WARNING):
            assert embedding._resolve_tls_verify() is False
        assert "SSL verification is disabled" in caplog.text
    finally:
        settings.llm.ark_ssl_verify = original_verify
        settings.llm.ark_ca_bundle = original_bundle
