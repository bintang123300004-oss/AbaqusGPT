import unittest

from src.hybrid.safety import ApprovalRegistry, validate_bridge_request
from abaqus_scripts.bridge_contract import validate_envelope


class BridgeSafetyTests(unittest.TestCase):
    def test_allowlisted_read_operation_is_queued(self):
        registry = ApprovalRegistry()
        item = registry.create("inspect_model", {"model_name": "Bracket"})
        self.assertEqual(item.status, "queued_read_only")
        self.assertFalse(item.approval_required)

    def test_model_change_waits_for_explicit_approval(self):
        registry = ApprovalRegistry()
        item = registry.create("propose_model_change", {
            "model_name": "Bracket", "change_type": "material",
            "description": "Add steel material",
        })
        self.assertEqual(item.status, "awaiting_approval")
        approved = registry.approve(item.request_id)
        self.assertEqual(approved.status, "approved_for_operator_review")

    def test_unknown_operations_and_extra_fields_are_rejected(self):
        with self.assertRaises(ValueError):
            validate_bridge_request("run_python", {"code": "print(1)"})
        with self.assertRaises(ValueError):
            validate_bridge_request("inspect_model", {"model_name": "A", "command": "whoami"})

    def test_job_submission_requires_approval_and_cannot_be_auto_executed(self):
        registry = ApprovalRegistry()
        item = registry.create("submit_job", {"job_name": "Case-1"})
        self.assertEqual(item.status, "awaiting_approval")
        self.assertEqual(registry.approve(item.request_id).status, "approved_for_operator_review")

    def test_values_are_bounded_and_scalar_only(self):
        with self.assertRaises(ValueError):
            validate_bridge_request("inspect_model", {"model_name": "x" * 2049})
        with self.assertRaises(ValueError):
            validate_bridge_request("inspect_model", {"model_name": ["A"]})

    def test_python27_contract_rejects_unapproved_changes_and_arbitrary_code(self):
        envelope = {
            "request_id": "abc", "operation": "propose_model_change",
            "parameters": {"model_name": "A", "change_type": "material", "description": "steel"},
            "approved": False,
        }
        with self.assertRaises(ValueError):
            validate_envelope(envelope)
        envelope["approved"] = True
        self.assertTrue(validate_envelope(envelope))
        envelope["operation"] = "execute_python"
        with self.assertRaises(ValueError):
            validate_envelope(envelope)


if __name__ == "__main__":
    unittest.main()

