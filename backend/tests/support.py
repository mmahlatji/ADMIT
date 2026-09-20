"""Shared test plumbing for router tests."""


def request_scoped_db(session):
    """A get_db override that keeps the real request's transaction semantics.

    The production get_db commits when a request succeeds and rolls back when
    it raises. Overriding it with a bare `yield session` keeps neither, so
    nothing in the suite could tell a working transaction from a broken one:
    a query module committing behind get_db's back, and get_db losing its
    rollback, both still looked like a passing test.

    A savepoint rather than the session's own transaction, because a test has
    usually set rows up before the request runs. In production those rows are
    already committed and a rolled back request leaves them alone. Here they
    are still pending on the outer transaction, and the savepoint is what
    gives them that same treatment.
    """

    def _override():
        nested = session.begin_nested()
        try:
            yield session
            nested.commit()
        except BaseException:
            nested.rollback()
            raise

    return _override
