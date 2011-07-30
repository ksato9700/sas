## -*- coding: utf-8 -*-
##
## Copyright 2011 Kenichi Sato <ksato9700@gmail.com>
##
<%page />
<%
success_url, fail_url = args
%>
<html>
<head>
<title>Sign-in Page</title>
</head>
<body>
  <h2>Sign-in</h2>
  <form method="POST" action="/signin_submit">
    <input type="hidden" name="success_url" value="${success_url}" />
    <input type="hidden" name="fail_url" value="${fail_url}" />
    <input type="text" name="username" value="" />
    <input type="password" name="password" value="" />
    <input type="submit" name="signin" value="Sign-in" />
    <input type="submit" name="cancel" value="Cancel" />
  </form>
</body>
</html>
