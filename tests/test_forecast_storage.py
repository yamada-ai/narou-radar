from datetime import date

from app.storage.duckdb_repo import DuckDBRepository


def test_store_forecast_upserts_by_unique_key(tmp_path) -> None:
    db = tmp_path / "test.duckdb"
    repo = DuckDBRepository(str(db))
    repo.migrate()

    repo.store_forecast("exile", "avg_weekly", [(date(2026, 4, 4), 10.0)], "seasonal_naive")
    repo.store_forecast("exile", "avg_weekly", [(date(2026, 4, 4), 12.5)], "seasonal_naive")

    row = repo.conn.execute(
        """
        select count(*) as c, max(yhat) as y
        from forecast_results
        where theme='exile' and metric='avg_weekly' and ds='2026-04-04' and model='seasonal_naive'
        """
    ).fetchone()
    repo.close()

    assert row[0] == 1
    assert float(row[1]) == 12.5
