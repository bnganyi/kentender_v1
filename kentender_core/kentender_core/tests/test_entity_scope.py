"""Phase G — entity scope helpers (stubs)."""

import unittest

from kentender_core.utils.entity_scope import filter_by_entity, get_user_departments, get_user_entity


class TestEntityScope(unittest.TestCase):
	def test_get_user_entity_stub(self):
		self.assertIsNone(get_user_entity())
		self.assertIsNone(get_user_entity("Administrator"))

	def test_get_user_departments_stub(self):
		self.assertEqual(get_user_departments(), [])
		self.assertEqual(get_user_departments("Administrator"), [])

	def test_filter_by_entity_identity(self):
		sentinel = object()
		self.assertIs(filter_by_entity(sentinel, "ENT-1"), sentinel)
		self.assertIs(filter_by_entity(sentinel, None), sentinel)
