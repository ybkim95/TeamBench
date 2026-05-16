# GH1: Fix Session Handling in Test Client

The test client's session data is lost when following redirects.
Users report that session values set during a request are not available
when the response redirects to another endpoint.

Fix the test client code in `testclient.py` so that session state
persists across redirects during testing.
