# -*- coding: utf-8 -*-
##
## Copyright 2011 Kenichi Sato <ksato9700@gmail.com>
##
<%page />
<%
id_url_base, userid, identity, idselect, trust_root = args
assert (identity.startswith(id_url_base) or idselect), repr((identity, id_url_base))
expected_user = int(identity[len(id_url_base):])
%>
<html>
<head>
<title>Approve OpenID request?</title>
</head>
<body>
<form method="POST" action="/allow">
  <table>
    <tr><td>Identity:</td>

%if idselect:
      <td>${id_url_base}<input type='text' name='identifier'></td></tr>
%else:
      <td>${identity}</td></tr>
%endif
    <tr><td>Trust Root:</td><td>${trust_root}</td></tr>
  </table>
  <p>Allow this authentication to proceed?</p>
  <input type="checkbox" id="remember" name="remember" value="yes"
         /><label for="remember">Remember this decision</label><br />
%if not idselect and expected_user != userid:
  <input type="hidden" name="login_as" value="${expected_user}"/>
%endif
  <input type="submit" name="yes" value="yes" />
  <input type="submit" name="no" value="no" />
</form>

</body>
</html>
