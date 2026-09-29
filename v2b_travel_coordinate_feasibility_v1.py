"""Audit coordinate coverage for frozen V2B travel route identities.

Research-only. Consumes the immutable V2B route-identity artifact and resolves club
home-venue coordinates through Wikidata:

    association football club -> home venue (P115) -> coordinate location (P625)

If a club has no usable home-venue coordinate, a direct club P625 coordinate may be
recorded only as an explicit fallback. Fallback coordinates are never silently promoted
to stadium-level coordinates.

No route kilometers and no market direction are computed in this block.
"""
from __future__ import annotations

import argparse
import json
import math
import re
import time
import unicodedata
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import requests

EXPERIMENT_ID = "V2B_TRAVEL_COORDINATE_FEASIBILITY_V1"
ROUTE_EXPERIMENT_ID = "V2B_TRAVEL_VENUE_IDENTITY_FEASIBILITY_V1"

EXPECTED_ROUTE_ARTIFACT_ID = "11044111558"
EXPECTED_ROUTE_ARTIFACT_DIGEST = (
    "sha256:8c895a500169760c1fe36fe5eeb40861d06d2aa23a4b26e15d3f580f3243837b"
)
EXPECTED_FIXTURES = 43
EXPECTED_TEAM_SIDES = 86
TARGET_DATE = date(2026, 9, 20)

WIKIDATA_API = "https://www.wikidata.org/w/api.php"
WIKIPEDIA_API = "https://en.wikipedia.org/w/api.php"
FOOTBALL_CLUB_QID = "Q476028"

SEARCH_ALIASES = {
    "Alaves": "Deportivo Alaves",
    "Anderlecht": "RSC Anderlecht",
    "Angers": "Angers SCO",
    "Atalanta": "Atalanta BC",
    "Ath Bilbao": "Athletic Bilbao",
    "Ath Madrid": "Atletico Madrid",
    "Athletic Club": "Athletic Bilbao",
    "Atletico Madrid": "Atletico Madrid",
    "Augsburg": "FC Augsburg",
    "Auxerre": "AJ Auxerre",
    "Barcelona": "FC Barcelona",
    "Bayer Leverkusen": "Bayer 04 Leverkusen",
    "Besiktas": "Besiktas JK",
    "Betis": "Real Betis",
    "Bologna": "Bologna FC 1909",
    "Borussia M'gladbach": "Borussia Monchengladbach",
    "Bournemouth": "AFC Bournemouth",
    "Brest": "Stade Brestois 29",
    "Brighton": "Brighton and Hove Albion",
    "Celta Vigo": "Celta Vigo",
    "Como": "Como 1907",
    "Deportivo A Coruna": "Deportivo La Coruna",
    "Dortmund": "Borussia Dortmund",
    "Elche": "Elche CF",
    "Elversberg": "SV Elversberg",
    "FC Koln": "1. FC Koln",
    "Fiorentina": "ACF Fiorentina",
    "Freiburg": "SC Freiburg",
    "Frosinone": "Frosinone Calcio",
    "Genoa": "Genoa CFC",
    "Getafe": "Getafe CF",
    "Hamburg": "Hamburger SV",
    "Hoffenheim": "TSG Hoffenheim",
    "Inter": "Inter Milan",
    "La Coruna": "Deportivo La Coruna",
    "Lazio": "SS Lazio",
    "Le Havre": "Le Havre AC",
    "Le Mans": "Le Mans FC",
    "Lecce": "US Lecce",
    "Leeds": "Leeds United",
    "Levante": "Levante UD",
    "Leverkusen": "Bayer 04 Leverkusen",
    "Lille": "Lille OSC",
    "Lorient": "FC Lorient",
    "Lyon": "Olympique Lyonnais",
    "Mainz": "Mainz 05",
    "Malaga": "Malaga CF",
    "Man City": "Manchester City",
    "Marseille": "Olympique de Marseille",
    "Milan": "AC Milan",
    "Napoli": "SSC Napoli",
    "Newcastle": "Newcastle United",
    "Nice": "OGC Nice",
    "Nottm Forest": "Nottingham Forest",
    "OFI Crete": "OFI Crete FC",
    "Omonia": "Omonia Nicosia",
    "Osasuna": "CA Osasuna",
    "Paderborn": "SC Paderborn 07",
    "Parma": "Parma Calcio 1913",
    "Paris FC": "Paris FC",
    "RB Leipzig": "RB Leipzig",
    "Roma": "AS Roma",
    "Schalke": "Schalke 04",
    "Sevilla": "Sevilla FC",
    "Strasbourg": "RC Strasbourg",
    "Sturm Graz": "SK Sturm Graz",
    "Sunderland": "Sunderland AFC",
    "Torino": "Torino FC",
    "Tottenham": "Tottenham Hotspur",
    "Toulouse": "Toulouse FC",
    "Udinese": "Udinese Calcio",
    "Union Berlin": "Union Berlin",
    "Valencia": "Valencia CF",
    "Vallecano": "Rayo Vallecano",
    "Venezia": "Venezia FC",
    "Villarreal": "Villarreal CF",
    "Werder Bremen": "Werder Bremen",
}


def _key(value: Any) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return "".join(ch.lower() for ch in text if ch.isalnum())


def _wikipedia_title(label: str) -> str:
    return SEARCH_ALIASES.get(label, label)


def _claim_item_ids(entity: dict[str, Any], prop: str) -> list[tuple[str, dict[str, Any]]]:
    result: list[tuple[str, dict[str, Any]]] = []
    for claim in (entity.get("claims") or {}).get(prop) or []:
        if claim.get("rank") == "deprecated":
            continue
        snak = claim.get("mainsnak") or {}
        value = (snak.get("datavalue") or {}).get("value")
        if isinstance(value, dict):
            qid = value.get("id")
            if isinstance(qid, str) and qid.startswith("Q"):
                result.append((qid, claim))
    return result


def _claim_coordinate(entity: dict[str, Any]) -> tuple[float, float] | None:
    claims = (entity.get("claims") or {}).get("P625") or []
    candidates: list[tuple[int, float, float]] = []
    for claim in claims:
        if claim.get("rank") == "deprecated":
            continue
        value = ((claim.get("mainsnak") or {}).get("datavalue") or {}).get("value")
        if not isinstance(value, dict):
            continue
        try:
            lat = float(value.get("latitude"))
            lon = float(value.get("longitude"))
        except (TypeError, ValueError):
            continue
        if not (math.isfinite(lat) and math.isfinite(lon)):
            continue
        if not (-90 <= lat <= 90 and -180 <= lon <= 180):
            continue
        candidates.append((2 if claim.get("rank") == "preferred" else 1, lat, lon))
    if not candidates:
        return None
    best_rank = max(x[0] for x in candidates)
    coords = sorted({(x[1], x[2]) for x in candidates if x[0] == best_rank})
    if len(coords) != 1:
        return None
    return coords[0]


def _wikidata_time(claim: dict[str, Any], prop: str) -> date | None:
    values = (claim.get("qualifiers") or {}).get(prop) or []
    parsed: list[date] = []
    for snak in values:
        value = (snak.get("datavalue") or {}).get("value")
        if not isinstance(value, dict):
            continue
        raw = str(value.get("time") or "")
        match = re.match(r"^[+-](\d{4})-(\d{2})-(\d{2})T", raw)
        if not match:
            continue
        try:
            parsed.append(date(int(match.group(1)), int(match.group(2)), int(match.group(3))))
        except ValueError:
            continue
    return max(parsed) if parsed else None


def _claim_active_at(claim: dict[str, Any], target: date = TARGET_DATE) -> bool:
    start = _wikidata_time(claim, "P580")
    end = _wikidata_time(claim, "P582")
    if start is not None and start > target:
        return False
    if end is not None and end < target:
        return False
    return True


def _footballish(search_result: dict[str, Any], entity: dict[str, Any]) -> bool:
    desc = str(search_result.get("description") or "").lower()
    if "football" in desc or "soccer" in desc:
        return True
    return FOOTBALL_CLUB_QID in {qid for qid, _ in _claim_item_ids(entity, "P31")}


def _label(entity: dict[str, Any]) -> str | None:
    labels = entity.get("labels") or {}
    for lang in ("en", "de", "fr", "es", "it"):
        value = labels.get(lang)
        if isinstance(value, dict) and value.get("value"):
            return str(value["value"])
    return None


class WikidataClient:
    def __init__(self, session: requests.Session | None = None):
        self._owned = session is None
        self.session = session or requests.Session()
        self.session.headers.update(
            {"User-Agent": "football-ai-v2b-coordinate-feasibility/1.0"}
        )
        self.public_http_requests = 0

    def close(self) -> None:
        if self._owned:
            self.session.close()

    def _get_url(self, url: str, params: dict[str, Any]) -> dict[str, Any]:
        response = self.session.get(url, params=params, timeout=30)
        self.public_http_requests += 1
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, dict):
            raise RuntimeError("coordinate-source response is not an object")
        return payload

    def _get(self, params: dict[str, Any]) -> dict[str, Any]:
        return self._get_url(WIKIDATA_API, params)

    def wikipedia_qids(self, titles: Iterable[str]) -> dict[str, str | None]:
        unique = list(dict.fromkeys(str(x) for x in titles if str(x).strip()))
        result: dict[str, str | None] = {}
        for i in range(0, len(unique), 50):
            batch = unique[i : i + 50]
            payload = self._get_url(
                WIKIPEDIA_API,
                {
                    "action": "query",
                    "titles": "|".join(batch),
                    "prop": "pageprops",
                    "ppprop": "wikibase_item",
                    "redirects": 1,
                    "format": "json",
                    "origin": "*",
                },
            )
            query = payload.get("query") or {}
            aliases = {title: title for title in batch}
            for section in ("normalized", "redirects"):
                for row in query.get(section) or []:
                    if isinstance(row, dict) and row.get("from") and row.get("to"):
                        aliases[str(row["from"])] = str(row["to"])
            pages_by_title = {
                str(page.get("title")): page
                for page in (query.get("pages") or {}).values()
                if isinstance(page, dict) and page.get("title")
            }
            for original in batch:
                current = original
                seen: set[str] = set()
                while current in aliases and aliases[current] != current and current not in seen:
                    seen.add(current)
                    current = aliases[current]
                page = pages_by_title.get(current)
                qid = None
                if isinstance(page, dict):
                    value = (page.get("pageprops") or {}).get("wikibase_item")
                    if isinstance(value, str) and value.startswith("Q"):
                        qid = value
                result[original] = qid
        return result

    def entities(self, ids: Iterable[str]) -> dict[str, dict[str, Any]]:
        unique = list(dict.fromkeys(str(x) for x in ids if str(x).startswith("Q")))
        result: dict[str, dict[str, Any]] = {}
        for i in range(0, len(unique), 50):
            batch = unique[i : i + 50]
            payload = self._get(
                {
                    "action": "wbgetentities",
                    "ids": "|".join(batch),
                    "props": "claims|labels|descriptions",
                    "languages": "en|de|fr|es|it",
                    "format": "json",
                    "origin": "*",
                }
            )
            for qid, entity in (payload.get("entities") or {}).items():
                if isinstance(entity, dict) and not entity.get("missing"):
                    result[str(qid)] = entity
        return result


def _choose_club_candidate(query_label, search_results, entities):
    desired_key = _key(query_label.replace(" football club", ""))
    scored = []
    for rank, result in enumerate(search_results):
        qid = str(result.get("id") or "")
        entity = entities.get(qid)
        if entity is None or not _footballish(result, entity):
            continue
        score = 0
        if _claim_item_ids(entity, "P115"):
            score += 100
        if _claim_coordinate(entity) is not None:
            score += 20
        label_key = _key(result.get("label") or _label(entity) or "")
        if label_key == desired_key:
            score += 30
        elif desired_key and (desired_key in label_key or label_key in desired_key):
            score += 15
        score -= rank
        scored.append((score, -rank, result, entity))
    if not scored:
        return None
    scored.sort(key=lambda row: (row[0], row[1]), reverse=True)
    if len([row for row in scored if row[0] == scored[0][0]]) != 1:
        return None
    _, _, result, entity = scored[0]
    return {
        "qid": str(result["id"]),
        "search_label": str(result.get("label") or _label(entity) or ""),
        "description": str(result.get("description") or ""),
        "entity": entity,
    }


def _resolve_coordinate(*, club, venue_entities):
    entity = club["entity"]
    active_claims = [
        (qid, claim)
        for qid, claim in _claim_item_ids(entity, "P115")
        if _claim_active_at(claim)
    ]
    preferred = [
        (qid, claim) for qid, claim in active_claims
        if claim.get("rank") == "preferred"
    ]
    candidate_claims = preferred if preferred else active_claims

    stadium_candidates = []
    for qid, _ in candidate_claims:
        venue = venue_entities.get(qid)
        if venue is None:
            continue
        coord = _claim_coordinate(venue)
        if coord is not None:
            stadium_candidates.append((qid, coord))

    unique_stadium = {
        (qid, round(coord[0], 8), round(coord[1], 8))
        for qid, coord in stadium_candidates
    }
    if len(unique_stadium) == 1:
        qid, lat, lon = next(iter(unique_stadium))
        venue = venue_entities[qid]
        return {
            "coordinate_status": "STADIUM_COORDINATE",
            "club_qid": club["qid"],
            "club_label": club["search_label"],
            "venue_qid": qid,
            "venue_label": _label(venue),
            "latitude": lat,
            "longitude": lon,
            "active_home_venue_claim_count": len(active_claims),
        }
    if len(unique_stadium) > 1:
        return {
            "coordinate_status": "AMBIGUOUS_ACTIVE_HOME_VENUES",
            "club_qid": club["qid"],
            "club_label": club["search_label"],
            "venue_qid": None,
            "venue_label": None,
            "latitude": None,
            "longitude": None,
            "active_home_venue_claim_count": len(active_claims),
            "ambiguous_venue_qids": sorted({row[0] for row in unique_stadium}),
        }

    club_coord = _claim_coordinate(entity)
    if club_coord is not None:
        return {
            "coordinate_status": "CLUB_COORDINATE_FALLBACK",
            "club_qid": club["qid"],
            "club_label": club["search_label"],
            "venue_qid": None,
            "venue_label": None,
            "latitude": club_coord[0],
            "longitude": club_coord[1],
            "active_home_venue_claim_count": len(active_claims),
        }

    return {
        "coordinate_status": "NO_COORDINATE",
        "club_qid": club["qid"],
        "club_label": club["search_label"],
        "venue_qid": None,
        "venue_label": None,
        "latitude": None,
        "longitude": None,
        "active_home_venue_claim_count": len(active_claims),
    }


def _validate_route(payload):
    if payload.get("experiment_id") != ROUTE_EXPERIMENT_ID:
        raise RuntimeError("unexpected route-identity experiment")
    if payload.get("status") != "FULL_86_VENUE_IDENTITY_FEASIBLE":
        raise RuntimeError("route identity is not fully feasible")
    if int(payload.get("locked_fixture_count", -1)) != EXPECTED_FIXTURES:
        raise RuntimeError("unexpected route fixture count")
    if int(payload.get("team_side_count", -1)) != EXPECTED_TEAM_SIDES:
        raise RuntimeError("unexpected route team-side count")
    if int(payload.get("previous_event_resolved_team_sides", -1)) != EXPECTED_TEAM_SIDES:
        raise RuntimeError("route side coverage changed")
    if payload.get("coordinate_layer_applied") is not False:
        raise RuntimeError("route artifact already applied coordinates")
    if payload.get("distance_km_computed") is not False:
        raise RuntimeError("route artifact already computed distance")
    for flag in (
        "market_rows_read",
        "v2b_odds_read",
        "centre_delta_read",
        "direction_test_performed",
        "match_outcome_target_used",
    ):
        if payload.get(flag) is not False:
            raise RuntimeError(f"route safety flag changed: {flag}")
    rows = payload.get("rows")
    if not isinstance(rows, list) or len(rows) != EXPECTED_TEAM_SIDES:
        raise RuntimeError("unexpected route rows")
    return rows


def audit(route_payload, *, client):
    rows = _validate_route(route_payload)
    labels = sorted(
        {
            str(value)
            for row in rows
            for value in (
                row.get("previous_venue_label"),
                row.get("target_venue_label"),
            )
            if str(value or "").strip()
        }
    )

    title_by_label = {label: _wikipedia_title(label) for label in labels}
    qid_by_title = client.wikipedia_qids(sorted(set(title_by_label.values())))
    club_qids = sorted({qid for qid in qid_by_title.values() if qid})
    candidate_entities = client.entities(club_qids)

    clubs_by_title = {}
    for title, qid in qid_by_title.items():
        entity = candidate_entities.get(str(qid)) if qid else None
        if entity is None:
            clubs_by_title[title] = None
            continue
        description = " ".join(
            str(value.get("value") or "")
            for value in (entity.get("descriptions") or {}).values()
            if isinstance(value, dict)
        ).lower()
        footballish = (
            "football" in description
            or "soccer" in description
            or FOOTBALL_CLUB_QID in {x for x, _ in _claim_item_ids(entity, "P31")}
            or bool(_claim_item_ids(entity, "P115"))
        )
        if not footballish:
            clubs_by_title[title] = None
            continue
        clubs_by_title[title] = {
            "qid": str(qid),
            "search_label": _label(entity) or title,
            "description": description,
            "entity": entity,
        }

    venue_ids = {
        qid
        for club in clubs_by_title.values()
        if club is not None
        for qid, claim in _claim_item_ids(club["entity"], "P115")
        if _claim_active_at(claim)
    }
    venue_entities = client.entities(sorted(venue_ids))

    coordinate_by_label = {}
    for label in labels:
        title = title_by_label[label]
        club = clubs_by_title.get(title)
        if club is None:
            coordinate_by_label[label] = {
                "input_label": label,
                "wikipedia_title": title,
                "coordinate_status": "CLUB_IDENTITY_UNRESOLVED",
                "club_qid": None,
                "club_label": None,
                "venue_qid": None,
                "venue_label": None,
                "latitude": None,
                "longitude": None,
            }
        else:
            coordinate_by_label[label] = {
                "input_label": label,
                "wikipedia_title": title,
                **_resolve_coordinate(club=club, venue_entities=venue_entities),
            }

    status_counts = {}
    for item in coordinate_by_label.values():
        key = item["coordinate_status"]
        status_counts[key] = status_counts.get(key, 0) + 1

    stadium_route_sides = 0
    any_route_sides = 0
    per_fixture_stadium = {}
    per_fixture_any = {}
    route_rows = []
    for row in rows:
        previous = coordinate_by_label[str(row["previous_venue_label"])]
        target = coordinate_by_label[str(row["target_venue_label"])]
        stadium_ok = (
            previous["coordinate_status"] == "STADIUM_COORDINATE"
            and target["coordinate_status"] == "STADIUM_COORDINATE"
        )
        any_ok = (
            previous.get("latitude") is not None
            and target.get("latitude") is not None
        )
        stadium_route_sides += int(stadium_ok)
        any_route_sides += int(any_ok)
        fixture_id = str(row["fixture_id"])
        per_fixture_stadium[fixture_id] = per_fixture_stadium.get(fixture_id, 0) + int(stadium_ok)
        per_fixture_any[fixture_id] = per_fixture_any.get(fixture_id, 0) + int(any_ok)
        route_rows.append(
            {
                "fixture_id": fixture_id,
                "league": row["league"],
                "target_team": row["target_team"],
                "target_role": row["target_role"],
                "previous_venue_label": row["previous_venue_label"],
                "target_venue_label": row["target_venue_label"],
                "previous_coordinate_status": previous["coordinate_status"],
                "target_coordinate_status": target["coordinate_status"],
                "stadium_coordinate_route_feasible": stadium_ok,
                "any_coordinate_route_feasible": any_ok,
            }
        )

    fixtures_stadium = sum(1 for count in per_fixture_stadium.values() if count == 2)
    fixtures_any = sum(1 for count in per_fixture_any.values() if count == 2)

    if stadium_route_sides == EXPECTED_TEAM_SIDES:
        status = "FULL_86_STADIUM_COORDINATE_FEASIBLE"
    elif any_route_sides == EXPECTED_TEAM_SIDES:
        status = "FULL_86_MIXED_COORDINATE_FEASIBLE"
    elif any_route_sides > 0:
        status = "PARTIAL_COORDINATE_FEASIBILITY"
    else:
        status = "COORDINATE_SOURCE_UNUSABLE"

    return {
        "experiment_id": EXPERIMENT_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "research_only": True,
        "source_feasibility_audit": True,
        "route_source_artifact_id": EXPECTED_ROUTE_ARTIFACT_ID,
        "route_source_artifact_digest": EXPECTED_ROUTE_ARTIFACT_DIGEST,
        "coordinate_source": "ENWIKI_PAGEPROPS_TO_WIKIDATA",
        "coordinate_contract": (
            "club -> P115 home venue -> P625 coordinate; "
            "direct club P625 fallback is explicit only"
        ),
        "target_date_for_home_venue_claims": TARGET_DATE.isoformat(),
        "unique_route_venue_labels": len(labels),
        "stadium_coordinate_labels": status_counts.get("STADIUM_COORDINATE", 0),
        "club_coordinate_fallback_labels": status_counts.get("CLUB_COORDINATE_FALLBACK", 0),
        "ambiguous_active_home_venue_labels": status_counts.get("AMBIGUOUS_ACTIVE_HOME_VENUES", 0),
        "unresolved_club_identity_labels": status_counts.get("CLUB_IDENTITY_UNRESOLVED", 0),
        "no_coordinate_labels": status_counts.get("NO_COORDINATE", 0),
        "coordinate_status_counts": status_counts,
        "team_side_count": EXPECTED_TEAM_SIDES,
        "stadium_coordinate_route_team_sides": stadium_route_sides,
        "any_coordinate_route_team_sides": any_route_sides,
        "fixtures_both_sides_stadium_coordinate_feasible": fixtures_stadium,
        "fixtures_both_sides_any_coordinate_feasible": fixtures_any,
        "status": status,
        "public_http_requests": client.public_http_requests,
        "coordinate_layer_applied": True,
        "distance_km_computed": False,
        "market_rows_read": False,
        "v2b_odds_read": False,
        "centre_delta_read": False,
        "direction_test_performed": False,
        "match_outcome_target_used": False,
        "odds_api_requests": 0,
        "supabase_operations": 0,
        "production_model_operations": 0,
        "coordinate_rows": [coordinate_by_label[label] for label in labels],
        "route_rows": route_rows,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--route-report", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    route = json.loads(args.route_report.read_text(encoding="utf-8"))
    client = WikidataClient()
    try:
        report = audit(route, client=client)
    finally:
        client.close()

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False))


if __name__ == "__main__":
    main()
