## -*- coding: utf-8 -*-
##
## Copyright 2011 Kenichi Sato <ksato9700@gmail.com>
##
<%page />
<%
baseurl, userid, types = args
%>
<?xml version="1.0" encoding="UTF-8"?>
<xrds:XRDS
   xmlns:xrds="xri://$xrds"
   xmlns="xri://$xrd*($v*2.0)">
  <XRD>
    <Service priority="0">
%for type in types:
      <Type>${type}</Type>
%endfor
      <URI>${baseurl + "/openidserver"}</URI>
      <LocalID>${baseurl + "/id/" + userid}</LocalID>
    </Service>
  </XRD>
</xrds:XRDS>
