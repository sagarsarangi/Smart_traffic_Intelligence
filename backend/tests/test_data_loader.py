"""
Tests for backend/data/loader.py

Covers the dataset loading lifecycle, the heatmap weight formula, the
analytics cache structure, and the live-incident append path.
"""

from __future__ import annotations

import math

import pandas as pd
import pytest

from backend.data import loader
from backend.data.loader import (
    _compute_resolution_minutes,
    _compute_single_heatmap_point,
    _corridor_rank,
    add_live_incident,
    get_analytics_cache,
    get_corridor_counts,
    get_dataframe,
    get_heatmap_cache,
    get_junction_lookup,
    load_dataset,
)


# ---------------------------------------------------------------------------
# load_dataset lifecycle
# ---------------------------------------------------------------------------

class TestLoadDataset:
    def test_dataset_is_loaded_after_init(self):
        df = get_dataframe()
        assert isinstance(df, pd.DataFrame)
        # Real dataset has 8,173 records (per AGENTS.md §2)
        assert len(df) == 8173

    def test_dataset_has_required_columns(self):
        df = get_dataframe()
        for col in [
            "latitude", "longitude", "event_type", "event_cause",
            "requires_road_closure", "start_datetime", "zone", "junction",
            "corridor", "priority", "police_station", "address", "status",
        ]:
            assert col in df.columns, f"Missing required column: {col}"

    def test_load_dataset_is_idempotent(self):
        """Calling load_dataset again must not reload or raise."""
        df_before = get_dataframe()
        load_dataset()  # should be a no-op
        df_after = get_dataframe()
        assert len(df_before) == len(df_after)

    def test_get_dataframe_before_load_raises(self, monkeypatch):
        """If the module-level _df is None, get_dataframe must raise."""
        monkeypatch.setattr(loader, "_df", None)
        with pytest.raises(RuntimeError):
            get_dataframe()

    def test_get_heatmap_cache_before_load_raises(self, monkeypatch):
        monkeypatch.setattr(loader, "_heatmap_cache", None)
        with pytest.raises(RuntimeError):
            get_heatmap_cache()

    def test_get_analytics_cache_before_load_raises(self, monkeypatch):
        monkeypatch.setattr(loader, "_analytics_cache", None)
        with pytest.raises(RuntimeError):
            get_analytics_cache()


# ---------------------------------------------------------------------------
# Heatmap cache + weight formula
# ---------------------------------------------------------------------------

class TestHeatmapCache:
    def test_heatmap_cache_is_non_empty(self):
        cache = get_heatmap_cache()
        assert isinstance(cache, list)
        assert len(cache) > 0

    def test_heatmap_point_shape(self):
        cache = get_heatmap_cache()
        point = cache[0]
        assert set(point.keys()) == {"lat", "lng", "weight"}

    def test_heatmap_weights_are_positive_floats(self):
        # The cache divides a 1440-capped resolution by the real dataset max
        # (~1437), so High-priority weights can marginally exceed 2.0.
        # True invariant: weight <= 2 * (1440 / max_res).
        from backend.data import loader as L
        upper = 2.0 * (1440.0 / L._heatmap_max_res)
        cache = get_heatmap_cache()
        for p in cache:
            assert isinstance(p["weight"], float)
            assert p["weight"] >= 0.0  # some historical rows compute to 0.0
            assert p["weight"] <= upper + 1e-3

    def test_heatmap_drops_zero_coordinates(self):
        cache = get_heatmap_cache()
        for p in cache:
            assert p["lat"] != 0.0
            assert p["lng"] != 0.0

    def test_compute_single_heatmap_point_high_priority(self):
        # High priority → base 2; factor = resolution / real dataset max_res
        from backend.data import loader as L
        point = _compute_single_heatmap_point(
            lat=12.97, lng=77.59, priority="High", resolution_minutes=720
        )
        assert point is not None
        assert point["weight"] == round(2.0 * (720 / L._heatmap_max_res), 4)

    def test_compute_single_heatmap_point_low_priority(self):
        from backend.data import loader as L
        point = _compute_single_heatmap_point(
            lat=12.97, lng=77.59, priority="Low", resolution_minutes=720
        )
        assert point is not None
        # Low → base 1
        assert point["weight"] == round(1.0 * (720 / L._heatmap_max_res), 4)

    def test_compute_single_heatmap_point_null_duration_uses_05_factor(self):
        # null / invalid resolution → 0.5 factor (matches _build_heatmap_cache)
        point = _compute_single_heatmap_point(
            lat=12.97, lng=77.59, priority="High", resolution_minutes=None
        )
        assert point is not None
        assert point["weight"] == round(2.0 * 0.5, 4)

    def test_compute_single_heatmap_point_zero_coords_returns_none(self):
        assert _compute_single_heatmap_point(
            lat=0, lng=0, priority="High", resolution_minutes=10
        ) is None
        assert _compute_single_heatmap_point(
            lat=None, lng=77.59, priority="High", resolution_minutes=10
        ) is None

    def test_compute_single_heatmap_point_over_1440_uses_fallback(self):
        # resolution > 1440 fails the `0 < x <= 1440` guard → 0.5 factor,
        # NOT a clamp to 1.0. This matches _compute_single_heatmap_point logic.
        point = _compute_single_heatmap_point(
            lat=12.97, lng=77.59, priority="High", resolution_minutes=99999
        )
        assert point is not None
        assert point["weight"] == round(2.0 * 0.5, 4)

    def test_compute_single_heatmap_point_case_insensitive_priority(self):
        high = _compute_single_heatmap_point(
            lat=12.97, lng=77.59, priority="HIGH", resolution_minutes=None
        )
        assert high["weight"] == round(2.0 * 0.5, 4)


# ---------------------------------------------------------------------------
# Analytics cache
# ---------------------------------------------------------------------------

class TestAnalyticsCache:
    def test_analytics_has_all_four_sections(self):
        analytics = get_analytics_cache()
        assert set(analytics.keys()) == {
            "volume_grid", "top_junctions", "corridor_durations",
            "planned_vs_unplanned",
        }

    def test_volume_grid_is_7x24(self):
        grid = get_analytics_cache()["volume_grid"]
        assert len(grid) == 7  # 7 days
        for row in grid:
            assert len(row) == 24  # 24 hours

    def test_volume_grid_non_negative(self):
        grid = get_analytics_cache()["volume_grid"]
        for row in grid:
            for val in row:
                assert val >= 0

    def test_top_junctions_max_15(self):
        junctions = get_analytics_cache()["top_junctions"]
        assert 0 < len(junctions) <= 15

    def test_top_junctions_sorted_desc(self):
        junctions = get_analytics_cache()["top_junctions"]
        counts = [j["count"] for j in junctions]
        assert counts == sorted(counts, reverse=True)

    def test_top_junctions_have_coords(self):
        for j in get_analytics_cache()["top_junctions"]:
            assert "junction" in j and "count" in j
            assert "lat" in j and "lng" in j
            assert isinstance(j["count"], int)

    def test_corridor_durations_has_three_ranks(self):
        corridors = get_analytics_cache()["corridor_durations"]
        assert len(corridors) == 3
        ranks = [c["corridor_rank"] for c in corridors]
        assert sorted(ranks) == [0, 1, 2]

    def test_corridor_durations_labels(self):
        corridors = get_analytics_cache()["corridor_durations"]
        labels = {c["corridor_rank"]: c["label"] for c in corridors}
        assert labels[0] == "Non-Corridor"
        assert labels[1] == "ORR Variant"
        assert labels[2] == "Named Corridor"

    def test_planned_vs_unplanned_shape(self):
        series = get_analytics_cache()["planned_vs_unplanned"]
        assert len(series) > 0
        for entry in series:
            assert "month" in entry
            assert "planned" in entry
            assert "unplanned" in entry
            assert isinstance(entry["planned"], int)
            assert isinstance(entry["unplanned"], int)

    def test_planned_vs_unplanned_months_sorted(self):
        series = get_analytics_cache()["planned_vs_unplanned"]
        months = [e["month"] for e in series]
        assert months == sorted(months)


# ---------------------------------------------------------------------------
# Lookups
# ---------------------------------------------------------------------------

class TestLookups:
    def test_junction_lookup_is_dict(self):
        lookup = get_junction_lookup()
        assert isinstance(lookup, dict)
        assert len(lookup) > 0
        # All values are positive ints
        for k, v in lookup.items():
            assert isinstance(v, int) and v > 0

    def test_corridor_counts_is_dict(self):
        counts = get_corridor_counts()
        assert isinstance(counts, dict)
        assert len(counts) > 0


# ---------------------------------------------------------------------------
# Corridor rank helper
# ---------------------------------------------------------------------------

class TestCorridorRank:
    def test_orr_variant_is_rank_1(self):
        assert _corridor_rank("ORR East 1") == 1
        assert _corridor_rank("ORR North 2") == 1

    def test_non_corridor_is_rank_0(self):
        assert _corridor_rank("Non-corridor") == 0
        assert _corridor_rank("") == 0

    def test_named_corridor_is_rank_2(self):
        assert _corridor_rank("MG Road") == 2
        assert _corridor_rank("Outer Ring Road") == 2

    def test_null_corridor_is_rank_0(self):
        assert _corridor_rank(None) == 0
        assert _corridor_rank(float("nan")) == 0


# ---------------------------------------------------------------------------
# Resolution minutes computation
# ---------------------------------------------------------------------------

class TestResolutionMinutes:
    def _df(self, **kwargs):
        base = {
            "start_datetime": ["2025-06-15T08:00:00"],
            "closed_datetime": [None],
            "resolved_datetime": [None],
        }
        base.update(kwargs)
        return pd.DataFrame(base)

    def test_uses_closed_datetime_when_present(self):
        df = self._df(closed_datetime=["2025-06-15T09:00:00"])
        res = _compute_resolution_minutes(df)
        assert math.isclose(res.iloc[0], 60.0)

    def test_falls_back_to_resolved_datetime(self):
        df = self._df(resolved_datetime=["2025-06-15T10:30:00"])
        res = _compute_resolution_minutes(df)
        assert math.isclose(res.iloc[0], 150.0)

    def test_returns_nan_when_both_absent(self):
        df = self._df()
        res = _compute_resolution_minutes(df)
        assert pd.isna(res.iloc[0])

    def test_closed_takes_precedence_over_resolved(self):
        df = self._df(
            closed_datetime=["2025-06-15T09:00:00"],
            resolved_datetime=["2025-06-15T10:00:00"],
        )
        res = _compute_resolution_minutes(df)
        assert math.isclose(res.iloc[0], 60.0)  # closed wins


# ---------------------------------------------------------------------------
# Live incident append
# ---------------------------------------------------------------------------

class TestAddLiveIncident:
    def test_appends_one_row_to_dataframe(self):
        before = len(get_dataframe())
        add_live_incident(
            {
                "lat": 12.97, "lng": 77.59,
                "event_type": "unplanned", "event_cause": "accident",
                "start_datetime": "2025-06-15T08:00:00",
            },
            {"priority": "High", "estimated_duration_minutes": 90},
        )
        after = len(get_dataframe())
        assert after == before + 1

    def test_appends_heatmap_point(self):
        cache_before = len(get_heatmap_cache())
        add_live_incident(
            {
                "lat": 12.97, "lng": 77.59,
                "event_type": "unplanned", "event_cause": "accident",
                "start_datetime": "2025-06-15T08:00:00",
            },
            {"priority": "High", "estimated_duration_minutes": 90},
        )
        cache_after = len(get_heatmap_cache())
        assert cache_after == cache_before + 1

    def test_appended_point_has_correct_coords(self):
        add_live_incident(
            {
                "lat": 12.345, "lng": 77.999,
                "event_type": "unplanned", "event_cause": "accident",
                "start_datetime": "2025-06-15T08:00:00",
            },
            {"priority": "Low", "estimated_duration_minutes": 30},
        )
        cache = get_heatmap_cache()
        last = cache[-1]
        assert last["lat"] == 12.345
        assert last["lng"] == 77.999

    def test_no_crash_when_dataset_not_loaded(self, monkeypatch):
        monkeypatch.setattr(loader, "_df", None)
        # Should warn + return, not raise
        add_live_incident(
            {"lat": 12.97, "lng": 77.59},
            {"priority": "High", "estimated_duration_minutes": 10},
        )
