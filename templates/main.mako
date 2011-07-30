## -*- coding: utf-8 -*-
##
## Copyright 2011 Kenichi Sato <ksato9700@gmail.com>
##
<%page />
<%
sas, userid, username, handle = args
%>
<html>
<head>
<meta http-equiv="x-xrds-location" content="${sas.baseurl}/serveryadis">
<title>Main</title>
</head>
<body>
<table border="0">
<tr><td>Username</td><td>${username}</td></tr>
<tr><td>Handle</td><td>${handle}</td></tr>
<tr><td>OpenID URL</td><td>${sas.baseurl}/id/${userid}</td></tr>
</table>

<form method="POST" action="/signin_submit">
  <input type="hidden" name="success_url" value="/" />
  <input type="hidden" name="fail_url" value="/" />
  <input type="submit" name="signout" value="Sign-out" />
</form>

</body>
</html>
