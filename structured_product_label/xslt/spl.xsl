<?xml version="1.0" encoding="ASCII"?>
<!--
The contents of this file are subject to the Health Level-7 Public
License Version 1.0 (the "License"); you may not use this file
except in compliance with the License. You may obtain a copy of the
License at http://www.hl7.org/HPL/hpl.txt.

Software distributed under the License is distributed on an "AS IS"
basis, WITHOUT WARRANTY OF ANY KIND, either express or implied. See
the License for the specific language governing rights and
limitations under the License.

The Original Code is all this file.

The Initial Developer of the Original Code is Gunther Schadow.
Portions created by Initial Developer are Copyright (C) 2002-2004
Health Level Seven, Inc. All Rights Reserved.

Contributor(s): Steven Gitterman, Brian Keller

Revision: $Id: spl.xsl,v 1.52 2005/08/26 05:59:26 gschadow Exp $

Revision: $Id: spl-common.xsl,v 2.0 2006/08/18 04:11:00 sbsuggs Exp $

-->
<xsl:transform version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xmlns:v3="urn:hl7-org:v3" exclude-result-prefixes="v3 xsl">
	<xsl:import href="spl-common.xsl"/>
	<!-- Whether to show the clickable XML, set to "/.." instead of "1" to turn off -->
	<xsl:param name="show-subjects-xml" select="/.."/>
	<!-- Whether to show the data elements in special tables etc., set to "/.." instead of "1" to turn off -->
	<xsl:param name="show-data" select="1"/>
	<!-- This is the CSS link put into the output -->
	<xsl:param name="css">http://www.accessdata.fda.gov/spl/stylesheet/spl.css</xsl:param>
	<!-- Whether to show section numbers, set to 1 to enable and "/.." to turn off-->
	<xsl:param name="show-section-numbers" select="/.."/>
	<xsl:output method="html" version="1.0" encoding="UTF-8" indent="yes"/>
	<xsl:strip-space elements="*"/>
</xsl:transform>
