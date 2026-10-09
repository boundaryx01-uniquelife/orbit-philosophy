"""Validate public synthetic Life OS scenarios before they enter an app or PR."""

import json
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = Path(__file__).with_name("first_flow.schema.json")
FIXTURE_PATH = ROOT / "fixtures" / "first_flow.synthetic.json"


def validate_scenarios(scenarios: list[dict]) -> None:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    scenario_ids: set[str] = set()
    entity_ids: set[str] = set()

    for scenario in scenarios:
        validator.validate(scenario)
        scenario_id = scenario["id"]
        if scenario_id in scenario_ids:
            raise ValueError(f"duplicate scenario id: {scenario_id}")
        scenario_ids.add(scenario_id)

        case = scenario["case"]
        case_id = case["id"]

        collections = {
            "evidence": scenario["evidence"],
            "claim": scenario["claims"],
            "preference_constraint": scenario["preferences_constraints"],
            "proposal": scenario["proposals"],
            "feedback": scenario["feedback"],
        }
        indexed = {
            kind: {item["id"]: item for item in items}
            for kind, items in collections.items()
        }
        indexed["case"] = {case_id: case}

        for kind, items in collections.items():
            for item in items:
                if item["case_id"] != case_id:
                    raise ValueError(f"{kind} {item['id']} points to another case")
                if item["id"] in entity_ids:
                    raise ValueError(f"duplicate entity id: {item['id']}")
                entity_ids.add(item["id"])
        if case_id in entity_ids:
            raise ValueError(f"duplicate entity id: {case_id}")
        entity_ids.add(case_id)

        evidence = indexed["evidence"]
        claims = indexed["claim"]
        proposals = indexed["proposal"]
        for claim in scenario["claims"]:
            require_ids(claim["evidence_ids"], evidence, claim["id"])
        for preference in scenario["preferences_constraints"]:
            require_ids([preference["source_evidence_id"]], evidence, preference["id"])
        for proposal in scenario["proposals"]:
            require_ids(proposal["evidence_ids"], evidence, proposal["id"])
            require_ids(proposal["observation_claim_ids"], claims, proposal["id"])
            for claim_id in proposal["observation_claim_ids"]:
                if claims[claim_id]["kind"] != "observation":
                    raise ValueError(f"proposal {proposal['id']} cites inference as observation")
        for feedback in scenario["feedback"]:
            require_ids([feedback["proposal_id"]], proposals, feedback["id"])
        for event in scenario["chronicle"]:
            if event["case_id"] != case_id:
                raise ValueError(f"event {event['id']} points to another case")
            if event["id"] in entity_ids:
                raise ValueError(f"duplicate entity id: {event['id']}")
            entity_ids.add(event["id"])
            if event["event"] != "deleted":
                require_ids([event["entity_id"]], indexed[event["entity_type"]], event["id"])


def require_ids(ids: list[str], collection: dict, referrer: str) -> None:
    for entity_id in ids:
        if entity_id not in collection:
            raise ValueError(f"{referrer} refers to missing or foreign entity {entity_id}")


if __name__ == "__main__":
    fixtures = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    validate_scenarios(fixtures)
    print(f"Validated {len(fixtures)} synthetic Life OS scenarios")
