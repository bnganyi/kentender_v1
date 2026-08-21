# Copyright (c) 2026, KenTender and contributors
from kentender_strategy.seeds.works_master_strategy_purge import (
	purge_non_works_strategy_hierarchy,
	purge_works_master_strategy_hierarchy,
)


def run(*args, **kwargs):
	return purge_works_master_strategy_hierarchy(*args, **kwargs)
