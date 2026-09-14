import duckdb

con = duckdb.connect()


def show(label, sql, setup=None):
    if setup:
        con.execute(setup)
    try:
        rows = con.execute(sql).fetchall()
        out = repr(rows)
    except Exception as exc:
        out = "ERROR: " + type(exc).__name__ + ": " + str(exc).splitlines()[0]
    print(label + " => " + out)


print("F0 duckdb " + duckdb.__version__)
show("F1 TimeZone", "SELECT current_setting('TimeZone')")

show("F2 trunc type on DATE", "SELECT typeof(date_trunc('month', DATE '2017-03-14'))")
show("F3 trunc type on TIMESTAMP", "SELECT typeof(date_trunc('month', TIMESTAMP '2017-03-14 09:30:00'))")
show("F4 trunc on VARCHAR", "SELECT date_trunc('month', '2017-03-14')")

show("F5 generate_series DATE bounds",
     "SELECT count(*), min(g), max(g), typeof(min(g)) "
     "FROM generate_series(DATE '2016-09-01', DATE '2016-12-01', INTERVAL 1 MONTH) s(g)")
show("F6 range DATE bounds",
     "SELECT count(*), min(g), max(g), typeof(min(g)) "
     "FROM range(DATE '2016-09-01', DATE '2016-12-01', INTERVAL 1 MONTH) s(g)")
show("F7 series from day 31",
     "SELECT list(g) FROM generate_series(DATE '2017-01-31', DATE '2017-05-31', INTERVAL 1 MONTH) s(g)")
show("F8 month add clamps",
     "SELECT DATE '2017-01-31' + INTERVAL 1 MONTH + INTERVAL 1 MONTH, DATE '2017-01-31' + INTERVAL 2 MONTH")

show("F9 week start", "SELECT date_trunc('week', DATE '2017-03-14'), dayname(date_trunc('week', DATE '2017-03-14'))")
show("F10 week vs isoyear",
     "SELECT d, weekofyear(d), year(d), isoyear(d), date_trunc('week', d) "
     "FROM (SELECT unnest([DATE '2016-01-01', DATE '2017-01-01', DATE '2018-12-31']) AS d)")

show("F11 empty bounds",
     "SELECT (SELECT count(*) FROM generate_series(CAST(NULL AS TIMESTAMP), CAST(NULL AS TIMESTAMP), INTERVAL 1 MONTH)), "
     "(SELECT count(*) FROM generate_series(TIMESTAMP '2017-05-01', TIMESTAMP '2017-01-01', INTERVAL 1 MONTH)), "
     "(SELECT count(*) FROM generate_series(TIMESTAMP '2017-05-01', TIMESTAMP '2017-05-01', INTERVAL 1 MONTH))")

show("F12 try_cast spellings",
     "SELECT s, TRY_CAST(s AS TIMESTAMP), TRY_CAST(s AS DATE) FROM (SELECT unnest("
     "['2017-03-14','2017-03-14 09:30:00','14/03/2017','03/14/2017','2017-13-01','2017-02-30','20170314']) AS s)")

con.execute(
    "CREATE TABLE t AS SELECT * FROM (VALUES "
    "(TIMESTAMP '2016-09-04 10:00:00', 10.00), (TIMESTAMP '2016-10-02 11:00:00', 20.00), "
    "(TIMESTAMP '2016-12-05 09:00:00', 30.00), (TIMESTAMP '2017-01-09 09:00:00', 40.00), "
    "(NULL, 50.00)) v(ordered_at, amount)"
)
show("F13 group by alone",
     "SELECT date_trunc('month', ordered_at), count(*) FROM t GROUP BY 1 ORDER BY 1")
show("F14 left join from series",
     "WITH b AS (SELECT date_trunc('month', min(ordered_at)) lo, date_trunc('month', max(ordered_at)) hi FROM t), "
     "s AS (SELECT g AS period FROM b, generate_series(b.lo, b.hi, INTERVAL 1 MONTH) x(g)), "
     "d AS (SELECT date_trunc('month', ordered_at) m, count(*) n FROM t WHERE ordered_at IS NOT NULL GROUP BY 1) "
     "SELECT strftime(s.period, '%Y-%m'), coalesce(d.n, 0) FROM s LEFT JOIN d ON d.m = s.period ORDER BY 1")
show("F15 undated rows",
     "SELECT count(*) FILTER (WHERE ordered_at IS NULL), count(*) FROM t")

con.execute(
    "CREATE TABLE g AS SELECT * FROM (VALUES (TIMESTAMP '2016-09-04'), (TIMESTAMP '2016-10-02'), "
    "(TIMESTAMP '2017-02-05'), (TIMESTAMP '2017-03-01'), (TIMESTAMP '2017-07-01')) v(ordered_at)"
)
show("F16 longest missing run",
     "WITH b AS (SELECT date_trunc('month', min(ordered_at)) lo, date_trunc('month', max(ordered_at)) hi FROM g), "
     "s AS (SELECT x.g AS period FROM b, generate_series(b.lo, b.hi, INTERVAL 1 MONTH) x(g)), "
     "d AS (SELECT date_trunc('month', ordered_at) m, count(*) n FROM g GROUP BY 1), "
     "j AS (SELECT s.period, coalesce(d.n, 0) AS n FROM s LEFT JOIN d ON d.m = s.period), "
     "r AS (SELECT period, n, row_number() OVER (ORDER BY period) "
     "- row_number() OVER (PARTITION BY (n = 0) ORDER BY period) AS grp FROM j) "
     "SELECT count(*), count(*) FILTER (WHERE n > 0), count(*) FILTER (WHERE n = 0), "
     "(SELECT max(c) FROM (SELECT count(*) c FROM r WHERE n = 0 GROUP BY grp)) FROM j")

show("F17 tz trunc at UTC",
     "SELECT CAST(date_trunc('day', TIMESTAMPTZ '2017-03-14 23:30:00+00') AS VARCHAR)",
     setup="SET TimeZone='UTC'")
show("F18 tz trunc at Asia/Kolkata",
     "SELECT CAST(date_trunc('day', TIMESTAMPTZ '2017-03-14 23:30:00+00') AS VARCHAR), "
     "typeof(date_trunc('day', TIMESTAMPTZ '2017-03-14 23:30:00+00'))",
     setup="SET TimeZone='Asia/Kolkata'")
show("F19 plain timestamp under Asia/Kolkata",
     "SELECT CAST(date_trunc('day', TIMESTAMP '2017-03-14 23:30:00') AS VARCHAR)")

show("F20 day-grain series length",
     "SELECT count(*) FROM generate_series(TIMESTAMP '2016-09-01', TIMESTAMP '2018-10-01', INTERVAL 1 DAY)",
     setup="SET TimeZone='UTC'")
show("F21 strftime per grain",
     "SELECT strftime(TIMESTAMP '2017-03-14', '%Y'), strftime(TIMESTAMP '2017-03-14', '%Y-%m'), "
     "strftime(TIMESTAMP '2017-03-14', '%Y-%m-%d'), strftime(TIMESTAMP '2017-03-14', '%Y-Q') "
     "|| quarter(TIMESTAMP '2017-03-14')")
