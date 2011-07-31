## -*- coding: utf-8 -*-
##
## Copyright 2011 Kenichi Sato <ksato9700@gmail.com>
##
<%page />
<%
baseurl, userid = args
%>
<html>
<head>
<link rel="openid.server" href="${baseurl}/openidserver">
<meta http-equiv="x-xrds-location" content="${baseurl}/yadis/${userid}">
<title>Id</title>
</head>
<body>
</body>
</html>
