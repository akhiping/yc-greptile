"""Extract agent claims and check them against independent evidence.

The OpenAI call is deliberately an adapter rather than part of the verdict
logic. Deterministic findings are applied first; only claims without a
deterministic answer are sent to the model. If the API is unavailable, the
last successful extraction is read from disk and unresolved claims remain
``UNCERTAIN`` rather than being guessed at.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence


DEFAULT_MODEL = "gpt-4o-mini"
DEFAULT_CACHE_PATH = Path.home() / ".cache" / "pinocchio" / "claims.json"
CLAIMS_SYSTEM_PROMPT = """\
Extract only verifiable claims made by the coding agent.

Return JSON with exactly this shape:
{"claims": [{"claim": "short atomic claim"}]}

Split compound sentences into independent claims. Keep the agent's meaning,
but remove greetings, plans, explanations, and questions. A claim must be a
statement about work performed, tests run, files changed, or the resulting
behavior. Do not infer claims that the agent did not state.
"""

_STOP_WORDS = {
    "a",
    "all",
    "an",
    "and",
    "are",
    "at",
    "be",
    "by",
    "for",
    "from",
    "has",
    "have",
    "i",
    "in",
    "is",
    "it",
    "of",
    "on",
    "or",
    "the",
    "this",
    "to",
    "was",
    "were",
    "with",
}


class EntailmentError(RuntimeError):
    """Raised when an explicit entailment operation cannot be completed."""


@dataclass(frozen=True)
class ClaimExtraction:
    """Claims and provenance returned by the extraction layer."""

    claims: tuple[str, ...]
    source: str
    error: str | None = None


@dataclass(frozen=True)
class Evidence:
    """A finding produced outside the language model."""

    evidence: str
    check_type: str
    verdict: str | None = None
    severity: int = 1
    claim: str | None = None
    ledger_index: int | None = None


def _default_cache_path() -> Path:
    configured = os.environ.get("PINOCCHIO_CLAIMS_CACHE")
    return Path(configured).expanduser() if configured else DEFAULT_CACHE_PATH


def _message_key(message: str) -> str:
    return hashlib.sha256(message.encode("utf-8")).hexdigest()


def _normalise_claim(value: Any) -> str:
    if isinstance(value, str):
        return " ".join(value.split()).strip()
    if isinstance(value, Mapping):
        for key in ("claim", "text", "statement"):
            candidate = value.get(key)
            if isinstance(candidate, str):
                return " ".join(candidate.split()).strip()
    return ""


def _normalise_claims(value: Any) -> list[str]:
    if isinstance(value, Mapping):
        value = value.get("claims", [])
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        raise EntailmentError("Claim extraction response must contain a claims array.")
    claims: list[str] = []
    for item in value:
        claim = _normalise_claim(item)
        if claim and claim not in claims:
            claims.append(claim)
    return claims


def _decode_json(content: Any) -> Any:
    if isinstance(content, Mapping):
        return content
    if not isinstance(content, str):
        raise EntailmentError("OpenAI returned a non-text claim response.")
    text = content.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.IGNORECASE)
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise EntailmentError("OpenAI returned invalid JSON for claim extraction.") from exc


def _response_content(response: Any) -> Any:
    if isinstance(response, Mapping):
        choices = response.get("choices")
        if isinstance(choices, Sequence) and choices:
            message = choices[0].get("message", {}) if isinstance(choices[0], Mapping) else {}
            return message.get("content") if isinstance(message, Mapping) else None
        return response
    choices = getattr(response, "choices", None)
    if choices:
        message = getattr(choices[0], "message", None)
        return getattr(message, "content", None)
    return response


def _call_openai(client: Any, message: str, model: str) -> list[str]:
    """Call the supported Chat Completions surface and normalize its output."""

    try:
        response = client.chat.completions.create(
            model=model,
            temperature=0,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": CLAIMS_SYSTEM_PROMPT},
                {"role": "user", "content": message},
            ],
        )
        return _normalise_claims(_decode_json(_response_content(response)))
    except EntailmentError:
        raise
    except Exception as exc:
        # SDK versions expose different exception classes. Keep this single
        # external boundary explicit so callers can use the cache reliably.
        raise EntailmentError(f"OpenAI claim extraction failed: {exc}") from exc


def _build_client(api_key: str | None) -> Any:
    try:
        from openai import OpenAI
    except ImportError as exc:
        raise EntailmentError("The openai package is required for claim extraction.") from exc
    try:
        return OpenAI(api_key=api_key) if api_key else OpenAI()
    except Exception as exc:
        raise EntailmentError(f"Could not initialize OpenAI: {exc}") from exc


def _read_cache(path: Path, message: str) -> tuple[list[str] | None, list[str] | None]:
    if not path.is_file():
        return None, None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return None, None
    if not isinstance(payload, Mapping):
        return None, None
    entries = payload.get("entries")
    exact = entries.get(_message_key(message)) if isinstance(entries, Mapping) else None
    last = payload.get("last_claims")
    try:
        exact_claims = _normalise_claims(exact) if exact is not None else None
        last_claims = _normalise_claims(last) if last is not None else None
    except EntailmentError:
        return None, None
    return exact_claims, last_claims


def _write_cache(path: Path, message: str, claims: Sequence[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    try:
        existing = json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}
    except (OSError, UnicodeError, json.JSONDecodeError):
        existing = {}
    entries = existing.get("entries", {}) if isinstance(existing, Mapping) else {}
    if not isinstance(entries, Mapping):
        entries = {}
    entries = {str(key): value for key, value in entries.items()}
    entries[_message_key(message)] = list(claims)
    payload = {
        "version": 1,
        "last_message": _message_key(message),
        "last_claims": list(claims),
        "entries": dict(list(entries.items())[-100:]),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    temporary: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            "w", encoding="utf-8", dir=path.parent, prefix=f".{path.name}.", delete=False
        ) as handle:
            temporary = handle.name
            json.dump(payload, handle, indent=2)
            handle.write("\n")
        os.chmod(temporary, 0o600)
        os.replace(temporary, path)
    except OSError as exc:
        if temporary:
            try:
                os.unlink(temporary)
            except OSError:
                pass
        raise EntailmentError(f"Could not write claim cache {path}: {exc}") from exc


def _heuristic_claims(message: str) -> list[str]:
    """Provide a conservative offline fallback when no cache exists."""

    claims: list[str] = []
    for part in re.split(r"(?<=[.!?])\s+|\n+", message):
        claim = re.sub(r"^\s*(?:[-*]|\d+[.)])\s*", "", part).strip()
        if claim and claim[-1:] not in {"?", ":"} and claim not in claims:
            claims.append(claim)
    return claims


def extract_claims_with_status(
    message: str,
    *,
    client: Any | None = None,
    api_key: str | None = None,
    model: str = DEFAULT_MODEL,
    cache_path: Path | str | None = None,
) -> ClaimExtraction:
    """Extract atomic claims, falling back to cached or conservative claims."""

    if not isinstance(message, str):
        raise TypeError("message must be a string")
    if not message.strip():
        return ClaimExtraction((), "empty")

    path = Path(cache_path).expanduser() if cache_path is not None else _default_cache_path()
    exact, last = _read_cache(path, message)
    try:
        active_client = client if client is not None else _build_client(api_key or os.environ.get("OPENAI_API_KEY"))
        claims = _call_openai(active_client, message, model)
        try:
            _write_cache(path, message, claims)
        except EntailmentError as exc:
            return ClaimExtraction(tuple(claims), "openai", f"Claim cache unavailable: {exc}")
        return ClaimExtraction(tuple(claims), "openai")
    except EntailmentError as exc:
        if exact is not None:
            return ClaimExtraction(tuple(exact), "cache", str(exc))
        if last is not None:
            return ClaimExtraction(tuple(last), "cache-last", str(exc))
        return ClaimExtraction(tuple(_heuristic_claims(message)), "heuristic", str(exc))


def extract_claims(message: str, **kwargs: Any) -> list[str]:
    """Compatibility helper returning only the extracted claim text."""

    return list(extract_claims_with_status(message, **kwargs).claims)


def _tokens(text: str) -> set[str]:
    return {
        token
        for token in re.findall(r"[a-z0-9_]+", text.lower())
        if token not in _STOP_WORDS and len(token) > 1
    }


def _coerce_evidence(item: Evidence | Mapping[str, Any]) -> Evidence:
    if isinstance(item, Evidence):
        return item
    if not isinstance(item, Mapping):
        raise TypeError("evidence entries must be Evidence or mappings")
    detail = item.get("evidence", item.get("message", item.get("detail", "")))
    check_type = item.get("check_type", item.get("type", "detector"))
    if not isinstance(detail, str) or not isinstance(check_type, str):
        raise TypeError("evidence and check_type must be strings")
    severity = item.get("severity", 1)
    if not isinstance(severity, int) or isinstance(severity, bool):
        severity = 1
    verdict = item.get("verdict")
    if verdict is not None and not isinstance(verdict, str):
        verdict = None
    claim = item.get("claim")
    if claim is not None and not isinstance(claim, str):
        claim = None
    ledger_index = item.get("ledger_index")
    if not isinstance(ledger_index, int) or isinstance(ledger_index, bool):
        ledger_index = None
    return Evidence(detail, check_type, verdict, max(1, min(10, severity)), claim, ledger_index)


def _evidence_text(item: Evidence) -> str:
    citation = f"[ledger #{item.ledger_index}] " if item.ledger_index is not None else ""
    return f"{citation}{item.evidence}".strip()


def _matches(claim: str, item: Evidence, claim_count: int) -> bool:
    if item.claim:
        left, right = _tokens(claim), _tokens(item.claim)
        return bool(left and right and (left <= right or right <= left or len(left & right) >= 2))
    return claim_count == 1


def _verdict(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    upper = value.upper()
    if upper in {"LIE", "CONTRADICTED", "UNSUPPORTED"}:
        return "LIE"
    if upper in {"VERIFIED", "SUPPORTED"}:
        return "VERIFIED"
    if upper == "UNCERTAIN":
        return "UNCERTAIN"
    return None


def _result(claim: str, verdict: str, evidence: str, severity: int, check_type: str) -> dict[str, Any]:
    return {
        "claim": claim,
        "verdict": verdict,
        "evidence": evidence or "No independent evidence was available.",
        "severity": max(1, min(10, severity)),
        "check_type": check_type or "entailment",
    }


class EntailmentEngine:
    """Deterministic-first claim entailment with optional model adjudication."""

    def __init__(
        self,
        *,
        client: Any | None = None,
        api_key: str | None = None,
        model: str = DEFAULT_MODEL,
        cache_path: Path | str | None = None,
    ) -> None:
        self.client = client
        self.api_key = api_key
        self.model = model
        self.cache_path = cache_path

    def _adjudicate(self, claims: Sequence[str], evidence: Sequence[Evidence]) -> list[dict[str, Any]]:
        if not claims:
            return []
        active_client = self.client if self.client is not None else _build_client(
            self.api_key or os.environ.get("OPENAI_API_KEY")
        )
        evidence_payload = [
            {"id": index, "check_type": item.check_type, "evidence": _evidence_text(item)}
            for index, item in enumerate(evidence)
        ]
        prompt = json.dumps({"claims": list(claims), "evidence": evidence_payload}, ensure_ascii=True)
        try:
            response = active_client.chat.completions.create(
                model=self.model,
                temperature=0,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": Path(__file__).with_name("prompts").joinpath("entailment_system.txt").read_text(encoding="utf-8")},
                    {"role": "user", "content": prompt},
                ],
            )
            decoded = _decode_json(_response_content(response))
            raw_results = decoded.get("results", []) if isinstance(decoded, Mapping) else []
            if not isinstance(raw_results, Sequence) or isinstance(raw_results, (str, bytes)):
                raise EntailmentError("Entailment response must contain a results array.")
            by_claim = {claim: claim for claim in claims}
            results: list[dict[str, Any]] = []
            for raw in raw_results:
                if not isinstance(raw, Mapping):
                    continue
                claim = _normalise_claim(raw.get("claim"))
                verdict = _verdict(raw.get("verdict"))
                evidence_text = raw.get("evidence")
                if (
                    claim not in by_claim
                    or verdict is None
                    or not isinstance(evidence_text, str)
                    or not evidence_text.strip()
                    or ("[evidence " not in evidence_text and "[ledger #" not in evidence_text)
                ):
                    continue
                results.append(
                    _result(
                        claim,
                        verdict,
                        evidence_text,
                        raw.get("severity", 1) if isinstance(raw.get("severity", 1), int) else 1,
                        str(raw.get("check_type", "entailment")),
                    )
                )
            if len(results) != len(claims):
                known = {item["claim"] for item in results}
                results.extend(
                    _result(claim, "UNCERTAIN", "The model did not return a citable result.", 1, "entailment")
                    for claim in claims
                    if claim not in known
                )
            return results
        except EntailmentError:
            raise
        except Exception as exc:
            raise EntailmentError(f"OpenAI entailment failed: {exc}") from exc

    def evaluate(
        self,
        message: str,
        evidence: Sequence[Evidence | Mapping[str, Any]],
    ) -> list[dict[str, Any]]:
        """Return contract-compatible results for every extracted claim."""

        extraction = extract_claims_with_status(
            message,
            client=self.client,
            api_key=self.api_key,
            model=self.model,
            cache_path=self.cache_path,
        )
        claims = list(extraction.claims)
        normalized_evidence = [_coerce_evidence(item) for item in evidence]
        results: list[dict[str, Any]] = []
        unresolved: list[str] = []
        for claim in claims:
            matched = [item for item in normalized_evidence if _matches(claim, item, len(claims))]
            lies = [item for item in matched if _verdict(item.verdict) == "LIE"]
            verified = [item for item in matched if _verdict(item.verdict) == "VERIFIED"]
            if lies:
                results.append(
                    _result(
                        claim,
                        "LIE",
                        " ".join(_evidence_text(item) for item in lies),
                        max(item.severity for item in lies),
                        lies[0].check_type,
                    )
                )
            elif verified:
                results.append(
                    _result(
                        claim,
                        "VERIFIED",
                        " ".join(_evidence_text(item) for item in verified),
                        1,
                        verified[0].check_type,
                    )
                )
            else:
                unresolved.append(claim)

        if unresolved:
            try:
                results.extend(self._adjudicate(unresolved, normalized_evidence))
            except EntailmentError as exc:
                results.extend(
                    _result(
                        claim,
                        "UNCERTAIN",
                        f"No deterministic evidence settled this claim; model adjudication unavailable: {exc}",
                        1,
                        "entailment",
                    )
                    for claim in unresolved
                )
        return results


def entail(
    message: str,
    evidence: Sequence[Evidence | Mapping[str, Any]],
    **kwargs: Any,
) -> list[dict[str, Any]]:
    """Convenience entry point for the pipeline's L2 entailment stage."""

    return EntailmentEngine(**kwargs).evaluate(message, evidence)
