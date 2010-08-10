<?xml version="1.0" encoding="ASCII"?>
<?xml-stylesheet href="..//Documentation/xsltdoc.xsl" type="text/xsl" media="screen"?>
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

Contributor(s): Steven Gitterman, Brian Keller, Brian Suggs

Revision: $Id: spl-common.xsl,v 1.5 2005/10/07 17:14:07 gschadow Exp $

Revision: $Id: spl-common.xsl,v 1.5 2006/02/15 16:50:07 sbsuggs Exp $

Revision: $Id: spl-common.xsl,v 2.0 2006/08/24 04:11:00 sbsuggs Exp $

TODO: footnote styleCode Footnote, Endnote not yet obeyed
TODO: Implementation guide needs to define linkHtml styleCodes.
-->
<xsl:transform version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xmlns:v3="urn:hl7-org:v3"  xmlns:str="http://exslt.org/strings" xmlns:exsl="http://exslt.org/common" xmlns:msxsl="urn:schemas-microsoft-com:xslt"
	xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" exclude-result-prefixes="exsl msxsl v3 xsl xsi">
	<xsl:import href="xml-verbatim.xsl"/>
	<xsl:param name="show-subjects-xml" select="1"/>
	<xsl:param name="show-data" select="/.."/>
	<xsl:param name="show-section-numbers" select="/.."/>
	<xsl:param name="update-check-url-base" select="/.."/>
	<xsl:param name="standardSections" select="document('plr-sections.xml')/*"/>
	<xsl:param name="documentTypes" select="document('doc-types.xml')/*"/>	
	<xsl:param name="css" select="'./spl.css'"/>
	<xsl:output method="html" version="1.0" encoding="UTF-8" indent="no"/>
	<xsl:strip-space elements="*"/>
	<xsl:variable name="numHighlightSections"
		select="number(count(//v3:section[descendant::v3:highlight and not(ancestor::v3:section) and not(./v3:code[descendant-or-self::*[(self::v3:code or self::v3:translation) and @codeSystem='2.16.840.1.113883.6.1' and @code='34066-1' or @code='43683-2' or @code='49489-8']])]/v3:excerpt) )"/>
	<!-- The indication secction variable contains the actual Indication Section node-->
	<xsl:variable name="indicationSection"
		select="/v3:document/v3:component/v3:structuredBody/v3:component//v3:section [v3:code [descendant-or-self::* [(self::v3:code or self::v3:translation) and @codeSystem='2.16.840.1.113883.6.1' and @code='34067-9'] ] ]"/>
	<xsl:variable name="indicationSectionCode">34067-9</xsl:variable>
	<xsl:variable name="dosageFormsAndStrengthsSectionCode">43678-2</xsl:variable>
	<xsl:variable name="dosageAndAdministrationSectionCode">34068-7</xsl:variable>
	<xsl:variable name="contraindicatonsSectionCode">34070-3</xsl:variable>
	<xsl:variable name="warningsAndPrecautionsSectionCode">43685-7</xsl:variable>
	<xsl:variable name="boxedWarningSectionCode">34066-1</xsl:variable>
	<xsl:variable name="currentLoincCode" select="v3:document/v3:code/@code"/>	
	<xsl:variable name="gSr4" select="boolean(count(//v3:manufacturedProduct/v3:manufacturedProduct)) or v3:document/v3:code/@code = '51726-8'  or v3:document/v3:code/@code = '51725-0' "/>
	<xsl:variable name="gSr3" select="boolean(count(//v3:manufacturedProduct/v3:manufacturedMedicine))"/>
	<xsl:template match="/">
		<html>
			<head>
				<title>
					<xsl:value-of select="v3:document/v3:title"/>
				</title>
				<link rel="stylesheet" type="text/css" href="{$css}"/>
				<xsl:if test="$show-subjects-xml">
					<xsl:call-template name="xml-verbatim-setup"/>
				</xsl:if>
			</head>
			<body>		
				<xsl:apply-templates mode="title" select="v3:document"/>
				<xsl:if test="not($gSr4) and string-length(v3:document/v3:title) &gt; 1">
					<h1>
						<!-- PCR 807 -->
						<xsl:apply-templates mode="mixed" select="/v3:document/v3:title"></xsl:apply-templates>
					</h1>
				</xsl:if>
				<xsl:choose>
					<xsl:when test="$numHighlightSections > 0">	
						<xsl:call-template name="highlights"/>
						<xsl:call-template name="index"/>
						<strong>FULL PRESCRIBING INFORMATION</strong>
					</xsl:when>
					<xsl:when test="boolean($gSr4)">		
						 <strong><xsl:apply-templates mode="mixed" select="/v3:document/v3:title"></xsl:apply-templates></strong>
					</xsl:when>
				</xsl:choose>
				
				
				<xsl:apply-templates select="@*|node()"/>
				<xsl:call-template name="PLRIndications"/>
				<xsl:call-template name="PLRInteractions"/>
				<xsl:call-template name="PharmacologicalClass"/>
				<br/>
				<xsl:apply-templates mode="subjects" select="/v3:document"/>
				
				<xsl:if test="boolean($gSr4)">
					
				<xsl:apply-templates mode="subjects" select="//v3:author/v3:assignedEntity/v3:representedOrganization"/>
				<xsl:apply-templates mode="subjects" select="//v3:author/v3:assignedEntity/v3:representedOrganization/v3:assignedEntity/v3:assignedOrganization"/>
				<xsl:apply-templates mode="subjects" select="//v3:author/v3:assignedEntity/v3:representedOrganization/v3:assignedEntity/v3:assignedOrganization/v3:assignedEntity/v3:assignedOrganization"/>
					
				</xsl:if>
				
				<xsl:call-template name="effectiveDate"/>
				
				<xsl:call-template name="distributorName"/>
				
				<xsl:if test="$show-subjects-xml">
					<hr/>
					<div class="Subject" onclick="xmlVerbatimClick(event);" ondblclick="xmlVerbatimDblClick(event);">
						<xsl:apply-templates mode="xml-verbatim" select="node()"/>
					</div>
				</xsl:if>
			</body>
		</html>
	</xsl:template>
	<!-- helper templates -->
	<xsl:template name="string-lowercase">
		<!--** Convert the input text that is passed in as a parameter to lower case  -->
		<xsl:param name="text"/>
		<xsl:value-of select="translate($text,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz')"/>
	</xsl:template>
	<xsl:template name="string-uppercase">
		<!--** Convert the input text that is passed in as a parameter to upper case  -->
		<xsl:param name="text"/>
		<xsl:value-of select="translate($text,'abcdefghijklmnopqrstuvwxyz','ABCDEFGHIJKLMNOPQRSTUVWXYZ')"/>
	</xsl:template>
	<xsl:template name="printSeperator">
		<!--** Print an ampercent-->
		<xsl:param name="currentPos" select="position()"/>
		<xsl:param name="lastPos" select="last()"/>
		<xsl:param name="lastDelimiter">and</xsl:param>
		<xsl:choose>
			<xsl:when test="number($currentPos) = number($lastPos)-1"><xsl:value-of select="$lastDelimiter"/>&#160;</xsl:when>
			<xsl:when test="number($currentPos) &lt; number($lastPos)-1">,&#160;</xsl:when>
		</xsl:choose>
	</xsl:template>
	<xsl:template name="string-to-date">
		<xsl:param name="text"/>
		<xsl:param name="displayMonth">true</xsl:param>
		<xsl:param name="displayDay">true</xsl:param>
		<xsl:param name="displayYear">true</xsl:param>
		<xsl:param name="delimiter">/</xsl:param>
		<xsl:if test="string-length($text) > 7">
			<xsl:variable name="year" select="substring($text,1,4)"/>
			<xsl:variable name="month" select="substring($text,5,2)"/>
			<xsl:variable name="day" select="substring($text,7,2)"/>
			<!-- changed by Brian Suggs 11-13-05.  Changes made to display date in MM/DD/YYYY format instead of DD/MM/YYYY format -->
			<xsl:if test="$displayMonth = 'true'">
				<xsl:value-of select="$month"/>
				<xsl:value-of select="$delimiter"/>
			</xsl:if>
			<xsl:if test="$displayDay = 'true'">
				<xsl:value-of select="$day"/>
				<xsl:value-of select="$delimiter"/>
			</xsl:if>
			<xsl:if test="$displayYear = 'true'">
				<xsl:value-of select="$year"/>
			</xsl:if>
		</xsl:if>
	</xsl:template>
	<xsl:template mode="format" match="*/v3:addr">
		<table>
			<tr><td>Address:</td><td><xsl:value-of select="./v3:streetAddressLine"/></td></tr>
			<tr><td>City, State, Zip:</td>
				<td>
					<xsl:value-of select="./v3:city"/>
					<xsl:if test="string-length(./v3:state)>0">,&#160;<xsl:value-of select="./v3:state"/></xsl:if>
					<xsl:if test="string-length(./v3:postalCode)>0">,&#160;<xsl:value-of select="./v3:postalCode"/></xsl:if>
				</td>
			</tr>
			<tr><td>Country:</td><td><xsl:value-of select="./v3:country"/></td></tr>
		</table>
	</xsl:template>
	<!-- MAIN MODE based on the deep null-transform -->
	<xsl:template match="@*|node()">
		<xsl:apply-templates select="@*|node()"/>
	</xsl:template>
	<!-- MODE HIGHLIGHTS -->
	<xsl:template name="highlights">
		<table class="textHighlights">
			<tbody>
				<tr>
					<td width="50%" class="textHighlights" align="justify" vAlign="top">
						<table cellSpacing="1" cellPadding="3">
							<tbody>
								<tr>
									<td colSpan="2">
										<strong>HIGHLIGHTS OF PRESCRIBING INFORMATION</strong>
									</td>
								</tr>
								<!-- see PCR 801, starting version 4, we don't display this template text, we display the title instead -->
								<xsl:if test="not(boolean($gSr4))">
								<tr>
									<td align="justify" vAlign="top">		
										<xsl:variable name="medName">
											<xsl:call-template name="string-uppercase">
												<xsl:with-param name="text">
													<xsl:copy>
														<xsl:apply-templates mode="specialCus"
															select="//v3:subject[1]/v3:manufacturedProduct/v3:manufacturedMedicine/v3:name|//v3:subject[1]/v3:manufacturedProduct/v3:manufacturedProduct/v3:name"
														/>
													</xsl:copy>
												</xsl:with-param>
											</xsl:call-template>
										</xsl:variable>
										<strong>These highlights do not include all the information needed to use <xsl:value-of select="$medName"/>
											safely and effectively. See full prescribing information for <xsl:value-of select="$medName"
											/>.</strong>
									</td>
								</tr>
								</xsl:if>
								<tr>
									<td>
								<xsl:choose>
									<xsl:when test="boolean($gSr4)">								
										<strong><xsl:apply-templates mode="mixed" select="/v3:document/v3:title"></xsl:apply-templates></strong>
									</xsl:when>
									<xsl:otherwise>
										<xsl:for-each select=".//v3:subject[v3:manufacturedProduct[v3:manufacturedMedicine|v3:manufacturedProduct]]">											
											<xsl:variable name="prevProductTitleString">
												<xsl:for-each select="preceding::v3:manufacturedProduct/v3:manufacturedMedicine|preceding::v3:manufacturedProduct/v3:manufacturedProduct">
													<xsl:call-template name="titleString">
														<xsl:with-param name="curProduct" select="." />
													</xsl:call-template>
												</xsl:for-each>
											</xsl:variable>
											<xsl:variable name="curProductTitleString"><xsl:call-template name="titleString"><xsl:with-param name="curProduct" select="./v3:manufacturedProduct/v3:manufacturedMedicine|./v3:manufacturedProduct/v3:manufacturedProduct" /></xsl:call-template></xsl:variable>
											<xsl:choose>
												<xsl:when test="position() > 1 and contains($prevProductTitleString, $curProductTitleString)"/>
												<xsl:otherwise>
													<xsl:if test="position() > 1">
														<br/>
													</xsl:if>
													<strong>
																<xsl:apply-templates mode="hlMedNames" select="./v3:manufacturedProduct/v3:manufacturedMedicine|./v3:manufacturedProduct/v3:manufacturedProduct"/> for <!-- PCR 669  -->
																<xsl:variable name="iNumberOfRouteCodes" select="count(./v3:manufacturedProduct/v3:consumedIn/v3:substanceAdministration/v3:routeCode)"/>
																<xsl:for-each select="./v3:manufacturedProduct/v3:consumedIn/v3:substanceAdministration/v3:routeCode">																																	
																	<xsl:if test="(position()=last()) and ($iNumberOfRouteCodes>1)"> and </xsl:if>
																	<xsl:call-template name="string-lowercase">
																		<xsl:with-param name="text" select="@displayName"/>
																	</xsl:call-template>
																	<xsl:if test="(last() - position() > 1) and ($iNumberOfRouteCodes>1)">, </xsl:if>
																</xsl:for-each>
																use <xsl:if test="./v3:manufacturedProduct/v3:subjectOf/v3:policy/v3:code/@displayName != ''"> - <xsl:value-of
																	select="./v3:manufacturedProduct/v3:subjectOf/v3:policy/v3:code/@displayName"/></xsl:if>
														
													</strong>
												</xsl:otherwise>
											</xsl:choose>
										</xsl:for-each>
									</xsl:otherwise>
								</xsl:choose>
										<br/>
											<xsl:choose>
												<xsl:when test="boolean($gSr4)">
												</xsl:when>
												<xsl:otherwise>
													<xsl:choose>
														<xsl:when test="/v3:document/v3:component/v3:structuredBody/v3:component/v3:section/v3:subject/v3:manufacturedProduct/v3:subjectOf/v3:approval/v3:author/v3:time/@value">															
															<strong>Initial U.S. Approval:	
															<xsl:value-of select="/v3:document/v3:component/v3:structuredBody/v3:component/v3:section/v3:subject/v3:manufacturedProduct/v3:subjectOf/v3:approval/v3:author/v3:time/@value"/>
															</strong>
														</xsl:when>
														<xsl:when test="/v3:document/v3:verifier/v3:time/@value">															
															<strong>Initial U.S. Approval:	
																<xsl:value-of select="/v3:document/v3:verifier/v3:time/@value"/>
															</strong>
														</xsl:when>
													</xsl:choose>
												</xsl:otherwise>				
											</xsl:choose>
										<br/>
										<xsl:if test="//v3:section[descendant::v3:highlight and ./v3:code[descendant-or-self::*[(self::v3:code or self::v3:translation) and @codeSystem='2.16.840.1.113883.6.1' and @code='49489-8']]]/v3:excerpt"><br/></xsl:if>
										
										<p>
										<xsl:apply-templates mode="mixed" select="//v3:section[descendant::v3:highlight and ./v3:code[descendant-or-self::*[(self::v3:code or self::v3:translation) and @codeSystem='2.16.840.1.113883.6.1' and @code='49489-8']]]/v3:excerpt"/> 
										</p>
									</td>
								</tr>
								<xsl:for-each
									select="//v3:section[descendant::v3:highlight and not(ancestor::v3:section) and ./v3:code[descendant-or-self::*[(self::v3:code or self::v3:translation) and @codeSystem='2.16.840.1.113883.6.1' and @code='34066-1']]]/v3:excerpt">
									<tr>
										<td align="justify" vAlign="top" class="Warning">
											<xsl:for-each select="v3:highlight/v3:text/node()[not(self::v3:title)]">
												<xsl:choose>
													<xsl:when test="position() &lt; 3">
														<h1 class="Warning">
															<xsl:apply-templates mode="mixed" select="."/>
														</h1>
													</xsl:when>
													<xsl:otherwise>
														<xsl:apply-templates mode="mixed" select="."/>
													</xsl:otherwise>
												</xsl:choose>
											</xsl:for-each>
										</td>
									</tr>
								</xsl:for-each>
								<xsl:apply-templates mode="highlights"
									select="//v3:section[descendant::v3:highlight/v3:text and not(ancestor::v3:section) and ./v3:code[@codeSystem='2.16.840.1.113883.6.1' and @code='43683-2']]/v3:excerpt"/>
								<xsl:for-each
									select="//v3:section[descendant::v3:highlight/v3:text and not(ancestor::v3:section) and not(./v3:code[@codeSystem='2.16.840.1.113883.6.1' and (@code='34066-1' or @code='43683-2' or @code='49489-8')])]/v3:excerpt">
									
									<xsl:apply-templates mode="highlights" select="."/>
								</xsl:for-each>
								<tr>
									<xsl:variable name="sectionNumberSequence">
										<xsl:apply-templates mode="sectionNumber" select="//v3:section[v3:code/@code = '34076-0']"/>
									</xsl:variable>
									<td align="justify" vAlign="top">
										<strong>
											<xsl:choose>
												<xsl:when
													test="count(//v3:section[v3:code/@code = '34076-0']) > 0 and (count(//v3:section[v3:code/@code = '42231-1']) = 0 and count(//v3:section[v3:code/@code = '38056-8']) = 0 and count(//v3:section[v3:code/@code = '42230-3']) = 0)">
													<br/>See <a href="#section-{substring($sectionNumberSequence,2)}">17</a> for PATIENT COUNSELING INFORMATION </xsl:when>
												<xsl:when
													test="count(//v3:section[v3:code/@code = '34076-0']) > 0 and (count(//v3:section[v3:code/@code = '38056-8']) > 0 or count(//v3:section[v3:code/@code = '42230-3']) > 0) and count(//v3:section[v3:code/@code = '42231-1']) = 0">
													<br/>See <a href="#section-{substring($sectionNumberSequence,2)}">17</a> for PATIENT COUNSELING INFORMATION and FDA-approved patient labeling </xsl:when>
												<xsl:when
													test="(count(//v3:section[v3:code/@code = '34076-0']) > 0 and count(//v3:section[v3:code/@code = '42231-1']) > 0) and (count(//v3:section[v3:code/@code = '38056-8']) = 0 or count(//v3:section[v3:code/@code = '42230-3']) = 0)">
													<br/>See <a href="#section-{substring($sectionNumberSequence,2)}">17</a> for PATIENT COUNSELING INFORMATION and Medication Guide </xsl:when>
												<xsl:when
													test="count(//v3:section[v3:code/@code = '34076-0']) > 0 and count(//v3:section[v3:code/@code = '42231-1']) > 0 and count(//v3:section[v3:code/@code = '38056-8']) > 0 and count(//v3:section[v3:code/@code = '42230-3']) > 0">
													<br/>See <a href="#section-{substring($sectionNumberSequence,2)}">17</a> for PATIENT COUNSELING INFORMATION and Medication Guide </xsl:when>
											</xsl:choose>
										</strong>
									</td>
								</tr>
								<tr>
									<td align="right" vAlign="top">
										<br/>
										<strong>
											<xsl:call-template name="effectiveDateHighlights"/>
										</strong>
									</td>
								</tr>
							</tbody>
						</table>
					</td>
				</tr>
			</tbody>
		</table>
		<hr/>
	</xsl:template>	
	<xsl:template name="headerString">
		<xsl:param name="curProduct">.</xsl:param>
		GSG
		<xsl:value-of select="$curProduct/v3:name"/>
		<xsl:value-of select="$curProduct/v3:formCode/@code"/>
		<xsl:choose>
			<xsl:when test="$curProduct/v3:part">
				<xsl:value-of select="$curProduct/v3:asEntityWithGeneric/v3:genericMedicine/v3:name"/>
			</xsl:when>
			<xsl:otherwise>
				<xsl:for-each select="$curProduct/v3:ingredient[@classCode='ACTIM']">
					<xsl:call-template name="string-lowercase">
						<xsl:with-param name="text"
							select="v3:ingredientSubstance/v3:name"
						/>
					</xsl:call-template> 
				</xsl:for-each>
				<xsl:for-each select="$curProduct/v3:activeIngredient">
					<xsl:call-template name="string-lowercase">
						<xsl:with-param name="text"
							select="v3:activeIngredientSubstance/v3:name"
						/>
					</xsl:call-template> 
				</xsl:for-each>
			</xsl:otherwise>
		</xsl:choose>		
		GEG
	</xsl:template>	
	<xsl:template name="regMedNames">	
		<xsl:variable name="medName">
			<xsl:call-template name="string-uppercase">
				<xsl:with-param name="text">
					<xsl:copy><xsl:apply-templates mode="specialCus" select="./v3:name" /></xsl:copy>
				</xsl:with-param>
			</xsl:call-template>
		</xsl:variable>
		<xsl:value-of select="$medName"/>
		<xsl:if test="./v3:name/v3:suffix">&#160;</xsl:if>
		<xsl:call-template name="string-uppercase">
			<xsl:with-param name="text"
				select="./v3:name/v3:suffix"/>
		</xsl:call-template> 
		 - 
		<xsl:choose>
			<xsl:when test="./v3:activeIngredient">
				<xsl:for-each select="./v3:activeIngredient">
					<xsl:choose>
						<xsl:when test="position() > 1 and position() = last()"> and
						</xsl:when>				
						<xsl:when test="position() > 1">,
						</xsl:when>
					</xsl:choose>
					<xsl:call-template name="string-lowercase">
						<xsl:with-param name="text"
							select="v3:activeIngredientSubstance/v3:name"
						/>
					</xsl:call-template> 
				</xsl:for-each>
			</xsl:when>
			<xsl:when test="./v3:ingredient[@classCode!='IACT']">
				<xsl:for-each select="./v3:ingredient[@classCode!='IACT']">
					<xsl:choose>
						<xsl:when test="position() > 1 and  position() = last()"> and
						</xsl:when>				
						<xsl:when test="position() > 1">,
						</xsl:when>
					</xsl:choose>
					<xsl:call-template name="string-lowercase">
						<xsl:with-param name="text"
							select="v3:ingredientSubstance/v3:name"
						/>
					</xsl:call-template> 
				</xsl:for-each>
			</xsl:when>
			<xsl:otherwise>
				<xsl:variable name="genMedName">
					<xsl:call-template name="string-uppercase">
						<xsl:with-param name="text"
							select="./v3:asEntityWithGeneric/v3:genericMedicine/v3:name"
						/>
					</xsl:call-template>
				</xsl:variable>
				<xsl:choose>
					<xsl:when test="$medName != $genMedName">
						<xsl:call-template name="string-lowercase">
							<xsl:with-param name="text"
								select="$genMedName"
							/>
						</xsl:call-template> 
					</xsl:when>
					<xsl:otherwise>&#160;</xsl:otherwise>
				</xsl:choose>&#160;
			</xsl:otherwise>
		</xsl:choose>&#160;<xsl:if test="not(v3:part)">
			<xsl:call-template name="string-lowercase">
				<xsl:with-param name="text"
					select="./v3:formCode/@displayName"/>
			</xsl:call-template>
			<xsl:text>&#160;</xsl:text>
		</xsl:if>
	</xsl:template>	
	<xsl:template name="titleString">
		<xsl:param name="curProduct">.</xsl:param>
		GSG
		<xsl:value-of select="$curProduct/v3:name"/>
		<xsl:value-of select="$curProduct/v3:formCode/@code"/>
		<xsl:value-of select="$curProduct/v3:asEntityWithGeneric/v3:genericMedicine/v3:name"/>
		GEG
	</xsl:template>	
	<xsl:template name="hlMedNames" mode="hlMedNames" match="*">	
		<xsl:variable name="medName">
			<xsl:call-template name="string-uppercase">
				<xsl:with-param name="text">
					<xsl:copy><xsl:apply-templates mode="specialCus" select="./v3:name" /></xsl:copy>
				</xsl:with-param>
			</xsl:call-template>
		</xsl:variable>
		<xsl:variable name="genMedName">
			<xsl:call-template name="string-uppercase">
				<xsl:with-param name="text"
					select="./v3:asEntityWithGeneric/v3:genericMedicine/v3:name"
				/>
			</xsl:call-template>
		</xsl:variable>
		<xsl:value-of select="$medName"/>
		<xsl:choose>
			<xsl:when test="$medName != $genMedName">
				(<xsl:call-template name="string-lowercase">
					<xsl:with-param name="text"
						select="$genMedName"
					/>
				</xsl:call-template>) 
			</xsl:when>
			<xsl:otherwise>&#160;</xsl:otherwise>
		</xsl:choose>
		<xsl:call-template name="string-lowercase">
			<xsl:with-param name="text"
				select="./v3:formCode/@displayName"/>
		</xsl:call-template>
	</xsl:template>
	<xsl:template name="piMedNames" mode="piMedNames" match="*">		
		<xsl:variable name="medName">
			<xsl:call-template name="string-uppercase">
				<xsl:with-param name="text">
					<xsl:copy><xsl:apply-templates mode="specialCus" select="./v3:name" /></xsl:copy>
				</xsl:with-param>
			</xsl:call-template>
		</xsl:variable>
		<xsl:variable name="genMedName">
			<xsl:call-template name="string-uppercase">
				<xsl:with-param name="text"
					select="./v3:asEntityWithGeneric/v3:genericMedicine/v3:name"
				/>
			</xsl:call-template>
		</xsl:variable>		
		
		<tr>
			<td class="contentTableTitle">
				<strong>
					<xsl:value-of select="$medName"/>&#160;		
					<xsl:call-template name="string-uppercase">
						<xsl:with-param name="text"
							select="./v3:name/v3:suffix"/>
					</xsl:call-template>	
				</strong>
				<br/>
				<font class="contentTableReg">
						<xsl:call-template name="string-lowercase">
							<xsl:with-param name="text"
								select="$genMedName"
							/>
						</xsl:call-template>&#160;
				<xsl:call-template name="string-lowercase">
					<xsl:with-param name="text"
						select="./v3:formCode/@displayName"/>
				</xsl:call-template>
				</font>	
			</td>
		</tr>
	</xsl:template>
	<xsl:template mode="specialCus" match="v3:name">
		<xsl:value-of select="text()"/>
	</xsl:template>	
	<xsl:template mode="highlights" match="/|@*|node()">
		<xsl:param name="class" select="."/>
		<xsl:apply-templates mode="highlights" select="@*|node()">
			<xsl:with-param name="class" select="$class"/>
		</xsl:apply-templates>
	</xsl:template>
	<xsl:template mode="highlights" match="v3:excerpt">
		<!--**Generates the highlights of the PLR.  -->
		<xsl:variable name="currentCode" select="ancestor::v3:section//v3:code/@code"/>
		<xsl:variable name="standardSection" select="$standardSections//v3:section[@code=$currentCode]"/>
		<xsl:variable name="sectionNumber" select="$standardSection/@number"/>
		<xsl:variable name="ARSection" select="$standardSections//v3:section[@code='34084-4']"/>
		<xsl:variable name="ARNumber" select="$ARSection[1]/@number"/>
		<xsl:variable name="currentSectionNum">
			<xsl:apply-templates mode="sectionNumber" select="ancestor-or-self::v3:section"/>
		</xsl:variable>
		<tr>
			<td align="center" vAlign="top">
				<div class="DotleaderTop"/>
				<h1 class="Highlights">
					<!-- this was changed at FDA request and will now display the standard section title rather than what is coded in the label -->
					<xsl:apply-templates mode="highlights" select=".."/>
				</h1>
				<div class="DotleaderBot"/>
			</td>
		</tr>
		<tr>
			<td align="justify" vAlign="top">				
				<xsl:apply-templates mode="mixed" select="@*|node()[not(self::v3:title)]"/>
				<br/>
			</td>
		</tr>
		<!-- see PCR 801 -->
		<xsl:if test="not(boolean($gSr4)) and ../v3:code[@codeSystem='2.16.840.1.113883.6.1' and @code='34084-4']">
			<xsl:call-template name="suspectedARboilerPlate"/>
		</xsl:if>
		<xsl:if
			test="not(../../../v3:component/v3:section[v3:code[@codeSystem='2.16.840.1.113883.6.1' and @code='34084-4']]/v3:excerpt/v3:highlight/v3:text) and (number($sectionNumber)+1 = number($ARNumber) or (number(substring($currentSectionNum,2)) = number($ARNumber) and $currentCode != '43683-2'))">
			<xsl:call-template name="highlightNoAR"/>
		</xsl:if>
	</xsl:template>
	<xsl:template name="suspectedARboilerPlate">
		<!-- Genearate Suscpected Adverse Reactions section that is part of the highlights columns. -->
		<tr>
			<td width="50%" align="justify" vAlign="top">
				<strong><br/>	
							To report SUSPECTED ADVERSE REACTIONS, contact <xsl:value-of select="/v3:document/v3:legalAuthenticator/v3:assignedEntity/v3:representedOrganization/v3:name"/> at
							<xsl:for-each select="/v3:document/v3:legalAuthenticator/v3:assignedEntity/v3:telecom">
								<xsl:value-of select="@value"/>
								<xsl:if test="position() != last()">&#160;and&#160;</xsl:if>
							</xsl:for-each>							
					<xsl:choose>
						<xsl:when test="$currentLoincCode = '53404-0'" >
							or VAERS at 1-800-822-7967 or <a href="www.vaers.hhs.gov">www.vaers.hhs.gov</a>
						</xsl:when>
						<xsl:otherwise>
							or FDA at 1-800-FDA-1088 or <a href="http://www.fda.gov/medwatch">www.fda.gov/medwatch</a>
						</xsl:otherwise>	
					</xsl:choose>
					</strong>
				<br/>
				<br/>
			</td>
		</tr>
	</xsl:template>
	<xsl:template name="highlightNoAR">
		<!-- See  statement and if condition,  where this is called from -->
		<xsl:variable name="ARSection" select="$standardSections//v3:section[@code='34084-4']"/>
		<xsl:variable name="ARNumber" select="$ARSection[1]/@number"/>
		<tr>
			<td width="50%" align="justify" vAlign="top">
				<div class="DotleaderTop"/>
				<h1 class="Highlights">
					<!-- this was changed at FDA request and will now display the standard section title rather what is coded in the label -->
					<xsl:value-of select="$ARSection/v3:title"/>
				</h1>
				<div class="DotleaderBot"/>
			</td>
		</tr>
		<!-- see PCR 801 -->
		<xsl:if test="not(boolean($gSr4))">
			<xsl:call-template name="suspectedARboilerPlate"/>
		</xsl:if>
	</xsl:template>
	<xsl:template mode="highlights" match="v3:section[descendant::v3:highlight/v3:text and not(ancestor::v3:section)]">
		
		<xsl:param name="class" select="."/>
		<xsl:param name="standardSection"
			select="$standardSections//v3:section[@code=current()/v3:code/descendant-or-self::*[(self::v3:code or self::v3:translation) and @codeSystem='2.16.840.1.113883.6.1']/@code]"/>
		<xsl:choose>
			<xsl:when test="$standardSection[1]/v3:title">
				<xsl:value-of select="$standardSection[1]/v3:title"/>
			</xsl:when>
			<xsl:otherwise>
				<xsl:value-of select="v3:code/@displayName"/>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template>
	<xsl:template mode="highlights" match="v3:highlight//v3:paragraph">
		<!--**May not be called from anywhere.  -->
		<p class="Highlights{@styleCode}">
			<xsl:apply-templates select="v3:caption"/>
			<xsl:apply-templates mode="mixed" select="node()[not(self::v3:caption)]"/>
			<xsl:text> </xsl:text>
			<xsl:if test="not(following-sibling::v3:paragraph)">
				<xsl:variable name="reference" select="ancestor::v3:highlight[1]/v3:reference"/>
				<xsl:apply-templates mode="reference" select=".|//v3:section[v3:id/@root=$reference/v3:section/v3:id/@root and not(ancestor::v3:reference)]"/>
			</xsl:if>
		</p>
	</xsl:template>
	<xsl:template mode="highlights" match="v3:highlight//v3:paragraph[@styleCode='Bullet']" priority="2">
		<!--**May not be called from anywhere.  -->
		<p class="HighlightsHanging">
			<span class="Exdent">&#x2022;</span>
			<xsl:apply-templates select="v3:caption"/>
			<xsl:apply-templates mode="mixed" select="node()[not(self::v3:caption)]"/>
			<xsl:text> </xsl:text>
			<xsl:if test="not(following-sibling::v3:paragraph)">
				<xsl:variable name="reference" select="ancestor::v3:highlight/reference"/>
				<xsl:apply-templates mode="reference" select=".|//v3:section[v3:id/@root=$reference/v3:section/v3:id/@root and v3:title]"/>
			</xsl:if>
		</p>
	</xsl:template>
	<xsl:template mode="highlights" match="v3:tr"/>
	<xsl:template mode="highlights" match="v3:highlight//v3:table">
		<!--**May not be called from anywhere.  -->
		<xsl:apply-templates select="."/>
	</xsl:template>
	<xsl:template mode="highlights" match="v3:content[@styleCode = 'xmChange']">
		<!--**May not be called from anywhere.  -->
		<p>
			<xsl:apply-templates select="@*[not(local-name(.)='styleCode')]"/>
			<xsl:apply-templates mode="mixed" select="node()"/>
		</p>
	</xsl:template>
	<!-- MODE index -->
	<xsl:template name="index">
		<!--** Generate the Table of Contents. Called from root match, if the SPL is a PLR.
			per FDA PCR 575: Stylesheet must render only sections and first level of subsections (e.g., 1, 1.1, 1.2 etc.) in the FULL
			  PRESCRIBING INFORMATION: CONTENTS part of PLR SPL.  This is accomplished by counting the number of 'component' 
			  ancestors from the current node-->
		<table cellSpacing="0" cellPadding="3" width="100%">
			<thead>
				<tr>
					<th colSpan="2" align="left">FULL PRESCRIBING INFORMATION: CONTENTS<A href="#footnote-content" name="footnote-reference-content">*</A></th>
				</tr>
			</thead>
			<tfoot>
				<tr>
					<td colSpan="2">
						<dl class="FootnoteContents">
							<A href="#footnote-reference-content" name="footnote-content">*</A>
							Sections or subsections omitted from the full prescribing information are not listed
						</dl>
					</td>
				</tr>
			</tfoot>
			<tbody>
				<tr>
					<!-- index now is single column, no more dividing by two --> 
					<td width="100%" vAlign="top">
						<p>
							<!-- per FDA PCR 575: Stylesheet must render only sections and first level of subsections (e.g., 1, 1.1, 1.2 etc.) in the FULL
							  PRESCRIBING INFORMATION: CONTENTS part of PLR SPL.  This is accomplished by counting the number of 'component' 
							  ancestors from the current node-->
							<xsl:for-each select="//v3:section[v3:title != '' and count(ancestor::*[name(.) = 'component']) &lt;= 3]">
								<xsl:apply-templates mode="index" select="."/>
							</xsl:for-each>
						</p>
					</td>
				</tr>
			</tbody>
		</table>
		<hr/>
	</xsl:template>
	<xsl:template mode="index" match="/|@*|node()">
		<!--** May not be called form anywhere. deep null-transform -->
		<xsl:apply-templates mode="index" select="@*|node()"/>
	</xsl:template>
	<xsl:template mode="index" match="v3:section[v3:title]">
		<xsl:param name="sectionLevel" select="count(ancestor::v3:section)+1"/>
		<xsl:param name="sectionNumber" select="/.."/>
		<xsl:param name="standardSection"
			select="$standardSections//v3:section[@code=current()/v3:code/descendant-or-self::*[(self::v3:code or self::v3:translation) and @codeSystem='2.16.840.1.113883.6.1']/@code]"/>
		<xsl:variable name="titles" select="v3:title|$standardSection[1]/v3:title"/>
		<xsl:variable name="sectionNumberSequence">
			<xsl:apply-templates mode="sectionNumber" select="ancestor-or-self::v3:section"/>
		</xsl:variable>
		<a href="#section-{substring($sectionNumberSequence,2)}">
			<xsl:element name="h{$sectionLevel}">
				<xsl:attribute name="class">toc</xsl:attribute>
				<xsl:apply-templates select="@*"/>
				<!-- PCR 601 Not displaying foonote mark inside a  table of content -->
				<xsl:apply-templates mode="mixed" select="./v3:title/node()">
					<xsl:with-param name="isTableOfContent" select="'yes'"/>
				</xsl:apply-templates>
			</xsl:element>
		</a>
	</xsl:template>
	<!-- MODE: reference -->
	<!-- Create a section number reference such as (13.2) -->
	<xsl:template mode="reference" match="/|@*|node()">
		<xsl:text>(</xsl:text>
		<xsl:variable name="sectionNumberSequence">
			<xsl:apply-templates mode="sectionNumber" select="ancestor-or-self::v3:section"/>
		</xsl:variable>
		<a href="#section-{substring($sectionNumberSequence,2)}">
			<xsl:value-of select="substring($sectionNumberSequence,2)"/>
		</a>
		<xsl:text>)</xsl:text>
	</xsl:template>
	<!-- styleCode processing: styleCode can be a list of tokens that
       are being combined into a single css class attribute. To 
       come to a normalized combination we sort the tokens. 

       Step 1: combine the attribute supplied codes and additional
       codes in a single token list.

       Step 2: split the token list into XML elements
       
       Step 3: sort the elements and turn into a single combo
       token.
    -->
	<xsl:template match="@styleCode" name="styleCodeAttr">
		<xsl:param name="styleCode" select="."/>
		<xsl:param name="additionalStyleCode" select="/.."/>
		<xsl:param name="allCodes" select="normalize-space(concat($additionalStyleCode,' ',$styleCode))"/>
		<xsl:param name="additionalStyleCodeSequence" select="/.."/>
		<xsl:variable name="splitRtf">
			<xsl:if test="$allCodes">
				<xsl:call-template name="splitTokens">
					<xsl:with-param name="text" select="$allCodes"/>
				</xsl:call-template>
			</xsl:if>
			<xsl:for-each select="$additionalStyleCodeSequence">
				<token
					value="{concat(translate(substring(current(),1,1),                                  'abcdefghijklmnopqrstuvwxyz',      'ABCDEFGHIJKLMNOPQRSTUVWXYZ'),          substring(current(),2))}"
				/>
			</xsl:for-each>
		</xsl:variable>
		<xsl:variable name="class">
			<xsl:choose>
				<xsl:when test="function-available('exsl:node-set')">
					<xsl:variable name="sortedTokensRtf">
						<xsl:for-each select="exsl:node-set($splitRtf)/token">
							<xsl:sort select="@value"/>
							<xsl:copy-of select="."/>
						</xsl:for-each>
					</xsl:variable>
					<xsl:call-template name="uniqueStyleCodesExsl">
						<xsl:with-param name="inRtf" select="$sortedTokensRtf"/>
					</xsl:call-template>
				</xsl:when>
				<xsl:when test="function-available('msxsl:node-set')">
					<xsl:variable name="sortedTokensRtf">
						<xsl:for-each select="msxsl:node-set($splitRtf)/token">
							<xsl:sort select="@value"/>
							<xsl:copy-of select="."/>
						</xsl:for-each>
					</xsl:variable>
					<xsl:call-template name="uniqueStyleCodesMsxsl">
						<xsl:with-param name="inRtf" select="$sortedTokensRtf"/>
					</xsl:call-template>
				</xsl:when>
				<xsl:otherwise>
					<!-- this one below should work for all parsers as it is using exslt but will keep the above code for msxsl for now -->
					<xsl:for-each select="str:tokenize($allCodes, ' ')">
						<xsl:sort select="."/>
						<xsl:copy-of select="."/>
					</xsl:for-each>
				</xsl:otherwise>
			</xsl:choose>
		</xsl:variable>
		<xsl:choose>
			<xsl:when test="string-length($class) > 0">
				<xsl:attribute name="class">
					<xsl:value-of select="$class"/>
				</xsl:attribute>
			</xsl:when>
			<xsl:when test="string-length($allCodes) > 0">
				<xsl:attribute name="class">
					<xsl:value-of select="$allCodes"/>
				</xsl:attribute>
			</xsl:when>
		</xsl:choose>
	</xsl:template>
	<xsl:template name="uniqueStyleCodesExsl">
		<xsl:param name="inRtf" select="/.."/>
		<xsl:param name="in" select="exsl:node-set($inRtf)/token[@value]"/>
		<xsl:param name="done" select="/.."/>
		<xsl:if test="$in">
			<xsl:if test="not(contains($done,$in[1]/@value))">
				<xsl:value-of select="$in[1]/@value"/>
			</xsl:if>
			<xsl:call-template name="uniqueStyleCodesExsl">
				<xsl:with-param name="inRtf">
					<xsl:copy-of select="$in[position()>1]"/>
				</xsl:with-param>
				<xsl:with-param name="done" select="concat($done,@value)"/>
			</xsl:call-template>
		</xsl:if>
	</xsl:template>
	<xsl:template name="uniqueStyleCodesMsxsl">
		<xsl:param name="inRtf" select="/.."/>
		<xsl:param name="in" select="msxsl:node-set($inRtf)/token[@value]"/>
		<xsl:param name="done" select="/.."/>
		<xsl:if test="$in">
			<xsl:if test="not(contains($done,$in[1]/@value))">
				<xsl:value-of select="$in[1]/@value"/>
			</xsl:if>
			<xsl:call-template name="uniqueStyleCodesMsxsl">
				<xsl:with-param name="inRtf">
					<xsl:copy-of select="$in[position()>1]"/>
				</xsl:with-param>
				<xsl:with-param name="done" select="concat($done,@value)"/>
			</xsl:call-template>
		</xsl:if>
	</xsl:template>
	<xsl:template name="splitTokens">
		<xsl:param name="text" select="."/>
		<xsl:param name="firstCode" select="substring-before($text,' ')"/>
		<xsl:param name="restOfCodes" select="substring-after($text,' ')"/>
		<xsl:choose>
			<xsl:when test="$firstCode">
				<token
					value="{concat(translate(substring($firstCode,1,1),                                  'abcdefghijklmnopqrstuvwxyz',      'ABCDEFGHIJKLMNOPQRSTUVWXYZ'),          substring($firstCode,2))}"/>
				<xsl:if test="string-length($restOfCodes) > 0">
					<xsl:call-template name="splitTokens">
						<xsl:with-param name="text" select="$restOfCodes"/>
					</xsl:call-template>
				</xsl:if>
			</xsl:when>
			<xsl:otherwise>
				<token value="{concat(translate(substring($text,1,1),                                  'abcdefghijklmnopqrstuvwxyz',      'ABCDEFGHIJKLMNOPQRSTUVWXYZ'),          substring($text,2))}"
				/>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template>
	<!-- DOCUMENT MODEL -->
	<xsl:template mode="title" match="v3:document">
		<p class="DocumentTitle">
			<xsl:apply-templates select="./title/@*"/>
			<!-- loop through all of the subject elements -->			
			<xsl:for-each select=".//v3:subject[v3:manufacturedProduct[v3:manufacturedMedicine|v3:manufacturedProduct]]">
				<!-- sr4 display current node name ====<xsl:value-of select="name(.)"/>==== -->
				<xsl:variable name="prevProductHeaderString">
					<xsl:for-each select="preceding::v3:manufacturedProduct/v3:manufacturedMedicine|preceding::v3:manufacturedProduct/v3:manufacturedProduct">
						<xsl:call-template name="headerString">
						<xsl:with-param name="curProduct" select="." />
					</xsl:call-template>
					</xsl:for-each>
				</xsl:variable>
				<xsl:variable name="curProductHeaderString"><xsl:call-template name="headerString"><xsl:with-param name="curProduct" select="./v3:manufacturedProduct/v3:manufacturedMedicine|./v3:manufacturedProduct/v3:manufacturedProduct" /></xsl:call-template></xsl:variable>
				<xsl:choose>
					<xsl:when test="position() > 1 and contains($prevProductHeaderString, $curProductHeaderString)">
						
					</xsl:when>
					<!-- otherwise display all the information for this subject -->
					<xsl:otherwise>
						<xsl:if test="position() > 1">
							<br/>
						</xsl:if>
						<xsl:for-each select="./v3:manufacturedProduct/v3:manufacturedMedicine|./v3:manufacturedProduct/v3:manufacturedProduct">
							<strong>
								<xsl:call-template name="regMedNames"/>
								
							</strong>
						</xsl:for-each>
					</xsl:otherwise>
				</xsl:choose>
			</xsl:for-each>
			<xsl:if test="./v3:author/v3:assignedEntity/v3:representedOrganization/v3:name">
				<br/><xsl:value-of select="./v3:author/v3:assignedEntity/v3:representedOrganization/v3:name"/>
			</xsl:if>
			<br/>
		</p>
		<xsl:call-template name="flushDocumentTitleFootnotes"/>		
		<xsl:if test="(boolean($gSr4) or boolean($gSr3)) and not($currentLoincCode = '51725-0')">				
			<p>----------</p>
		</xsl:if>
	</xsl:template>
	<xsl:template name="titleNumerator">
		<xsl:for-each
			select="./v3:activeIngredient[(./v3:quantity/v3:numerator/@unit or ./v3:quantity/v3:denominator/@unit) and (./v3:quantity/v3:numerator/@unit != '' or ./v3:quantity/v3:denominator/@unit != '') and (./v3:quantity/v3:numerator/@unit != '1' or ./v3:quantity/v3:denominator/@unit != '1')]">
			<xsl:if test="position() = 1">&#160;</xsl:if>
			<xsl:if test="position() > 1">&#160;/&#160;</xsl:if>
			<xsl:value-of select="./v3:quantity/v3:numerator/@value"/>
			<xsl:if test="./v3:quantity/v3:numerator/@unit">&#160;<xsl:value-of select="./v3:quantity/v3:numerator/@unit"/></xsl:if>
			<xsl:if test="./v3:quantity/v3:denominator/@unit != '' and ./v3:quantity/v3:denominator/@unit != '1'">
				<xsl:text>&#160;per&#160;</xsl:text>
				<xsl:value-of select="./v3:quantity/v3:denominator/@value"/>
				<xsl:text>&#160;</xsl:text>
				<xsl:value-of select="./v3:quantity/v3:denominator/@unit"/>
			</xsl:if>
		</xsl:for-each>
	</xsl:template>
	<xsl:template name="consumedIn">
		<xsl:for-each select="../v3:consumedIn">
			<span class="titleCase">
				<xsl:call-template name="string-lowercase">
					<xsl:with-param name="text" select="./v3:substanceAdministration/v3:routeCode/@displayName"/>
				</xsl:call-template>
			</span>
			<xsl:call-template name="printSeperator">
				<xsl:with-param name="currentPos" select="position()"/>
				<xsl:with-param name="lastPos" select="last()"/>
				<xsl:with-param name="lastDelimiter">&#160;and</xsl:with-param>
			</xsl:call-template>
		</xsl:for-each>
	</xsl:template>
	<!-- FOOTNOTES -->
	<xsl:param name="footnoteMarks" select="'*&#8224;&#8225;&#167;&#182;#&#0222;&#0223;&#0224;&#0232;&#0240;&#0248;&#0253;&#0163;&#0165;&#0338;&#0339;&#0393;&#0065;&#0066;&#0067;&#0068;&#0069;&#0070;&#0071;&#0072;&#0073;&#0074;&#0075;&#0076;&#0077;&#0078;&#0079;&#0080;&#0081;&#0082;&#0083;&#0084;&#0085;&#0086;&#0087;&#0088;&#0089;&#0090;'"/>
	<xsl:template name="footnoteMark">
		<xsl:param name="target" select="."/>
		<xsl:for-each select="$target[1]">
			<xsl:choose>
				<xsl:when test="ancestor::v3:table">
					<!-- innermost table - FIXME: does not work for the constructed tables -->
					<xsl:variable name="number">
						<xsl:number level="any" from="v3:table" count="v3:footnote"/>
					</xsl:variable>
					<xsl:value-of select="substring($footnoteMarks,$number,1)"/>
				</xsl:when>
				<xsl:otherwise>
					<xsl:value-of select="count(preceding::v3:footnote[not(ancestor::v3:table)])+1"/>
				</xsl:otherwise>
			</xsl:choose>
		</xsl:for-each>
	</xsl:template>
	<!-- changed by Brian Suggs 11-16-05.  Added the [name(..) != 'text']  -->
	<!-- PCR 601 Not displaying foonote mark inside a  table of content -->
	<xsl:template match="v3:footnote[name(..) != 'text']">
		<xsl:param name="isTableOfContent2"/>
		<xsl:if test="$isTableOfContent2!='yes'">
			<xsl:variable name="mark">
				<xsl:call-template name="footnoteMark"/>
			</xsl:variable>
			<xsl:variable name="globalnumber" select="count(preceding::v3:footnote)+1"/>
			<a name="footnote-reference-{$globalnumber}" href="#footnote-{$globalnumber}" class="Sup">
				<xsl:value-of select="$mark"/>
			</a>
		</xsl:if>
	</xsl:template>
	<xsl:template match="v3:footnoteRef">
		<xsl:variable name="ref" select="@IDREF"/>
		<xsl:variable name="target" select="//v3:footnote[@ID=$ref]"/>
		<xsl:variable name="mark">
			<xsl:call-template name="footnoteMark">
				<xsl:with-param name="target" select="$target"/>
			</xsl:call-template>
		</xsl:variable>
		<xsl:variable name="globalnumber" select="count($target/preceding::v3:footnote)+1"/>
		<a href="#footnote-{$globalnumber}" class="Sup">
			<xsl:value-of select="$mark"/>
		</a>
	</xsl:template>
	<xsl:template name="flushSectionTitleFootnotes">
		<xsl:variable name="footnotes" select="./v3:title/v3:footnote[not(ancestor::v3:table)]"/>
		<xsl:if test="$footnotes">
			<hr class="Footnoterule"/>
			<dl class="Footnote">
				<xsl:apply-templates mode="footnote" select="$footnotes"/>
			</dl>
		</xsl:if>
	</xsl:template>
	<xsl:template name="flushDocumentTitleFootnotes">
		<xsl:variable name="footnotes" select=".//v3:title/v3:footnote[not(ancestor::v3:table)]"/>
		<xsl:if test="$footnotes">
			<hr class="Footnoterule"/>
			<dl class="Footnote">
				<xsl:apply-templates mode="footnote" select="$footnotes"/>
			</dl>
		</xsl:if>
	</xsl:template>
	<!-- comment added by Brian Suggs on 11-11-05: The flushfootnotes template is called at the end of every section -->
	<xsl:template match="v3:flushfootnotes" name="flushfootnotes">
	<xsl:variable name="footnotes" select=".//v3:footnote[not(ancestor::v3:table)]"/>
		<xsl:if test="$footnotes">
			<hr class="Footnoterule"/>
			<dl class="Footnote">
				<xsl:apply-templates mode="footnote" select="$footnotes"/>
			</dl>
		</xsl:if>
	</xsl:template>
	<xsl:template mode="footnote" match="/|node()">
		<xsl:apply-templates mode="footnote" select="node()"/>
	</xsl:template>
	<xsl:template mode="footnoteChanged" match="v3:footnote">
		<xsl:variable name="mark">
			<xsl:call-template name="footnoteMark"/>
		</xsl:variable>
		<xsl:variable name="globalnumber" select="count(preceding::v3:footnote)+1"/>
		<dt>
			<span class="xmChange_footnotes">&#160;</span>
			<a name="footnote-{$globalnumber}" href="#footnote-reference-{$globalnumber}">
				<xsl:value-of select="$mark"/>
			</a>
		</dt>
		<dd>
			<xsl:apply-templates mode="mixed" select="node()"/>
		</dd>
	</xsl:template>
	<xsl:template mode="footnote" match="v3:footnote">
		<xsl:variable name="mark">
			<xsl:call-template name="footnoteMark"/>
		</xsl:variable>
		<xsl:variable name="globalnumber" select="count(preceding::v3:footnote)+1"/>
		<dt>
			<a name="footnote-{$globalnumber}" href="#footnote-reference-{$globalnumber}">
				<xsl:value-of select="$mark"/>
			</a>
		</dt>
		<dd>
			<xsl:apply-templates mode="mixed" select="node()"/>
		</dd>
	</xsl:template>
	<xsl:template mode="footnote" match="v3:section|v3:table"/>
	<!-- CROSS REFERENCE linkHtml -->
	<xsl:template name="reference" mode="mixed" match="v3:linkHtml[@href]">
		<xsl:param name="current" select="current()"/>
		<xsl:param name="href" select="$current/@href"/>
		<xsl:param name="target" select="//*[@ID=substring-after($href,'#')]"/>
		<xsl:param name="styleCode" select="$current/@styleCode"/>
		<xsl:variable name="targetTable" select="$target/self::v3:table"/>
		<xsl:choose>
			<xsl:when test="$targetTable and self::v3:linkHtml and $current/node()">
				<a href="#{$targetTable/@ID}">
					<xsl:apply-templates mode="mixed" select="$current/node()"/>
				</a>
			</xsl:when>
			<!-- see PCR 793, we don't generate anchor anymore, we just use what's in the spl -->
			<xsl:otherwise>
				<xsl:variable name="sectionNumberSequence">
					<xsl:apply-templates mode="sectionNumber" select="$target/ancestor-or-self::v3:section"/>
				</xsl:variable>
				<xsl:variable name="nhref">
					<xsl:choose>
						<xsl:when test="starts-with( $href, '#')">							
							<xsl:value-of select="$href"/>
						</xsl:when>
						<xsl:otherwise>
							#invalid_link
						</xsl:otherwise>
					</xsl:choose>
				</xsl:variable>
				<!-- XXX: can we match the style of the headings? -->
				<a href="{$nhref}">
					<xsl:if test="contains($styleCode,'MainTitle') and $target/ancestor-or-self::v3:section[last()]/v3:title">
						<xsl:value-of select="$target/ancestor-or-self::v3:section[last()]/v3:title"/>
					</xsl:if>
					<xsl:if test="contains($styleCode,'SubTitle') and $target/v3:title">
						<xsl:if test="contains($styleCode,'MainTitle') and $target/ancestor-or-self::v3:section[last()]/v3:title">
							<xsl:text>: </xsl:text>
						</xsl:if>
						<xsl:value-of select="$target/v3:title"/>
					</xsl:if>
					<xsl:if test="contains($styleCode,'Number') and $target/ancestor-or-self::v3:section[last()]/v3:title">
						<xsl:text>(</xsl:text>
						<xsl:value-of select="substring($sectionNumberSequence,2)"/>
						<xsl:text>)</xsl:text>
					</xsl:if>
					<xsl:if test="self::v3:linkHtml">
						<xsl:apply-templates mode="mixed" select="$current/node()"/>
					</xsl:if>
				</a>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template>
	<xsl:template mode="sectionNumber" match="/|@*|node()"/>
	<xsl:template mode="sectionNumber" match="v3:section">
		<xsl:param name="standardSection"
			select="$standardSections//v3:section[@code=current()/v3:code/descendant-or-self::*[(self::v3:code or self::v3:translation) and @codeSystem='2.16.840.1.113883.6.1']/@code]"/>
		<xsl:variable name="standardSectionNumber" select="$standardSection/@number"/>
		<!-- see note anchoring and PCR 793 -->
		<xsl:if test="@ID">
			<a name="{@ID}"/>
		</xsl:if>
		<xsl:value-of select="concat('.',count(parent::v3:component/preceding-sibling::v3:component[child::v3:section])+1)"/>
	</xsl:template>
	<xsl:template mode="standardSectionNumber" match="v3:section">
		<xsl:param name="standardSection"
			select="$standardSections//v3:section[@code=current()/v3:code/descendant-or-self::*[(self::v3:code or self::v3:translation) and @codeSystem='2.16.840.1.113883.6.1']/@code]"/>
		<xsl:variable name="standardSectionNumber" select="$standardSection/@number"/>
		<!-- see note anchoring and PCR 793 -->
		<xsl:if test="@ID">
			<a name="{@ID}"/>
		</xsl:if>
		<xsl:choose>
			<xsl:when test="$standardSectionNumber">
				<xsl:value-of select="$standardSectionNumber"/>
			</xsl:when>
			<xsl:otherwise>
				<xsl:value-of select="count(parent::v3:component/preceding-sibling::v3:component[child::v3:section])+1"/>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template>
	<!-- SECTION MODEL -->
	<xsl:template match="v3:section">
		<xsl:param name="standardSection"
			select="$standardSections//v3:section[@code=current()/v3:code/descendant-or-self::*[(self::v3:code or self::v3:translation) and @codeSystem='2.16.840.1.113883.6.1']/@code]"/>
		<xsl:param name="sectionLevel" select="count(ancestor-or-self::v3:section)"/>
		<xsl:variable name="sectionNumberSequence">
			<xsl:apply-templates mode="sectionNumber" select="ancestor-or-self::v3:section"/>
		</xsl:variable>
		<xsl:variable name="titles" select="v3:title"/>
		<xsl:if test="@ID">
			<a name="{@ID}"/>
		</xsl:if>
		<a name="section-{substring($sectionNumberSequence,2)}"/>
		<p/>
		<xsl:apply-templates select="$titles[1]">
			<xsl:with-param name="sectionLevel" select="$sectionLevel"/>
			<xsl:with-param name="sectionNumber" select="substring($sectionNumberSequence,2)"/>
		</xsl:apply-templates>
		<xsl:if test="$show-data">
			<xsl:apply-templates mode="data" select="."/>
		</xsl:if>
		<xsl:apply-templates select="@*|node()[not(self::v3:title)]"/>
		<xsl:call-template name="flushSectionTitleFootnotes"/>
	</xsl:template>
	<!-- boxed warning -->
	<xsl:template match="v3:section[           v3:code[   descendant-or-self::*[   (self::v3:code or self::v3:translation) and   @codeSystem='2.16.840.1.113883.6.1' and @code='34066-1'   ]    ]  ]"
		priority="2">
		<xsl:param name="mode" select="/.."/>
		<xsl:param name="standardSection"
			select="$standardSections//v3:section[@code=current()/v3:code/descendant-or-self::*[(self::v3:code or self::v3:translation) and @codeSystem='2.16.840.1.113883.6.1']/@code]"/>
		<xsl:param name="sectionLevel" select="count(ancestor-or-self::v3:section)"/>		
		<!-- see note anchoring and PCR 793 -->
		<xsl:if test="@ID">
			<a name="{@ID}"/>
		</xsl:if>
		<div>
			<xsl:call-template name="styleCodeAttr">
				<xsl:with-param name="styleCode" select="@styleCode"/>
				<xsl:with-param name="additionalStyleCode" select="'Warning'"/>
			</xsl:call-template>
			<xsl:variable name="sectionNumberSequence">
				<xsl:apply-templates mode="sectionNumber" select="ancestor-or-self::v3:section"/>
			</xsl:variable>
			<xsl:variable name="titles" select="v3:title"/>
			<xsl:if test="not($mode='highlights')">
				<a name="section-{substring($sectionNumberSequence,2)}"/>
			</xsl:if>
			<p/>
			<!-- this funny p is used to prevent melting two sub-sections together in condensed style -->
			<xsl:apply-templates select="$titles[1]">
				<xsl:with-param name="sectionLevel" select="$sectionLevel"/>
				<xsl:with-param name="sectionNumber" select="substring($sectionNumberSequence,2)"/>
			</xsl:apply-templates>
			<xsl:apply-templates select="@*|node()[not(self::v3:title)]"/>
		</div>
	</xsl:template>
	<!-- don't display the Recent Major Change section within the FPI -->
	<xsl:template match="v3:section[v3:code[descendant-or-self::*[(self::v3:code or self::v3:translation) and @codeSystem='2.16.840.1.113883.6.1' and @code='43683-2']]]" priority="2"/>
	<xsl:template match="v3:section/v3:title">
		<xsl:param name="sectionLevel" select="count(ancestor::v3:section)"/>
		<xsl:param name="sectionNumber" select="/.."/>
		<xsl:element name="h{$sectionLevel}">
			<xsl:apply-templates select="@*"/>
			<xsl:if test="$show-section-numbers and $sectionNumber">
				<span class="SectionNumber">
					<xsl:value-of select="$sectionNumber"/>
				</span>
			</xsl:if>
			<xsl:apply-templates mode="mixed" select="node()"/>
		</xsl:element>
		<!-- changed by Brian Suggs on 11-15-05 to add the footnote to the section title -->
		<!-- PCR 596 Seperating the Document title footnote display from the section footnote display  
			Now this template is called from the end of the section instead of the end of the title-->
	</xsl:template>
	<!-- PCR 601 Not displaying foonote mark inside a  table of content -->
	<xsl:template match="v3:section/v3:text">
		<xsl:apply-templates select="@*"/>
		<xsl:apply-templates mode="mixed" select="node()"/>
		<xsl:call-template name="flushfootnotes">
			<xsl:with-param name="isTableOfContent" select="'no'"/>
		</xsl:call-template>
	</xsl:template>
	<!-- DISPLAY SUBJECT STRUCTURED INFORMATION -->
	<xsl:template match="v3:excerpt|v3:subjectOf"/>
	<!-- PARAGRAPH MODEL -->
	<xsl:template match="v3:paragraph">
		<p>
			<!-- see note anchoring and PCR 793 -->
			<xsl:if test="@ID">
				<a name="{@ID}"/>
			</xsl:if>
			<xsl:call-template name="styleCodeAttr">
				<xsl:with-param name="styleCode" select="@styleCode"/>
				<xsl:with-param name="additionalStyleCode">
					<xsl:if test="count(preceding-sibling::v3:paragraph)=0">
						<xsl:text>First</xsl:text>
					</xsl:if>
				</xsl:with-param>
			</xsl:call-template>
			<xsl:apply-templates select="@*[not(local-name(.)='styleCode')]|v3:caption"/>
			<xsl:apply-templates mode="mixed" select="node()[not(self::v3:caption)]"/>
		</p>
	</xsl:template>
	<xsl:template match="v3:paragraph/v3:caption">
		<span>
			<xsl:call-template name="styleCodeAttr">
				<xsl:with-param name="styleCode" select="@styleCode"/>
				<xsl:with-param name="additionalStyleCode" select="'ParagraphCaption'"/>
			</xsl:call-template>
			<xsl:apply-templates select="@*[not(local-name(.)='styleCode')]"/>
			<xsl:apply-templates mode="mixed" select="node()"/>
		</span>
	</xsl:template>
	<!-- the old poor man's footnote -->
	<xsl:template match="v3:paragraph[contains(@styleCode,'Footnote') and v3:caption]">
		<dl class="Footnote">
			<dt>
				<xsl:apply-templates mode="mixed" select="node()[self::v3:caption]"/>
			</dt>
			<dd>
				<xsl:apply-templates mode="mixed" select="node()[not(self::v3:caption)]"/>
			</dd>
		</dl>
	</xsl:template>
	<!-- LIST MODEL -->
	<!-- listType='unordered' is default, if any item has a caption,
       all should have a caption -->
	<xsl:template match="v3:list[not(v3:item/v3:caption)]">
		<xsl:apply-templates select="v3:caption"/>
		<ul>
			<xsl:apply-templates select="@*|node()[not(self::v3:caption)]"/>
		</ul>
	</xsl:template>
	<xsl:template match="v3:list[@listType='ordered' and        not(v3:item/v3:caption)]" priority="1">
		<xsl:apply-templates select="v3:caption"/>
		<ol>
			<xsl:apply-templates select="@*|node()[not(self::v3:caption)]"/>
		</ol>
	</xsl:template>
	<xsl:template match="v3:list/v3:item[not(parent::v3:list/v3:item/v3:caption)]">
		<li>
			<xsl:apply-templates select="@*"/>
			<xsl:apply-templates mode="mixed" select="node()"/>
		</li>
	</xsl:template>
	<!-- lists with custom captions -->
	<xsl:template match="v3:list[v3:item/v3:caption]">
		<xsl:apply-templates select="v3:caption"/>
		<dl>
			<xsl:apply-templates select="@*|node()[not(self::v3:caption)]"/>
		</dl>
	</xsl:template>
	<xsl:template match="v3:list/v3:item[parent::v3:list/v3:item/v3:caption]">
		<xsl:apply-templates select="v3:caption"/>
		<dd>
			<xsl:apply-templates select="@*"/>
			<xsl:apply-templates mode="mixed" select="node()[not(self::v3:caption)]"/>
		</dd>
	</xsl:template>
	<xsl:template match="v3:list/v3:item/v3:caption">
		<dt>
			<xsl:apply-templates select="@*"/>
			<xsl:apply-templates mode="mixed" select="node()"/>
		</dt>
	</xsl:template>
	<xsl:template match="v3:list/v3:caption">
		<p>
			<xsl:call-template name="styleCodeAttr">
				<xsl:with-param name="styleCode" select="@styleCode"/>
				<xsl:with-param name="additionalStyleCode" select="'ListCaption'"/>
			</xsl:call-template>
			<xsl:apply-templates select="@*[not(local-name(.)='styleCode')]"/>
			<xsl:apply-templates mode="mixed" select="node()"/>
		</p>
	</xsl:template>
	<!-- TABLE MODEL -->
	<xsl:template match="v3:table">
		<!-- see note anchoring and PCR 793 -->
		<xsl:if test="@ID">
			<a name="{@ID}"/>
		</xsl:if>
		<table>
			<xsl:apply-templates select="@*|node()"/>
		</table>
	</xsl:template>
	<xsl:template
		match="v3:table/@summary                       |v3:table/@width                       |v3:table/@border                       |v3:table/@frame                       |v3:table/@rules                       |v3:table/@cellspacing                       |v3:table/@cellpadding">
		<xsl:copy-of select="."/>
	</xsl:template>
	<xsl:template match="v3:table/v3:caption">
		<caption>
			<xsl:if test="contains(parent::v3:table/@styleCode, 'xmChange')">
						<span class="xmChange_caption">&#160;</span>
			</xsl:if>
			<xsl:apply-templates select="@*"/>
			<xsl:apply-templates mode="mixed" select="node()"/>
		</caption>
		<!--xsl:if test="not(preceding-sibling::v3:tfoot) and not(preceding-sibling::v3:tbody)">
			<xsl:call-template name="flushtablefootnotes"/>
		</xsl:if-->
	</xsl:template>
	<xsl:template match="v3:thead">
		<thead>
			<xsl:apply-templates select="@*|node()"/>
		</thead>
	</xsl:template>
	<xsl:template match="v3:thead/@align                       |v3:thead/@char                       |v3:thead/@charoff                       |v3:thead/@valign">
		<xsl:copy-of select="."/>
	</xsl:template>
	<xsl:template match="v3:tfoot" name="flushtablefootnotes">
		<xsl:variable name="allspan" select="count(ancestor::v3:table[1]/v3:colgroup/v3:col|ancestor::v3:table[1]/v3:col)"/>
		<xsl:if test="self::v3:tfoot or ancestor::v3:table[1]//v3:footnote">
			<tfoot>
				<xsl:if test="self::v3:tfoot">
					<xsl:apply-templates select="@*|node()"/>
				</xsl:if>
				<xsl:if test="ancestor::v3:table[1]//v3:footnote">
					<tr>
						<td colspan="{$allspan}" align="left">
							<dl class="Footnote">
								<xsl:if test="contains(parent::v3:table/@styleCode, 'xmChange')">
									<span class="xmChange_footnote">&#160;</span>
								</xsl:if>
								<xsl:choose>
									<xsl:when test="contains(parent::v3:table/@styleCode, 'xmChange')">
										<xsl:apply-templates mode="footnoteChanged" select="ancestor::v3:table[1]/node()"/>
									</xsl:when>
									<xsl:otherwise>
										<xsl:apply-templates mode="footnote" select="ancestor::v3:table[1]/node()"/>
									</xsl:otherwise>
								</xsl:choose>												
							</dl>
						</td>
					</tr>
				</xsl:if>
			</tfoot>
		</xsl:if>
	</xsl:template>
	<xsl:template match="v3:tfoot/@align                       |v3:tfoot/@char                       |v3:tfoot/@charoff                       |v3:tfoot/@valign">
		<xsl:copy-of select="."/>
	</xsl:template>
	<xsl:template match="v3:tbody">
		<xsl:if test="not(preceding-sibling::v3:tfoot) and not(preceding-sibling::v3:tbody)">
			<xsl:call-template name="flushtablefootnotes"/>
		</xsl:if>
		<tbody>
			<xsl:apply-templates select="@*|node()"/>
		</tbody>
	</xsl:template>
	<xsl:template match="v3:tbody[not(preceding-sibling::v3:thead)]">
		<xsl:if test="not(preceding-sibling::v3:tfoot) and not(preceding-sibling::tbody)">
			<xsl:call-template name="flushtablefootnotes"/>
		</xsl:if>
		<tbody>
			<xsl:call-template name="styleCodeAttr">
				<xsl:with-param name="styleCode" select="@styleCode"/>
				<xsl:with-param name="additionalStyleCode" select="'Headless'"/>
			</xsl:call-template>
			<xsl:apply-templates select="@*[not(local-name(.)='styleCode')]"/>
			<xsl:apply-templates select="node()"/>
		</tbody>
	</xsl:template>
	<xsl:template match="v3:tbody/@align                       |v3:tbody/@char                       |v3:tbody/@charoff                       |v3:tbody/@valign">
		<xsl:copy-of select="."/>
	</xsl:template>
	<xsl:template match="v3:tr">
		<tr>
			<xsl:call-template name="styleCodeAttr">
				<xsl:with-param name="styleCode" select="@styleCode"/>
				<xsl:with-param name="additionalStyleCode">
					<xsl:if test="position()=1">
						<xsl:text> First </xsl:text>
					</xsl:if>
					<xsl:if test="position()=last()">
						<xsl:text> Last </xsl:text>
					</xsl:if>
				</xsl:with-param>
			</xsl:call-template>
			<xsl:apply-templates select="@*[not(local-name(.)='styleCode')]"/>
			<xsl:apply-templates select="node()"/>
		</tr>
	</xsl:template>
	<xsl:template match="v3:tr/@align                       |v3:tr/@char                       |v3:tr/@charoff                       |v3:tr/@valign">
		<xsl:copy-of select="."/>
	</xsl:template>
	<xsl:template match="v3:th">
		<!-- determine our position to find out the associated col -->
		<xsl:param name="position"
			select="1+count(preceding-sibling::v3:td[not(@colspan)]                     |preceding-sibling::v3:th[not(@colspan)])                +sum(preceding-sibling::v3:td/@colspan              |preceding-sibling::v3:th/@colspan)"/>
		<xsl:param name="associatedCol" select="(ancestor::v3:table/v3:colgroup/v3:col|ancestor::v3:table/v3:col)[$position]"/>
		<xsl:param name="associatedColgroup" select="$associatedCol/parent::v3:colgroup"/>
		<th>
			<xsl:call-template name="styleCodeAttr">
				<xsl:with-param name="styleCode" select="@styleCode"/>
				<xsl:with-param name="additionalStyleCode">
					<xsl:if test="not(ancestor::v3:tfoot)               and contains($associatedColgroup/@styleCode,'Lrule')                      and not($associatedCol/preceding-sibling::v3:col)">
						<xsl:text> Lrule </xsl:text>
					</xsl:if>
					<xsl:if test="not(ancestor::v3:tfoot)                      and contains($associatedColgroup/@styleCode,'Rrule')        and not($associatedCol/following-sibling::v3:col)">
						<xsl:text> Rrule </xsl:text>
					</xsl:if>
				</xsl:with-param>
			</xsl:call-template>
			<xsl:copy-of select="$associatedCol/@align"/>
			<xsl:apply-templates select="@*[not(local-name(.)='styleCode')]"/>
			<xsl:apply-templates mode="mixed" select="node()"/>
		</th>
	</xsl:template>
	<xsl:template
		match="v3:th/@align                       |v3:th/@char                       |v3:th/@charoff                       |v3:th/@valign                       |v3:th/@abbr                       |v3:th/@axis                       |v3:th/@headers                       |v3:th/@scope                       |v3:th/@rowspan                       |v3:th/@colspan">
		<xsl:copy-of select="."/>
	</xsl:template>
	<xsl:template match="v3:td">
		<!-- determine our position to find out the associated col -->
		<xsl:param name="position"
			select="1+count(preceding-sibling::v3:td[not(@colspan)]                     |preceding-sibling::v3:th[not(@colspan)])                +sum(preceding-sibling::v3:td/@colspan              |preceding-sibling::v3:th/@colspan)"/>
		<xsl:param name="associatedCol" select="(ancestor::v3:table/v3:colgroup/v3:col|ancestor::v3:table/v3:col)[$position]"/>
		<xsl:param name="associatedColgroup" select="$associatedCol/parent::v3:colgroup"/>
		
		<td>
			<xsl:if test="contains(ancestor::v3:table/@styleCode, 'xmChange')">		
					<xsl:variable name="tdLength" select="round(string-length(.) div 26) + 3"/>
				<span class="xmChange_all_rows" style="line-height: {$tdLength}ex">&#160;</span>
			</xsl:if>
			
			<xsl:call-template name="styleCodeAttr">
				<xsl:with-param name="styleCode" select="@styleCode"/>
				<xsl:with-param name="additionalStyleCode">
					<xsl:if test="not(ancestor::v3:tfoot)               and contains($associatedColgroup/@styleCode,'Lrule')                      and not($associatedCol/preceding-sibling::v3:col)">
						<xsl:text> Lrule </xsl:text>
					</xsl:if>
					<xsl:if test="not(ancestor::v3:tfoot)                      and contains($associatedColgroup/@styleCode,'Rrule')        and not($associatedCol/following-sibling::v3:col)">
						<xsl:text> Rrule </xsl:text>
					</xsl:if>
				</xsl:with-param>
			</xsl:call-template>
			<xsl:copy-of select="$associatedCol/@align"/>
			<xsl:apply-templates select="@*[not(local-name(.)='styleCode')]"/>
			<xsl:apply-templates mode="mixed" select="node()"/>
		</td>
	</xsl:template>
	<xsl:template
		match="v3:td/@align                       |v3:td/@char                       |v3:td/@charoff                       |v3:td/@valign                       |v3:td/@abbr                       |v3:td/@axis                       |v3:td/@headers                       |v3:td/@scope                       |v3:td/@rowspan                       |v3:td/@colspan">
		<xsl:copy-of select="."/>
	</xsl:template>
	<xsl:template match="v3:colgroup">
		<colgroup>
			<xsl:apply-templates select="@*|node()"/>
		</colgroup>
	</xsl:template>
	<xsl:template
		match="v3:colgroup/@span                       |v3:colgroup/@width                       |v3:colgroup/@align                       |v3:colgroup/@char                       |v3:colgroup/@charoff                       |v3:colgroup/@valign">
		<xsl:copy-of select="."/>
	</xsl:template>
	<xsl:template match="v3:col">
		<col>
			<xsl:apply-templates select="@*|node()"/>
		</col>
	</xsl:template>
	<xsl:template
		match="v3:col/@span                       |v3:col/@width                       |v3:col/@align                       |v3:col/@char                       |v3:col/@charoff                       |v3:col/@valign">
		<xsl:copy-of select="."/>
	</xsl:template>
	<!-- MIXED MODE: where text is rendered as is, even if nested 
         inside elements that we do not understand  -->
	<!-- based on the deep null-transform -->
	<xsl:template mode="mixed" match="@*|node()">
		<xsl:apply-templates mode="mixed" select="@*|node()"/>
	</xsl:template>
	<xsl:template mode="mixed" match="text()" priority="0">
		<xsl:copy/>
	</xsl:template>
	<xsl:template mode="mixed" match="v3:content">
		<span>
			<!-- see note anchoring and PCR 793 -->
			<xsl:if test="@ID">
				<a name="{@ID}"/>
			</xsl:if>
			<xsl:call-template name="styleCodeAttr">
				<xsl:with-param name="styleCode" select="@styleCode"/>
				<xsl:with-param name="additionalStyleCodeSequence" select="@emphasis|@revised"/>
			</xsl:call-template>
			<xsl:apply-templates select="@*[not(local-name(.)='styleCode')]"/>
			<xsl:apply-templates mode="mixed" select="node()"/>			
		</span>
	</xsl:template>
	<xsl:template mode="mixed" match="v3:content[@styleCode = 'xmChange']">
		<xsl:choose>
			<xsl:when test="ancestor::v3:list[v3:item/v3:caption]">
				<span class="xmChange_custom_caption">&#160;</span>
			</xsl:when>
			<xsl:otherwise>
				<span class="xmChange">&#160;</span>
			</xsl:otherwise>
		</xsl:choose>
		<span>
			<xsl:call-template name="styleCodeAttr">
				<xsl:with-param name="additionalStyleCodeSequence" select="@emphasis|@revised"/>
			</xsl:call-template>
			<xsl:apply-templates select="@*[not(local-name(.)='styleCode')]"/>
			<xsl:apply-templates mode="mixed" select="node()"/>
		</span>
	</xsl:template>
	<xsl:template mode="mixed" match="v3:content[@emphasis='yes']" priority="1">
		<em>
			<xsl:call-template name="styleCodeAttr">
				<xsl:with-param name="styleCode" select="@styleCode"/>
				<xsl:with-param name="additionalStyleCodeSequence" select="@revised"/>
			</xsl:call-template>
			<xsl:apply-templates select="@*[not(local-name(.)='styleCode')]"/>
			<xsl:apply-templates mode="mixed" select="node()"/>
		</em>
	</xsl:template>
	<xsl:template mode="mixed" match="v3:content[@emphasis]">
		<em>
			<xsl:call-template name="styleCodeAttr">
				<xsl:with-param name="styleCode" select="@styleCode"/>
				<xsl:with-param name="additionalStyleCodeSequence" select="@emphasis|@revised"/>
			</xsl:call-template>
			<xsl:apply-templates select="@*[not(local-name(.)='styleCode')]"/>
			<xsl:apply-templates mode="mixed" select="node()"/>
		</em>
	</xsl:template>
	<!-- We don't use <sub> and <sup> elements here because IE produces
       ugly uneven line spacing. -->
	<xsl:template mode="mixed" match="v3:sub">
		<span class="Sub">
			<xsl:apply-templates mode="mixed" select="@*|node()"/>
		</span>
	</xsl:template>
	<xsl:template mode="mixed" match="v3:sup">
		<span class="Sup">
			<xsl:apply-templates mode="mixed" select="@*|node()"/>
		</span>
	</xsl:template>
	<xsl:template mode="mixed" match="v3:br">
		<br/>
	</xsl:template>
	<xsl:template mode="mixed" priority="1" match="v3:renderMultiMedia[@referencedObject     and (   ancestor::v3:paragraph          or ancestor::v3:td          or ancestor::v3:th)]">
		<xsl:variable name="reference" select="@referencedObject"/>
		<!-- see note anchoring and PCR 793 -->
		<xsl:if test="@ID">
			<a name="{@ID}"/>
		</xsl:if>
		<xsl:choose>
			<xsl:when test="boolean(//v3:observationMedia[@ID=$reference]//v3:text)">
				<img alt="{//v3:observationMedia[@ID=$reference]//v3:text}" src="{//v3:observationMedia[@ID=$reference]//v3:reference/@value}">
					<xsl:apply-templates select="@*"/>
				</img>
			</xsl:when>
			<xsl:when test="not(boolean(//v3:observationMedia[@ID=$reference]//v3:text))">
				<img alt="Image from Drug Label Content" src="{//v3:observationMedia[@ID=$reference]//v3:reference/@value}">
					<xsl:apply-templates select="@*"/>
				</img>
			</xsl:when>
		</xsl:choose>
			<xsl:apply-templates mode="notCentered" select="v3:caption"/>
	</xsl:template>
	<xsl:template mode="mixed" match="v3:renderMultiMedia[@referencedObject]">
		<xsl:variable name="reference" select="@referencedObject"/>
		<div>
			<xsl:call-template name="styleCodeAttr">
				<xsl:with-param name="styleCode" select="@styleCode"/>
				<xsl:with-param name="additionalStyleCode" select="'Figure'"/>
			</xsl:call-template>
			<xsl:apply-templates select="@*[not(local-name(.)='styleCode')]"/>
			
			<!-- see note anchoring and PCR 793 -->
			<xsl:if test="@ID">
				<a name="{@ID}"/>
			</xsl:if>
			
				<xsl:choose>
					<xsl:when test="boolean(//v3:observationMedia[@ID=$reference]//v3:text)">
						<img alt="{//v3:observationMedia[@ID=$reference]//v3:text}" src="{//v3:observationMedia[@ID=$reference]//v3:reference/@value}">
							<xsl:apply-templates select="@*"/>
						</img>
					</xsl:when>
					<xsl:when test="not(boolean(//v3:observationMedia[@ID=$reference]//v3:text))">
						<img alt="Image from Drug Label Content" src="{//v3:observationMedia[@ID=$reference]//v3:reference/@value}">
							<xsl:apply-templates select="@*"/>
						</img>
					</xsl:when>
				</xsl:choose>			
			<xsl:apply-templates select="v3:caption"/>
		</div>
	</xsl:template>
	<xsl:template match="v3:renderMultiMedia/v3:caption">
		<p>
			<xsl:call-template name="styleCodeAttr">
				<xsl:with-param name="styleCode" select="@styleCode"/>
				<xsl:with-param name="additionalStyleCode" 
				select="'MultiMediaCaption'"/>
			</xsl:call-template>
			<xsl:apply-templates select="@*[not(local-name(.)='styleCode')]"/>
			<xsl:apply-templates mode="mixed" select="node()"/>
		</p>
	</xsl:template>
	<xsl:template mode="notCentered" match="v3:renderMultiMedia/v3:caption">
			<p>
				<xsl:call-template name="styleCodeAttr">
					<xsl:with-param name="styleCode" select="@styleCode"/>
					<xsl:with-param name="additionalStyleCode" 
					select="'MultiMediaCaptionNotCentered'"/>
				</xsl:call-template>
				<xsl:apply-templates select="@*[not(local-name(.)='styleCode')]"/>
				<xsl:apply-templates mode="mixed" select="node()"/>
			</p>
	</xsl:template>
	<xsl:template mode="mixed" match="v3:paragraph|v3:list|v3:table|v3:footnote|v3:footnoteRef|v3:flushfootnotes">
		<xsl:param name="isTableOfContent"/>
		<xsl:choose>
			<xsl:when test="$isTableOfContent='yes'">
				<xsl:apply-templates select=".">
					<xsl:with-param name="isTableOfContent2" select="'yes'"/>
				</xsl:apply-templates>
			</xsl:when>
			<xsl:otherwise>
				<xsl:apply-templates select=".">
					<xsl:with-param name="isTableOfContent2" select="'no'"/>
				</xsl:apply-templates>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template>
	<!-- MODE: DATA -->
	<xsl:template mode="data" match="*">
		<xsl:apply-templates mode="data" select="node()"/>
	</xsl:template>
	<xsl:template mode="data" match="text()">
		<xsl:copy/>
	</xsl:template>
	<xsl:template mode="data" match="*[@displayName and not(@code)]">
		<xsl:value-of select="@displayName"/>
	</xsl:template>
	<xsl:template mode="data" match="*[not(@displayName) and @code]">
		<xsl:value-of select="@code"/>
	</xsl:template>
	<xsl:template mode="data" match="*[@displayName and @code]">
		<xsl:value-of select="@displayName"/>
		<xsl:text> (</xsl:text>
		<xsl:value-of select="@code"/>
		<xsl:text>)</xsl:text>
	</xsl:template>
	<!-- add by Brian Suggs on 11-14-05. This will take care of the characteristic unit attribute that wasn't before taken care of -->
	<xsl:template mode="data" match="*[@value and @unit]" priority="1">
		<xsl:value-of select="@value"/>&#160;<xsl:value-of select="@unit"/>
	</xsl:template>
	<xsl:template mode="data" match="*[@value and not(@displayName)]">
		<xsl:value-of select="@value"/>
	</xsl:template>
	<xsl:template mode="data" match="*[@value and @displayName]">
		<xsl:value-of select="@value"/>
		<xsl:text>&#160;</xsl:text>
		<xsl:value-of select="@displayName"/>
	</xsl:template>
	<xsl:template mode="data" match="*[@value and (@xsi:type='TS' or contains(local-name(),'Time'))]" priority="1">
		<xsl:param name="displayMonth">true</xsl:param>
		<xsl:param name="displayDay">true</xsl:param>
		<xsl:param name="displayYear">true</xsl:param>
		<xsl:param name="delimiter">/</xsl:param>
		<xsl:variable name="year" select="substring(@value,1,4)"/>
		<xsl:variable name="month" select="substring(@value,5,2)"/>
		<xsl:variable name="day" select="substring(@value,7,2)"/>
		<!-- changed by Brian Suggs 11-13-05.  Changes made to display date in MM/DD/YYYY format instead of DD/MM/YYYY format -->
		<xsl:if test="$displayMonth = 'true'">
			<xsl:value-of select="$month"/>
			<xsl:value-of select="$delimiter"/>
		</xsl:if>
		<xsl:if test="$displayDay = 'true'">
			<xsl:value-of select="$day"/>
			<xsl:value-of select="$delimiter"/>
		</xsl:if>
		<xsl:if test="$displayYear = 'true'">
			<xsl:value-of select="$year"/>
		</xsl:if>
	</xsl:template>
	<xsl:template mode="data" match="*[v3:numerator]">
		<!-- changed by Brian Suggs 11-13-05.  Changes made to display the translation element displayName.  added /v3:translation -->
		<xsl:apply-templates mode="data" select="v3:numerator/v3:translation"/>
		<xsl:if test="v3:denominator/translation[not(@value='1' and (not(@displayName) or @displayName='1'))]">
			<xsl:text> : </xsl:text>
			<xsl:apply-templates mode="data" select="v3:denominator"/>
		</xsl:if>
	</xsl:template>
	<xsl:template name="effectiveDateHighlights">
		<xsl:if test="v3:document/v3:effectiveTime[@value != '']">
			<xsl:text>Revised: </xsl:text>
			<xsl:apply-templates mode="data" select="v3:document/v3:effectiveTime">
				<xsl:with-param name="displayMonth">true</xsl:with-param>
				<xsl:with-param name="displayDay">false</xsl:with-param>
				<xsl:with-param name="displayYear">true</xsl:with-param>
				<xsl:with-param name="delimiter">/</xsl:with-param>
			</xsl:apply-templates>
			<xsl:if test="$update-check-url-base">
				<xsl:variable name="url" select="concat($update-check-url-base, v3:document/v3:setId/@root)"/>
				<xsl:text> </xsl:text>
				<a href="{$url}">
					<xsl:text>Click here to check for updated version.</xsl:text>
				</a>
			</xsl:if>
		</xsl:if>
	</xsl:template>
	<xsl:template name="effectiveDate">
		<span class="EffectiveDate">
			<!-- changed by Brian Suggs 11-13-05. Added the Effective Date: text back in so that people will know what this date is for. -->
			<!-- changed by Brian Suggs 08-18-06. Modified text to state "Revised:" as per PCR 528 -->
			<xsl:if test="v3:document/v3:effectiveTime[@value != '']">
				<xsl:text>Revised: </xsl:text>
				<!-- changed by Brian Suggs 08-18-06. The effective date will now only display the month and year in the following format MM/YYYY (e.g. 08/2006). Code changed per PCR 528 -->
				<xsl:apply-templates mode="data" select="v3:document/v3:effectiveTime">
					<xsl:with-param name="displayMonth">true</xsl:with-param>
					<xsl:with-param name="displayDay">false</xsl:with-param>
					<xsl:with-param name="displayYear">true</xsl:with-param>
					<xsl:with-param name="delimiter">/</xsl:with-param>
				</xsl:apply-templates>
				<xsl:if test="$update-check-url-base">
					<xsl:variable name="url" select="concat($update-check-url-base, v3:document/v3:setId/@root)"/>
					<xsl:text> </xsl:text>
					<a href="{$url}">
						<xsl:text>Click here to check for updated version.</xsl:text>
					</a>
				</xsl:if>
			</xsl:if>
		</span>
	</xsl:template>
	<xsl:template name="distributorName">
			<span class="DistributorName">				
				<xsl:if test="v3:document/v3:author/v3:assignedEntity/v3:representedOrganization/v3:name != ''">					
					<xsl:value-of select="./v3:document/v3:author/v3:assignedEntity/v3:representedOrganization/v3:name"/>					
				</xsl:if>
			</span>
	</xsl:template>
	<!-- block at sections unless handled specially -->
	<xsl:template mode="data" match="v3:section"/>
	<!-- This section will display all of the subject information in one easy to read table. This view is replacing the previous display of the data elements. -->
	<!-- Sr4 now is v3:manufacturedProduct/v3:manufacturedProduct -->
	<xsl:template mode="subjects" match="/v3:document">
		<xsl:choose>			
			<xsl:when test="count(//v3:manufacturedProduct)=0">
				<table class="contentTablePetite" cellSpacing="0" cellPadding="3" width="100%">
					<tbody>
						<xsl:apply-templates mode="piMedNames" select="v3:component/v3:structuredBody/v3:component/v3:section/v3:subject/v3:manufacturedProduct/v3:manufacturedMedicine|v3:component/v3:structuredBody/v3:component/v3:section/v3:subject/v3:manufacturedProduct/v3:manufacturedProduct"/>
							
						<xsl:apply-templates mode="Sr4ProductInfoBasic" select="v3:component/v3:structuredBody/v3:component/v3:section/v3:subject/v3:manufacturedProduct|v3:code/@code"/>
					</tbody>
				</table>
			</xsl:when>		
			<xsl:otherwise>
				<!-- loop into the medicine portion of the label. This template will display all of the product information.  The following will be displayed within this section
				1. product code
				2. dosage form
				3. route of administration
				4. ingredients
				5. imprint information
				6. packaging information
				-->
				<xsl:apply-templates mode="subjects" select="v3:component/v3:structuredBody/v3:component//v3:section/v3:subject"/>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template>
	<xsl:template mode="subjects" match="v3:section/v3:subject">
		<xsl:param name="sr4"/>
		<xsl:variable name="nsr4" select="not(boolean(count(./v3:manufacturedProduct/v3:manufacturedMedicine)))"/>
		<table class="contentTablePetite" cellSpacing="0" cellPadding="3" width="100%">
			<tbody>
				<xsl:apply-templates mode="piMedNames" select="./v3:manufacturedProduct/v3:manufacturedMedicine|./v3:manufacturedProduct/v3:manufacturedProduct"/>
				<xsl:choose>
					<xsl:when test="boolean($nsr4)">
						<xsl:apply-templates mode="subjects" select="v3:manufacturedProduct/v3:manufacturedProduct"/>
					</xsl:when>
					<xsl:otherwise>
						<xsl:apply-templates mode="subjects" select="v3:manufacturedProduct/v3:manufacturedMedicine"/>
					</xsl:otherwise>
				</xsl:choose>	
			</tbody>
		</table>
		<br/>					
		<xsl:call-template name="image">
			<xsl:with-param name="path" select="v3:manufacturedProduct/v3:subjectOf/v3:characteristic[v3:code/@code='SPLIMAGE']"/>
		</xsl:call-template>
		<xsl:apply-templates mode="Sr4MarketingInfo" select="v3:manufacturedProduct"/>		
	</xsl:template>
	<xsl:template name="sr4ProductInfo" mode="subjects" match="v3:subject/v3:manufacturedProduct/v3:manufacturedProduct">	
		<xsl:apply-templates mode="Sr4ProductInfoBasic" select=".."/>
		<xsl:choose>
			<!-- if this is a multi-component subject then call to parts template -->
			<xsl:when test="./v3:part">
				<xsl:apply-templates mode="subjects" select="./v3:part">			
					<xsl:with-param name="sr4" select="true()"/>
				</xsl:apply-templates>
			</xsl:when>
			<!-- otherwise it is a single product and we simply need to display the ingredients, imprint and packaging. -->
			<xsl:otherwise>
				<xsl:call-template name="Sr4ProductInfoIng">			
					<xsl:with-param name="sr4" select="true()"/>
				</xsl:call-template>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template>		
	<xsl:template name="productInfo" mode="subjects" match="v3:subject/v3:manufacturedProduct/v3:manufacturedMedicine">		
		<xsl:apply-templates mode="Sr4ProductInfoBasic" select=".."/>
		<xsl:choose>
			<!-- if this is a multi-component subject then call to parts template -->
			<xsl:when test="./v3:part">
				<xsl:apply-templates mode="subjects" select="./v3:part">			
					<xsl:with-param name="sr4" select="false()"/>
				</xsl:apply-templates>
			</xsl:when>
			<!-- otherwise it is a single product and we simply need to display the ingredients, imprint and packaging. -->
			<xsl:otherwise>
				<xsl:call-template name="Sr4ProductInfoIng">			
					<xsl:with-param name="sr4" select="false()"/>
				</xsl:call-template>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template>	
	<xsl:template mode="Sr4ProductInfoBasic" match="@*|node()">	
		<xsl:variable name="iNumberOfRouteCodes" select="count(v3:consumedIn/v3:substanceAdministration/v3:routeCode)"/>
		<tr>
			<td>
				<table width="100%" cellpadding="5" cellspacing="0" class="formTablePetite">
					<tr>
						<td colspan="4" class="formHeadingTitle">Product Information</td>
					</tr>
						<tr class="formTableRowAlt">							
							<xsl:if test="not(../v3:part)">
								<td class="formLabel">Product Type</td>
								<td class="formItem">
									<xsl:value-of select="$documentTypes//v3:section[@code=$currentLoincCode]/v3:title"/>
								</td>
							</xsl:if>
							<xsl:choose>
								<xsl:when test="v3:manufacturedMedicine/v3:code/@code|v3:manufacturedProduct/v3:code/@code">
									<td class="formLabel">NDC Product Code (Source)</td>
									<td class="formItem">
										<xsl:value-of select="v3:manufacturedMedicine/v3:code/@code|v3:manufacturedProduct/v3:code/@code"/>
										<xsl:if test="v3:manufacturedProduct/v3:asEquivalentEntity/v3:code/@code = 'C64637'">
											(<xsl:value-of select="v3:manufacturedProduct/v3:asEquivalentEntity/v3:definingMaterialKind/v3:code/@code"/>)
										</xsl:if>
									</td>
								</xsl:when>
								<xsl:otherwise>
									<xsl:if test="v3:partProduct/v3:code/@code">
										<td class="formLabel">NDC Product Code (Source)</td>
										<td class="formItem">
											<xsl:value-of select="v3:partProduct/v3:code/@code"/>
											<xsl:if test="v3:partProduct/v3:asEquivalentEntity/v3:code/@code = 'C64637'">
												(<xsl:value-of select="v3:partProduct/v3:asEquivalentEntity/v3:definingMaterialKind/v3:code/@code"/>)
											</xsl:if>
										</td>
									</xsl:if>
								</xsl:otherwise>
							</xsl:choose>
						</tr>
					<xsl:if test="v3:subjectOf/v3:policy/v3:code/@displayName or  v3:consumedIn/v3:substanceAdministration/v3:routeCode and not(descendant::v3:part)">
						<tr class="formTableRow">
							<td width="30%" class="formLabel">Route of Administration</td>
							<td class="formItem">
								<xsl:for-each select="v3:consumedIn/v3:substanceAdministration/v3:routeCode">
									<xsl:value-of select="@displayName"/>
									<xsl:if test="(position()!=last()) and ($iNumberOfRouteCodes>1)">,&#160;</xsl:if>
								</xsl:for-each>
							</td>
							<td width="30%" class="formLabel">DEA Schedule</td>
							<td class="formItem">	
								<xsl:value-of select="v3:subjectOf/v3:policy/v3:code/@displayName"/>&#160;&#160;&#160;&#160;
							</td>
						</tr>
					</xsl:if>
				</table>
			</td>
		</tr>
	</xsl:template>
	
	<xsl:template name="Sr4ProductInfoIng">		
		<xsl:param name="sr4"/>
				<xsl:choose>
					<xsl:when test="$sr4">
						<tr>
							<td>
								<xsl:call-template name="sr4ActiveIngredients"/>
							</td>
						</tr>
						<tr>
							<td>
								<xsl:call-template name="sr4InactiveIngredients"/>
							</td>
						</tr>
					</xsl:when>
					<xsl:otherwise>
						<tr>
							<td>
								<xsl:call-template name="ingredients"/>
							</td>
						</tr>
					</xsl:otherwise>
				</xsl:choose>			
				<tr>
					<td>
						<xsl:call-template name="imprint"/>
					</td>
				</tr>
				<tr>
					<td>
						<xsl:call-template name="packaging">
							<xsl:with-param name="path" select="."/>
						</xsl:call-template>
					</td>
				</tr>
	</xsl:template>	
	
	<!-- multi-component packaging information will be displayed here.  -->
	<xsl:template mode="subjects" match="v3:part">
		<xsl:param name="sr4"/>
		<!-- only display the outer part packaging once -->
		<xsl:if test="count(preceding-sibling::v3:part) = 0">
			<tr>
				<td>
					<xsl:call-template name="packaging">
						<xsl:with-param name="path" select=".."/>
					</xsl:call-template>
				</td>
			</tr>
			<tr>
				<td>
					<xsl:call-template name="partQuantity">
						<xsl:with-param name="path" select=".."/>
					</xsl:call-template>
				</td>
			</tr>
		</xsl:if>
		<tr>
			<td>
				<table width="100%" cellspacing="0" cellpadding="5">
					<tr>
						<td class="contentTableTitle">Part <xsl:value-of select="count(preceding-sibling::v3:part)+1"/>&#160;of&#160;<xsl:value-of select="count(../v3:part)"/></td>
					</tr>
					<xsl:apply-templates mode="piMedNames" select="v3:partMedicine|v3:partProduct"/>					
				</table>
			</td>
		</tr>
		<xsl:apply-templates mode="Sr4ProductInfoBasic" select="."/>				
		<xsl:for-each select="v3:partMedicine|v3:partProduct">			
			<xsl:call-template name="Sr4ProductInfoIng">			
				<xsl:with-param name="sr4" select="$sr4"/>
			</xsl:call-template>
		</xsl:for-each>		
		<tr>
			<td >						
				<xsl:call-template name="image">
					<xsl:with-param name="path" select="v3:subjectOf/v3:characteristic[v3:code/@code='SPLIMAGE']"/>
				</xsl:call-template>
			</td>
		</tr>
		<tr>
			<td class="normalizer">
				<xsl:apply-templates mode="Sr4MarketingInfo" select="."/>	
			</td>
		</tr>
	</xsl:template>
	<!-- display the ingredient information (both active and inactive) -->
	<xsl:template name="sr4ActiveIngredients">
		<table width="100%" cellpadding="3" cellspacing="0" class="formTablePetite">
			<tr>
				<td colspan="3" class="formHeadingTitle">Active Ingredient/Active Moiety</td>
			</tr>
			<tr>
				<td class="formTitle">Ingredient Name</td>
				<td class="formTitle">Basis of Strength</td>
				<td class="formTitle">Strength</td>
			</tr>
			<xsl:if test="(count(./v3:ingredient[@classCode!='IACT'])=0)">
				<tr>
					<td colspan="3" class="formItem" align="center">No Active Ingredients Found</td>
				</tr>
			</xsl:if>
			<xsl:for-each select="./v3:ingredient[@classCode!='IACT']">
				<tr>
					<xsl:attribute name="class">
						<xsl:choose>
							<xsl:when test="position() mod 2 = 0">formTableRow</xsl:when>
							<xsl:otherwise>formTableRowAlt</xsl:otherwise>
						</xsl:choose>
					</xsl:attribute>
					<td class="formItem">
						<strong>
							<xsl:value-of select="v3:ingredientSubstance/v3:name"/>
						</strong>
						<xsl:if test="normalize-space(v3:ingredientSubstance/v3:activeMoiety/v3:activeMoiety/v3:name)">
							(<xsl:for-each select="v3:ingredientSubstance/v3:activeMoiety/v3:activeMoiety/v3:name">
								<xsl:value-of select="."/>
								<xsl:if test="position()!=last()">&#160;and&#160;</xsl:if>
							</xsl:for-each>)
						</xsl:if>
					</td>
					<td class="formItem">
						<xsl:choose>
							<xsl:when test="@classCode='ACTIR'"><xsl:value-of select="v3:ingredientSubstance/v3:asEquivalentSubstance/v3:definingSubstance/v3:name"/></xsl:when>
							<xsl:when test="@classCode='ACTIB'"><xsl:value-of select="v3:ingredientSubstance/v3:name"/></xsl:when>
							<xsl:otherwise><xsl:value-of select="v3:ingredientSubstance/v3:activeMoiety/v3:activeMoiety/v3:name"/></xsl:otherwise>
						</xsl:choose>
					</td>
					<td class="formItem">
						<xsl:value-of select="v3:quantity/v3:numerator/@value"/>&#160;<xsl:if test="normalize-space(v3:quantity/v3:numerator/@unit)!='1'"><xsl:value-of select="v3:quantity/v3:numerator/@unit"/></xsl:if>
						<xsl:if test="(v3:quantity/v3:denominator/@value and normalize-space(v3:quantity/v3:denominator/@value)!='1') 
							or (v3:quantity/v3:denominator/@unit and normalize-space(v3:quantity/v3:denominator/@unit)!='1')"> &#160;in&#160;<xsl:value-of select="v3:quantity/v3:denominator/@value"
						/>&#160;<xsl:if test="normalize-space(v3:quantity/v3:denominator/@unit)!='1'"><xsl:value-of select="v3:quantity/v3:denominator/@unit"/>
						</xsl:if></xsl:if>
					</td>
				</tr>
			</xsl:for-each>
		</table>
	</xsl:template>
	<xsl:template name="sr4InactiveIngredients">
		<table width="100%" cellpadding="3" cellspacing="0" class="formTablePetite">
			<tr>
				<!-- see PCR 801, just make the header bigger -->
				<td colspan="2" class="formHeadingTitle">Inactive Ingredients</td>
			</tr>
			<tr>
				<td class="formTitle">Ingredient Name</td>
				<td class="formTitle">Strength</td>
			</tr>
			<xsl:if test="(count(./v3:ingredient[@classCode='IACT'])=0)">
				<tr>
					<td colspan="2" class="formItem" align="center">No Inactive Ingredients Found</td>
				</tr>
			</xsl:if>			
			<xsl:for-each select="./v3:ingredient[@classCode='IACT']">
				<tr>
					<xsl:attribute name="class">
						<xsl:choose>
							<xsl:when test="position() mod 2 = 0">formTableRow</xsl:when>
							<xsl:otherwise>formTableRowAlt</xsl:otherwise>
						</xsl:choose>
					</xsl:attribute>
					<td class="formItem">
						<strong>
							<xsl:value-of select="v3:ingredientSubstance/v3:name"/>
						</strong>
						<xsl:if test="normalize-space(v3:ingredientSubstance/v3:activeMoiety/v3:activeMoiety/v3:name)"> (<xsl:value-of
							select="v3:ingredientSubstance/v3:activeMoiety/v3:activeMoiety/v3:name"/>) </xsl:if>
					</td>
					<td class="formItem">
						<xsl:value-of select="v3:quantity/v3:numerator/@value"/>&#160;<xsl:if test="normalize-space(v3:quantity/v3:numerator/@unit)!='1'"><xsl:value-of select="v3:quantity/v3:numerator/@unit"/></xsl:if>
						<xsl:if test="v3:quantity/v3:denominator/@value and normalize-space(v3:quantity/v3:denominator/@unit)!='1'"> &#160;in&#160;<xsl:value-of select="v3:quantity/v3:denominator/@value"
						/>&#160;<xsl:if test="normalize-space(v3:quantity/v3:denominator/@unit)!='1'"><xsl:value-of select="v3:quantity/v3:denominator/@unit"/>
						</xsl:if></xsl:if>
					</td>
				</tr>
			</xsl:for-each>
		</table>
	</xsl:template>
	<!-- display the ingredient information (both active and inactive) -->
	<xsl:template name="ingredients">
		<table width="100%" cellpadding="3" cellspacing="0" class="formTablePetite">
			<tr>
				<td colspan="4" class="formTitle">INGREDIENTS</td>
			</tr>
			<tr>
				<td class="formTitle">Name (Active Moiety)</td>
				<td class="formTitle">Type</td>
				<td class="formTitle">Strength</td>
			</tr>
			<xsl:if test="(count(./v3:activeIngredient)=0) and (count(./v3:inactiveIngredient)=0)">
				<tr>
					<td colspan="3" class="formItem" align="center">No Ingredients Found</td>
				</tr>
			</xsl:if>
			<xsl:for-each select="./v3:activeIngredient">
				<tr>
					<xsl:attribute name="class">
						<xsl:choose>
							<xsl:when test="position() mod 2 = 0">formTableRow</xsl:when>
							<xsl:otherwise>formTableRowAlt</xsl:otherwise>
						</xsl:choose>
					</xsl:attribute>
					<td class="formItem">
						<strong>
							<xsl:value-of select="v3:activeIngredientSubstance/v3:name"/>
						</strong>
						<xsl:if test="normalize-space(v3:activeIngredientSubstance/v3:activeMoiety/v3:activeMoiety/v3:name)"> (<xsl:value-of
								select="v3:activeIngredientSubstance/v3:activeMoiety/v3:activeMoiety/v3:name"/>) </xsl:if>
					</td>
					<td class="formItem">Active</td>
					<td class="formItem">
						<xsl:value-of select="v3:quantity/v3:numerator/v3:translation/@value"/>&#160;<xsl:value-of select="v3:quantity/v3:numerator/v3:translation/@displayName"/>
						<xsl:if test="normalize-space(v3:quantity/v3:denominator/v3:translation/@value)"> &#160;In&#160;<xsl:value-of select="v3:quantity/v3:denominator/v3:translation/@value"
								/>&#160;<xsl:value-of select="v3:quantity/v3:denominator/v3:translation/@displayName"/>
						</xsl:if>
					</td>
				</tr>
			</xsl:for-each>
			<xsl:variable name="iCount" select="count(./v3:activeIngredient)"/>
			<xsl:for-each select="./v3:inactiveIngredient">
				<tr>
					<xsl:attribute name="class">
						<xsl:choose>
							<xsl:when test="($iCount + position()) mod 2 = 0">formTableRow</xsl:when>
							<xsl:otherwise>formTableRowAlt</xsl:otherwise>
						</xsl:choose>
					</xsl:attribute>
					<td class="formItem">
						<strong>
							<xsl:value-of select="v3:inactiveIngredientSubstance/v3:name"/>
						</strong>
						<xsl:if test="normalize-space(v3:inactiveIngredientSubstance/v3:activeMoiety/v3:activeMoiety/v3:name)"> (<xsl:value-of
								select="v3:inactiveIngredientSubstance/v3:activeMoiety/v3:activeMoiety/v3:name"/>) </xsl:if>
					</td>
					<td class="formItem">Inactive</td>
					<td class="formItem">
						<xsl:value-of select="v3:quantity/v3:numerator/v3:translation/@value"/>&#160;<xsl:value-of select="v3:quantity/v3:numerator/v3:translation/@displayName"/>
						<xsl:if test="normalize-space(v3:quantity/v3:denominator/v3:translation/@value)"> &#160;In&#160;<xsl:value-of select="v3:quantity/v3:denominator/v3:translation/@value"
								/>&#160;<xsl:value-of select="v3:quantity/v3:denominator/v3:translation/@displayName"/>
						</xsl:if>
					</td>
				</tr>
			</xsl:for-each>
		</table>
	</xsl:template>
	<!-- display the imprint information in the specified order.  a apply-template could be used here but then we would not be able to control what order the
           imprint information is displayed in since there isn't a requirement specifying that the characteristic must be programmed in a certain order-->
	<xsl:template name="imprint">
		<table width="100%" cellpadding="3" cellspacing="0" class="formTablePetite">
			<tr>
				<td colspan="4" class="formHeadingTitle">Product Characteristics</td>
			</tr>
			<tr class="formTableRowAlt">
				<xsl:call-template name="color">
					<xsl:with-param name="path" select="../v3:subjectOf/v3:characteristic[v3:code/@code='SPLCOLOR']"/>
				</xsl:call-template>
				<xsl:call-template name="score">
					<xsl:with-param name="path" select="../v3:subjectOf/v3:characteristic[v3:code/@code='SPLSCORE']"/>
				</xsl:call-template>
			</tr>
			<tr class="formTableRow">
				<xsl:call-template name="shape">
					<xsl:with-param name="path" select="../v3:subjectOf/v3:characteristic[v3:code/@code='SPLSHAPE']"/>
				</xsl:call-template>
				<xsl:call-template name="size">
					<xsl:with-param name="path" select="../v3:subjectOf/v3:characteristic[v3:code/@code='SPLSIZE']"/>
				</xsl:call-template>
			</tr>
			<tr class="formTableRowAlt">
				<xsl:call-template name="flavor">
					<xsl:with-param name="path" select="../v3:subjectOf/v3:characteristic[v3:code/@code='SPLFLAVOR']"/>
				</xsl:call-template>
				<xsl:call-template name="imprintCode">
					<xsl:with-param name="path" select="../v3:subjectOf/v3:characteristic[v3:code/@code='SPLIMPRINT']"/>
				</xsl:call-template>
			</tr>
				<tr class="formTableRow">
					<xsl:call-template name="contains">
						<xsl:with-param name="path" select="../v3:subjectOf/v3:characteristic[v3:code/@code='SPLCONTAINS']"/>
					</xsl:call-template>
				</tr>
			<xsl:if test="../v3:subjectOf/v3:characteristic[v3:code/@code='SPLCOATING']|../v3:subjectOf/v3:characteristic[v3:code/@code='SPLSYMBOL']">
				<tr class="formTableRowAlt">
					<xsl:call-template name="coating">
						<xsl:with-param name="path" select="../v3:subjectOf/v3:characteristic[v3:code/@code='SPLCOATING']"/>
					</xsl:call-template>
					<xsl:call-template name="symbol">
						<xsl:with-param name="path" select="../v3:subjectOf/v3:characteristic[v3:code/@code='SPLSYMBOL']"/>
					</xsl:call-template>
				</tr>
			</xsl:if>
		</table>
	</xsl:template>
	<!-- display the imprint characteristic color -->
	<xsl:template name="color">
		<xsl:param name="path" select="."/>
		<td class="formLabel">Color</td>
		<td class="formItem">
			<xsl:for-each select="$path/v3:value">
				<xsl:if test="position() > 1">,&#160;</xsl:if>
				<xsl:value-of select="./@displayName"/>
				<xsl:if test="normalize-space(./v3:originalText)"> (<xsl:value-of select="./v3:originalText"/>) </xsl:if>
			</xsl:for-each>
			<xsl:if test="not($path/v3:value)">&#160;&#160;&#160;&#160;</xsl:if>
		</td>
	</xsl:template>
	<!-- display the imprint characteristic score -->
	<xsl:template name="score">
		<xsl:param name="path" select="."/>
		<td class="formLabel">Score</td>
		<td class="formItem">
			<xsl:choose>
				<xsl:when test="$path/v3:value/@value='1'">
					no score
				</xsl:when>
				<xsl:when test="$path/v3:value/@value &gt; 1">
					<xsl:value-of select="$path/v3:value/@value"/>&#160;pieces
				</xsl:when>
				<xsl:when test="$path/v3:value/@nullFlavor='OTH'">
					score with uneven pieces
				</xsl:when>
				<xsl:otherwise>&#160;&#160;&#160;&#160;</xsl:otherwise>
			</xsl:choose>
		</td>
	</xsl:template>
	<!-- display the imprint characteristic shape -->
	<xsl:template name="shape">
		<xsl:param name="path" select="."/>
		<td class="formLabel">Shape</td>
		<td class="formItem">
			<xsl:value-of select="$path/v3:value/@displayName"/>
			<xsl:if test="normalize-space($path/v3:value/v3:originalText)"> (<xsl:value-of select="$path/v3:value/v3:originalText"/>) </xsl:if>
		</td>
	</xsl:template>
	<!-- display the imprint characteristic flavor -->
	<xsl:template name="flavor">
		<xsl:param name="path" select="."/>
		<td class="formLabel">Flavor</td>
		<td class="formItem">			
			<xsl:for-each select="$path/v3:value">
				<xsl:if test="position() > 1">,&#160;</xsl:if>
				<xsl:value-of select="./@displayName"/>
				<xsl:if test="normalize-space(./v3:originalText)"> (<xsl:value-of select="./v3:originalText"/>) </xsl:if>
			</xsl:for-each>
		</td>
	</xsl:template>
	<!-- display the imprint characteristic code -->
	<xsl:template name="imprintCode">
		<xsl:param name="path" select="."/>
		<td class="formLabel">Imprint Code</td>
		<td class="formItem">
			<xsl:value-of select="$path[v3:value/@xsi:type='ST']"/>
		</td>
	</xsl:template>
	<!-- display the imprint characteristic size -->
	<xsl:template name="size">
		<xsl:param name="path" select="."/>
		<td class="formLabel">Size</td>
		<td class="formItem">
			<xsl:value-of select="$path/v3:value/@value"/>
			<xsl:value-of select="$path/v3:value/@unit"/>
		</td>
	</xsl:template>
	<!-- display the imprint characteristic symbol -->
	<xsl:template name="symbol">
		<xsl:param name="path" select="."/>
		<td class="formLabel">Symbol</td>
		<td class="formItem">
			<xsl:value-of select="$path/v3:value/@value"/>
		</td>
	</xsl:template>
	<!-- display the imprint characteristic coating -->
	<xsl:template name="coating">
		<xsl:param name="path" select="."/>
		<td class="formLabel">Coating</td>
		<td class="formItem">
			<xsl:value-of select="$path/v3:value/@value"/>
		</td>
	</xsl:template>	
	<xsl:template name="image">
		<xsl:param name="path" select="."/>
		<xsl:if test="string-length($path/v3:value/v3:reference/@value) > 0">
			<img alt="Image of Product" src="{$path/v3:value/v3:reference/@value}"/>
		</xsl:if>
	</xsl:template>
	
	<xsl:template name="contains">
		<xsl:param name="path" select="."/>
		<td class="formLabel">Contains</td>
		<td class="formItem">
			<xsl:for-each select="$path/v3:value">
				<xsl:if test="position() > 1">,&#160;</xsl:if>
				<xsl:value-of select="./@displayName"/>
				<xsl:if test="normalize-space(./v3:originalText)"> (<xsl:value-of select="./v3:originalText"/>) </xsl:if>
			</xsl:for-each>
			<xsl:if test="not($path/v3:value)">&#160;&#160;&#160;&#160;</xsl:if>
		</td>
	</xsl:template>
	<xsl:template name="partQuantity">
		<xsl:param name="path" select="."/>
		<table width="100%" cellpadding="3" cellspacing="0" class="formTable">
			<tr>
				<td colspan="5" class="formTitle">QUANTITY OF PARTS</td>
			</tr>
			<tr>
				<td width="5" class="formTitle">Part&#160;#</td>
				<td class="formTitle">Package Quantity</td>
				<td class="formTitle">Total Product Quantity</td>
			</tr>
			<xsl:for-each select="$path/v3:part">
				<tr>
					<xsl:attribute name="class">
						<xsl:choose>
							<xsl:when test="position() mod 2 = 0">formTableRow</xsl:when>
							<xsl:otherwise>formTableRowAlt</xsl:otherwise>
						</xsl:choose>
					</xsl:attribute>
					<td width="5" class="formItem">
						<strong>Part&#160;<xsl:value-of select="position()"/></strong>
					</td><!-- support both Sr3 and Sr4 -->
					<xsl:choose>
						<xsl:when test="./v3:partProduct">
							<td class="formItem">	
								<xsl:if test="./v3:partProduct/v3:asContent/v3:quantity/v3:numerator/@value">
									<xsl:value-of select="round(v3:quantity/v3:numerator/@value div ./v3:partProduct/v3:asContent/v3:quantity/v3:numerator/@value)"
									/>&#160;<xsl:value-of select="./v3:partProduct/v3:asContent/v3:containerPackagedProduct/v3:formCode/@displayName"/>
								</xsl:if>							
								&#160; 
							</td>							
							<td class="formItem">
								<xsl:value-of select="v3:quantity/v3:numerator/@value"/>&#160;<xsl:if test="normalize-space(v3:quantity/v3:numerator/@unit)!='1'"><xsl:value-of select="v3:quantity/v3:numerator/@unit"/></xsl:if>
							<xsl:if test="(v3:quantity/v3:denominator/@value and normalize-space(v3:quantity/v3:denominator/@value)!='1') 
								or (v3:quantity/v3:denominator/@unit and normalize-space(v3:quantity/v3:denominator/@unit)!='1')"> &#160;in&#160;<xsl:value-of select="v3:quantity/v3:denominator/@value"
								/>&#160;<xsl:if test="normalize-space(v3:quantity/v3:denominator/@unit)!='1'"><xsl:value-of select="v3:quantity/v3:denominator/@unit"/>
								</xsl:if></xsl:if>
							</td>
						</xsl:when>
						<xsl:otherwise>
							<td class="formItem">				
								<xsl:if test="./v3:partMedicine/v3:asContent/v3:quantity/v3:numerator/v3:translation/@value">
									<xsl:value-of select="round(v3:quantity/v3:numerator/v3:translation/@value div ./v3:partMedicine/v3:asContent/v3:quantity/v3:numerator/v3:translation/@value)"
									/>&#160;<xsl:value-of select="./v3:partMedicine/v3:asContent/v3:containerPackagedMedicine/v3:formCode/@displayName"/>
								</xsl:if>						
								&#160; 
							</td>
							<td class="formItem"><xsl:value-of select="v3:quantity/v3:numerator/v3:translation/@value"/>&#160;<xsl:value-of select="v3:quantity/v3:numerator/v3:translation/@displayName"/>
								<xsl:if test="normalize-space(v3:quantity/v3:denominator/v3:translation/@value)"> &#160;in&#160;<xsl:value-of select="v3:quantity/v3:denominator/v3:translation/@value"
								/>&#160;<xsl:value-of select="v3:quantity/v3:denominator/v3:translation/@displayName"/>
								</xsl:if>
							</td>
						</xsl:otherwise>
					</xsl:choose>		
				</tr>
			</xsl:for-each>
		</table>
	</xsl:template>
	<xsl:template name="packaging">
		<xsl:param name="path" select="."/>
		<table width="100%" cellpadding="3" cellspacing="0" class="formTablePetite">
			<tr>
				<td colspan="5" class="formHeadingTitle">Packaging</td>
			</tr>
			<tr>
				<td width="1" class="formTitle">#</td>
				<td class="formTitle">NDC</td>
				<td class="formTitle">Package Description</td>
				<td class="formTitle">Multilevel Packaging</td>
			</tr>
			<xsl:for-each select="$path/v3:asContent">
				<xsl:call-template name="packageInfo">
					<xsl:with-param name="path" select="."/>
					<xsl:with-param name="number" select="position()"/>
				</xsl:call-template>
			</xsl:for-each>
			<xsl:if test="count($path/v3:asContent) = 0">
				<tr>
					<td colspan="5" class="formTitle">
						<strong>Package Information Not Applicable</strong>
					</td>
				</tr>
			</xsl:if>
		</table>
	</xsl:template>
	<xsl:template name="packageInfo">
		<xsl:param name="path"/>
		<xsl:param name="number" select="1"/>
		<xsl:choose>
			<xsl:when test="$path/v3:containerPackagedProduct">
				<xsl:if test="$path/v3:containerPackagedProduct/v3:asContent">
					<xsl:call-template name="packageInfo">
						<xsl:with-param name="path" select="$path/v3:containerPackagedProduct/v3:asContent"/>
						<xsl:with-param name="number" select="$number"/>
					</xsl:call-template>
				</xsl:if>
				<xsl:variable name="tab">
					<xsl:for-each select="$path//v3:containerPackagedProduct//v3:asContent">&#160;&#160;</xsl:for-each>
				</xsl:variable>
				<xsl:for-each select="$path/v3:containerPackagedProduct">
					<tr>
						<xsl:attribute name="class">
							<xsl:choose>
								<xsl:when test="$number mod 2 = 0">formTableRow</xsl:when>
								<xsl:otherwise>formTableRowAlt</xsl:otherwise>
							</xsl:choose>
						</xsl:attribute>
						<td class="formItem">
							<strong>
								<xsl:value-of select="$number"/>
							</strong>
						</td>
						<td class="formItem">
							<xsl:value-of select="./v3:code/@code"/>
						</td>
						<td class="formItem">
							<xsl:choose>
								<xsl:when test="$path/v3:quantity/v3:numerator/@value">
									<xsl:value-of select="$path/v3:quantity/v3:numerator/@value"/>
								</xsl:when>
								<xsl:otherwise>
									<xsl:value-of select="$path/v3:quantity/v3:numerator/v3:translation/@value"/>
								</xsl:otherwise>
							</xsl:choose>&#160;<xsl:choose>
								<xsl:when test="$path/v3:quantity/v3:numerator/@unit and $path/v3:quantity/v3:numerator/@unit != '1'">
									<xsl:value-of select="$path/v3:quantity/v3:numerator/@unit"/>
									<xsl:if test="$path/v3:quantity/v3:numerator/v3:translation/@displayName">
									(<xsl:value-of select="$path/v3:quantity/v3:numerator/v3:translation/@displayName"/>)
									</xsl:if>
								</xsl:when>
								<xsl:otherwise>							
									<xsl:value-of select="$path/v3:quantity/v3:numerator/v3:translation/@displayName"/>
								</xsl:otherwise>
							</xsl:choose>				
							In&#160;1
							<xsl:value-of select="./v3:formCode/@displayName"/>
							<xsl:if test="normalize-space($path/v3:quantity/v3:denominator/v3:translation/@displayName) != ''"> (<xsl:value-of select="$path/v3:quantity/v3:denominator/@value"
							/>&#160;<xsl:value-of select="$path/v3:quantity/v3:denominator/v3:translation/@displayName"/>) </xsl:if>
						</td>
						<xsl:choose>
							<xsl:when test="ancestor::v3:containerPackagedProduct and descendant::v3:asContent">
								<td class="formItem">This package is contained within the <xsl:value-of select="v3:asContent/v3:containerPackagedProduct/v3:formCode/@displayName"/><xsl:if
									test="v3:asContent/v3:containerPackagedProduct/v3:code/@code">&#160;(<xsl:value-of select="v3:asContent/v3:containerPackagedProduct/v3:code/@code"/>)</xsl:if> and
									contains a <xsl:value-of select="../../v3:formCode/@displayName"/><xsl:if test="../../v3:code/@code">&#160;(<xsl:value-of
										select="../../v3:code/@code"/>)</xsl:if></td>
							</xsl:when>
							<xsl:when test="ancestor::v3:containerPackagedProduct">
								<td class="formItem">contains a <xsl:value-of select="../../v3:formCode/@displayName"/><xsl:if test="../../v3:code/@code"
									>&#160;(<xsl:value-of select="../../v3:code/@code"/>)</xsl:if></td>
							</xsl:when>
							<xsl:when test="descendant::v3:asContent">
								<td class="formItem">
									<xsl:text>This package is contained within </xsl:text>
									<xsl:choose>
										<xsl:when test="count(descendant::v3:asContent) > 1">
											<xsl:text>a </xsl:text>
										</xsl:when>
										<xsl:otherwise>
											<xsl:text>the </xsl:text>
										</xsl:otherwise>
									</xsl:choose>
									<xsl:for-each select="descendant::v3:asContent">
										<xsl:if test="position() > 1">
											<xsl:text> and a </xsl:text>
										</xsl:if>
										<xsl:value-of select="./v3:containerPackagedProduct/v3:formCode/@displayName"/>
										<xsl:if test="./v3:containerPackagedProduct/v3:code/@code">&#160;(<xsl:value-of select="./v3:containerPackagedProduct/v3:code/@code"/>)</xsl:if>
									</xsl:for-each>
								</td>
							</xsl:when>
							<xsl:otherwise>
								<td class="formItem">None</td>
							</xsl:otherwise>
						</xsl:choose>
					</tr>
				</xsl:for-each>
			</xsl:when>
			<xsl:otherwise>
				<xsl:if test="$path/v3:containerPackagedMedicine/v3:asContent">
					<xsl:call-template name="packageInfo">
						<xsl:with-param name="path" select="$path/v3:containerPackagedMedicine/v3:asContent"/>
						<xsl:with-param name="number" select="$number"/>
					</xsl:call-template>
				</xsl:if>
				<xsl:variable name="tab">
					<xsl:for-each select="$path//v3:containerPackagedMedicine//v3:asContent">&#160;&#160;</xsl:for-each>
				</xsl:variable>
				<xsl:for-each select="$path/v3:containerPackagedMedicine">
					<tr>
						<xsl:attribute name="class">
							<xsl:choose>
								<xsl:when test="$number mod 2 = 0">formTableRow</xsl:when>
								<xsl:otherwise>formTableRowAlt</xsl:otherwise>
							</xsl:choose>
						</xsl:attribute>
						<td class="formItem">
							<strong>
								<xsl:value-of select="$number"/>
							</strong>
						</td>
						<td class="formItem">
							<xsl:value-of select="./v3:code/@code"/>
						</td>
						<td class="formItem">
							<xsl:choose>
								<xsl:when test="$path/v3:quantity/v3:numerator/@value">
									<xsl:value-of select="$path/v3:quantity/v3:numerator/@value"/>
								</xsl:when>
								<xsl:otherwise>
									<xsl:value-of select="$path/v3:quantity/v3:numerator/v3:translation/@value"/>
								</xsl:otherwise>
							</xsl:choose>&#160;<xsl:choose>
								<xsl:when test="$path/v3:quantity/v3:numerator/@unit and $path/v3:quantity/v3:numerator/@unit != '1'">
									<xsl:value-of select="$path/v3:quantity/v3:numerator/@unit"/>
									(<xsl:value-of select="$path/v3:quantity/v3:numerator/v3:translation/@displayName"/>)
								</xsl:when>
								<xsl:otherwise>							
									<xsl:value-of select="$path/v3:quantity/v3:numerator/v3:translation/@displayName"/>
								</xsl:otherwise>
							</xsl:choose>				
							In&#160;1
							<xsl:value-of select="./v3:formCode/@displayName"/>
							<xsl:if test="normalize-space($path/v3:quantity/v3:denominator/v3:translation/@displayName) != ''"> (<xsl:value-of select="$path/v3:quantity/v3:denominator/@value"
							/>&#160;<xsl:value-of select="$path/v3:quantity/v3:denominator/v3:translation/@displayName"/>) </xsl:if>
						</td>
						<xsl:choose>
							<xsl:when test="ancestor::v3:containerPackagedMedicine and descendant::v3:asContent">
								<td class="formItem">This package is contained within the <xsl:value-of select="v3:asContent/v3:containerPackagedMedicine/v3:formCode/@displayName"/><xsl:if
									test="v3:asContent/v3:containerPackagedMedicine/v3:code/@code">&#160;(<xsl:value-of select="v3:asContent/v3:containerPackagedMedicine/v3:code/@code"/>)</xsl:if> and
									contains a <xsl:value-of select="../../v3:formCode/@displayName"/><xsl:if test="../../v3:code/@code">&#160;(<xsl:value-of
										select="../../v3:code/@code"/>)</xsl:if></td>
							</xsl:when>
							<xsl:when test="ancestor::v3:containerPackagedMedicine">
								<td class="formItem">contains a <xsl:value-of select="../../v3:formCode/@displayName"/><xsl:if test="../../v3:code/@code"
									>&#160;(<xsl:value-of select="../../v3:code/@code"/>)</xsl:if></td>
							</xsl:when>
							<xsl:when test="descendant::v3:asContent">
								<td class="formItem">
									<xsl:text>This package is contained within </xsl:text>
									<xsl:choose>
										<xsl:when test="count(descendant::v3:asContent) > 1">
											<xsl:text>a </xsl:text>
										</xsl:when>
										<xsl:otherwise>
											<xsl:text>the </xsl:text>
										</xsl:otherwise>
									</xsl:choose>
									<xsl:for-each select="descendant::v3:asContent">
										<xsl:if test="position() > 1">
											<xsl:text> and a </xsl:text>
										</xsl:if>
										<xsl:value-of select="./v3:containerPackagedMedicine/v3:formCode/@displayName"/>
										<xsl:if test="./v3:containerPackagedMedicine/v3:code/@code">&#160;(<xsl:value-of select="./v3:containerPackagedMedicine/v3:code/@code"/>)</xsl:if>
									</xsl:for-each>
								</td>
							</xsl:when>
							<xsl:otherwise>
								<td class="formItem">None</td>
							</xsl:otherwise>
						</xsl:choose>
					</tr>
				</xsl:for-each>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template>
	<xsl:template name="Sr4Marketing" mode="Sr4MarketingInfo" match="*">		
		<xsl:if test="(count(./v3:subjectOf/v3:approval)>0)">
		<table width="100%" cellpadding="3" cellspacing="0" class="formTableMorePetite">
			<tr>
				<td colspan="4" class="formHeadingReg"><font class="formHeadingTitle" >Marketing Information</font></td>
			</tr>
			<tr>
				<td class="formTitle">Marketing Category</td>
				<td class="formTitle">Application Number or Monograph Citation</td>
				<td class="formTitle">Marketing Start Date</td>
				<td class="formTitle">Marketing End Date</td>
			</tr>
			<tr class="formTableRowAlt">
				<td class="formItem">
						<xsl:value-of select="./v3:subjectOf/v3:approval/v3:code/@displayName"/>
				</td>
				<td class="formItem">
					<xsl:value-of select="./v3:subjectOf/v3:approval/v3:id/@extension"/>
				</td>
				<td class="formItem">						
					<xsl:call-template name="string-to-date">
						<xsl:with-param name="text"><xsl:value-of select="./v3:subjectOf/v3:marketingAct/v3:effectiveTime/v3:low/@value"/></xsl:with-param>
					</xsl:call-template>
				</td>
				<td class="formItem">					
					<xsl:call-template name="string-to-date">
						<xsl:with-param name="text"><xsl:value-of select="./v3:subjectOf/v3:marketingAct/v3:effectiveTime/v3:high/@value"/></xsl:with-param>
					</xsl:call-template>
				</td>
			</tr>
		</table>
			<br/>
		</xsl:if>
	</xsl:template>	
	<xsl:template name="Sr4Labeler" mode="subjects" match="//v3:author/v3:assignedEntity/v3:representedOrganization">	
		<xsl:if test="(count(./v3:name)>0)">
		<table width="100%" cellpadding="3" cellspacing="0" class="formTableMorePetite">
			<tr>
				<td colspan="4" class="formHeadingReg"><font class="formHeadingTitle" >Labeler -&#160;</font><xsl:value-of select="./v3:name"/> 
					<xsl:choose>
						<xsl:when test="./v3:id[@root='1.3.6.1.4.1.519.1']/@extension">
							(<xsl:value-of select="./v3:id[@root='1.3.6.1.4.1.519.1']/@extension"/>)
						</xsl:when>
						<xsl:when  test="./v3:assignedEntity/v3:assignedOrganization/v3:id[@root='1.3.6.1.4.1.519.1']/@extension">
							(<xsl:value-of select="./v3:assignedEntity/v3:assignedOrganization/v3:id[@root='1.3.6.1.4.1.519.1']/@extension"/>)
						</xsl:when>
						<xsl:otherwise/>
					</xsl:choose>
					<xsl:if test="$currentLoincCode = '51726-8'">
						<font class="formHeadingTitle" >NDC Labeler Code: </font>
						<xsl:choose>
							<xsl:when test="./v3:id[@root='2.16.840.1.113883.6.69']/@extension">
								<xsl:value-of select="./v3:id[@root='2.16.840.1.113883.6.69']/@extension"/>
							</xsl:when>						
							<xsl:when  test="./v3:assignedEntity/v3:assignedOrganization/v3:id[@root='2.16.840.1.113883.6.69']/@extension">
								<xsl:value-of select="./v3:assignedEntity/v3:assignedOrganization/v3:id[@root='2.16.840.1.113883.6.69']/@extension"/>
							</xsl:when>
							<xsl:otherwise/>
						</xsl:choose>
					</xsl:if>
				</td>
			</tr>
			<xsl:if test="(count(./v3:contactParty)>0)">
			<tr>
				<td class="formTitle">Contact</td>
				<td class="formTitle">Address</td>
				<td class="formTitle">Telephone Number</td>
				<td class="formTitle">Email Address</td>
			</tr>
			<tr class="formTableRowAlt">
				<td class="formItem">
					<xsl:value-of select="./v3:contactParty/v3:contactPerson/v3:name"/>
				</td>
				<td class="formItem">		
					<xsl:apply-templates mode="format" select="./v3:contactParty/v3:addr"/>
				</td>
				<td class="formItem">
					<xsl:value-of select=" substring-after(./v3:contactParty/v3:telecom[position()=1]/@value, 'tel:')"/>
				</td>
				<td class="formItem">
					<xsl:value-of select=" substring-after(./v3:contactParty/v3:telecom[position()=last()]/@value, 'mailto:')"/>
				</td>
			</tr>
			</xsl:if>
		</table>
		</xsl:if>
	</xsl:template>	
	
	<xsl:template name="Sr4Manufacturer" mode="subjects" match="//v3:author/v3:assignedEntity/v3:representedOrganization/v3:assignedEntity/v3:assignedOrganization">	
		<xsl:if test="./v3:name">
		<table width="100%" cellpadding="3" cellspacing="0" class="formTableMorePetite">
			<tr>
				<td colspan="4" class="formHeadingReg"><font class="formHeadingTitle" >Registrant -&#160;</font><xsl:value-of select="./v3:name"/><xsl:if test="./v3:id/@extension"> (<xsl:value-of select="./v3:id/@extension"/>)</xsl:if></td>
			</tr>
			<xsl:if test="(count(./v3:contactParty)>0)">
			<tr>
				<td class="formTitle">Contact</td>
				<td class="formTitle">Address</td>
				<td class="formTitle">Telephone Number</td>
				<td class="formTitle">Email Address</td>
			</tr>
			<tr class="formTableRowAlt">
				<td class="formItem">
					<xsl:value-of select="./v3:contactParty/v3:contactPerson/v3:name"/>
				</td>
				<td class="formItem">		
					<xsl:apply-templates mode="format" select="./v3:contactParty/v3:addr"/>
				</td>
				<td class="formItem">
					<xsl:value-of select=" substring-after(./v3:contactParty/v3:telecom[position()=1]/@value, 'tel:')"/>
				</td>
				<td class="formItem">
					<xsl:value-of select=" substring-after(./v3:contactParty/v3:telecom[position()=last()]/@value, 'mailto:')"/>
				</td>
			</tr>
			</xsl:if>
		</table>
		</xsl:if>
	</xsl:template>	
	
	<xsl:template name="Sr4Establishment" mode="subjects" match="//v3:author/v3:assignedEntity/v3:representedOrganization/v3:assignedEntity/v3:assignedOrganization/v3:assignedEntity/v3:assignedOrganization">	
		<xsl:if test="./v3:name">
		<table width="100%" cellpadding="3" cellspacing="0" class="formTableMorePetite">
			<tr>
				<td colspan="4" class="formHeadingReg"><font class="formHeadingTitle" >Establishment</font></td>				
			</tr>
			<tr>
				<td class="formTitle">Name</td>
				<td class="formTitle">Address</td>
				<td class="formTitle">ID/FEI</td>
				<td class="formTitle">Operations</td>
			</tr>
			<tr class="formTableRowAlt">
				<td class="formItem">
					<xsl:value-of select="./v3:name"/>
				</td>
				<td class="formItem">	
					<xsl:apply-templates mode="format" select="./v3:addr"/>	
				</td>
				<!-- root = "1.3.6.1.4.1.519.1" -->
				<td class="formItem">
					<xsl:value-of select="./v3:id[@root='1.3.6.1.4.1.519.1']/@extension"/><xsl:if test="./v3:id[@root='1.3.6.1.4.1.519.1']/@extension and ./v3:id[not(@root='1.3.6.1.4.1.519.1')]/@extension">/</xsl:if><xsl:value-of select="./v3:id[not(@root='1.3.6.1.4.1.519.1')]/@extension"/>
				</td>
				<td class="formItem">
					<xsl:for-each select="../v3:performance/v3:actDefinition/v3:code">
						<xsl:value-of select="@displayName"/>
						<xsl:if test="position()!=last()">,&#160;</xsl:if>
					</xsl:for-each>
				</td>
			</tr>
			<xsl:if test="(count(./v3:contactParty)>0)">
			<tr>
				<td class="formTitle">Contact</td>
				<td class="formTitle">Address</td>
				<td class="formTitle">Telephone Number</td>
				<td class="formTitle">Email Address</td>
			</tr>
			<tr class="formTableRowAlt">
				<td class="formItem">
					<xsl:value-of select="./v3:contactParty/v3:contactPerson/v3:name"/>
				</td>
				<td class="formItem">		
					<xsl:apply-templates mode="format" select="./v3:contactParty/v3:addr"/>
				</td>
				<td class="formItem">
					<xsl:value-of select=" substring-after(./v3:contactParty/v3:telecom[position()=1]/@value, 'tel:')"/>
				</td>
				<td class="formItem">
					<xsl:value-of select=" substring-after(./v3:contactParty/v3:telecom[position()=last()]/@value, 'mailto:')"/>
				</td>
			</tr>
			<xsl:for-each select="./v3:assignedEntity[v3:performance/v3:actDefinition/v3:code/@code='C73330']">
			<tr>
				<td class="formTitle">US Agent (ID)</td>
				<td class="formTitle">Address</td>
				<td class="formTitle">Telephone Number</td>
				<td class="formTitle">Email Address</td>
			</tr>
			<tr class="formTableRowAlt">
				<td class="formItem">
					<xsl:value-of select="v3:assignedOrganization/v3:name"/> (<xsl:value-of select="v3:assignedOrganization/v3:id/@extension"/>)
				</td>
				<td class="formItem">		
					<xsl:apply-templates mode="format" select="v3:assignedOrganization/v3:addr"/>
				</td>
				<td class="formItem">
					<xsl:value-of select=" substring-after(v3:assignedOrganization/v3:telecom[position()=1]/@value, 'tel:')"/>
				</td>
				<td class="formItem">
					<xsl:value-of select=" substring-after(v3:assignedOrganization/v3:telecom[position()=last()]/@value, 'mailto:')"/>
				</td>
			</tr>
			</xsl:for-each>
				<!-- 53617 changed to 73599 -->
			<xsl:for-each select="./v3:assignedEntity[v3:performance/v3:actDefinition/v3:code/@code='C73599']">	
			<tr>
				<td class="formTitle">Importer (ID)</td>
				<td class="formTitle">Address</td>
				<td class="formTitle">Telephone Number</td>
				<td class="formTitle">Email Address</td>
			</tr>
			
			<tr class="formTableRowAlt">
				<td class="formItem">
				<xsl:value-of select="v3:assignedOrganization/v3:name"/> (<xsl:value-of select="v3:assignedOrganization/v3:id/@extension"/>)
				</td>
				<td class="formItem">		
					<xsl:apply-templates mode="format" select="v3:assignedOrganization/v3:addr"/>
				</td>
				<td class="formItem">
					<xsl:value-of select=" substring-after(v3:assignedOrganization/v3:telecom[position()=1]/@value, 'tel:')"/>
				</td>
				<td class="formItem">
					<xsl:value-of select=" substring-after(v3:assignedOrganization/v3:telecom[position()=last()]/@value, 'mailto:')"/>
				</td>
			</tr>
			</xsl:for-each>
			</xsl:if>
		</table>
		</xsl:if>
	</xsl:template>	
	
	<!-- Start PLR Information templates
			1. product code
			2. dosage form
			3. route of administration
			4. ingredients
			5. imprint information
			6. packaging information
    -->
	<xsl:template name="PLRIndications" mode="indication"
		match="v3:section [v3:code [descendant-or-self::* [(self::v3:code or self::v3:translation) and @codeSystem='2.16.840.1.113883.6.1' and @code='34067-9'] ] ]">
		<xsl:if test="count(//v3:reason) > 0">
			<table class="contentTablePetite" cellSpacing="0" cellPadding="3" width="100%">
				<tbody>
					<tr>
						<td class="contentTableTitle">Indications and Usage</td>
					</tr>
					<tr>
						<td>
							<table class="formTablePetite" cellSpacing="0" cellPadding="3" width="100%">
								<tbody>
									<tr>
										<td class="formTitle" colSpan="2">INDICATIONS</td>
										<td class="formTitle" colSpan="4">USAGE</td>
									</tr>
									<tr>
										<td class="formTitle">Indication</td>
										<td class="formTitle">Intent&#160;Of Use</td>
										<td class="formTitle">Maximum Dose</td>
										<td class="formTitle" colSpan="4">Conditions &amp; Limitations Of Use</td>
									</tr>
									<!-- Repeat Me -->
									<xsl:for-each select="$indicationSection//v3:excerpt/v3:highlight/v3:subject">
										<tr class="formTableRowAlt">
											<td class="formItem" valign="top">
												<strong><xsl:value-of select="./v3:substanceAdministration/v3:reason/v3:indicationObservationCriterion/v3:value/@displayName"/> (<xsl:value-of
														select="./v3:substanceAdministration/v3:reason/v3:indicationObservationCriterion/v3:code/@displayName"/>)</strong>
											</td>
											<td class="formItem" valign="top">
												<xsl:value-of select="./v3:substanceAdministration/v3:reason/@typeCode"/>
											</td>
											<td class="formItem" valign="top">
												<xsl:choose>
													<xsl:when test="./v3:substanceAdministration/v3:maxDoseQuantity">
														<xsl:value-of select="./v3:substanceAdministration/v3:maxDoseQuantity/v3:numerator/@value"/>&#160; <xsl:value-of
															select="./v3:substanceAdministration/v3:maxDoseQuantity/v3:numerator/@unit"/>&#160;per&#160; <xsl:value-of
															select="./v3:substanceAdministration/v3:maxDoseQuantity/v3:denominator/@value"/>&#160; <xsl:value-of
															select="./v3:substanceAdministration/v3:maxDoseQuantity/v3:denominator/@unit"/>
													</xsl:when>
													<xsl:otherwise>
														<xsl:for-each select="//v3:maxDoseQuantity[ancestor::v3:section/v3:code/@code = $dosageAndAdministrationSectionCode]">
															<xsl:value-of select="./v3:numerator/@value"/>&#160; <xsl:value-of select="./v3:numerator/@unit"/>&#160;per&#160; <xsl:value-of
																select="./v3:denominator/@value"/>&#160; <xsl:value-of select="./v3:denominator/@unit"/>
														</xsl:for-each>
													</xsl:otherwise>
												</xsl:choose>
											</td>
											<td class="formItem" colSpan="3">
												<table class="formTablePetite" cellSpacing="0" cellPadding="5" width="100%">
													<tbody>
														<tr class="formTable">
															<td class="formTitle" colSpan="4">Conditions Of Use</td>
														</tr>
														<tr class="formTable">
															<td class="formTitle">Use Category</td>
															<td class="formTitle">Precondition Category</td>
															<td class="formTitle">Precondition</td>
															<td class="formTitle">Labeling Section</td>
														</tr>
														<!-- Repeat Each precondition for the indication subject -->
														<!-- PCR 593 Displaying all the preconditions that are specifict to this indication and those that may be in other sections such
															as the Dosage forms and Strengths.
														-->
														<!-- PCR 593 Displaying all the preconditions that are specifict to this indication and those that may be in other sections such
															as the Dosage forms and Strengths.
														-->
														<!-- PCR 606 In order to remove the duplicates each section whose ancestor is anything other than $indicationSectionCode.
															A not (!) in the predicate will not do since a precondition axis can have multiple section tags as ancestors, of which any may be an Indication Section.
														-->
														<xsl:for-each select="./v3:substanceAdministration/v3:precondition">
															<xsl:call-template name="displayConditionsOfUse"> </xsl:call-template>
														</xsl:for-each>
														<xsl:for-each select="//v3:excerpt/v3:highlight/v3:subject/v3:substanceAdministration/v3:precondition">
															<xsl:if test="count(ancestor::v3:section[v3:code/@code=$indicationSectionCode]) = 0">
																<xsl:call-template name="displayConditionsOfUse"> </xsl:call-template>
															</xsl:if>
														</xsl:for-each>
														<xsl:for-each select="./v3:substanceAdministration/v3:componentOf">
															<tr>
																<xsl:attribute name="class">
																	<xsl:choose>
																		<xsl:when test="position() mod 2 = 0">formTableRow</xsl:when>
																		<xsl:otherwise>formTableRowAlt</xsl:otherwise>
																	</xsl:choose>
																</xsl:attribute>
																<td class="formItem">Condition of use</td>
																<td class="formItem">Screening/monitoring test</td>
																<td class="formItem">
																	<xsl:for-each select="./v3:protocol/v3:component">
																		<xsl:value-of select="./v3:monitoringObservation/v3:code/@displayName"/>
																		<xsl:call-template name="printSeperator">
																			<xsl:with-param name="currentPos" select="position()"/>
																			<xsl:with-param name="lastPos" select="last()"/>
																			<xsl:with-param name="lastDelimiter">&#160;and</xsl:with-param>
																		</xsl:call-template>
																	</xsl:for-each>
																</td>
																<td class="formItem">
																	<xsl:variable name="sectionNumberSequence">
																		<xsl:apply-templates mode="sectionNumber" select="$indicationSection"/>
																	</xsl:variable>
																	<a href="#section-{substring($sectionNumberSequence,2)}">
																		<xsl:value-of select="$indicationSection/v3:title"/>
																	</a>
																</td>
															</tr>
														</xsl:for-each>
														<!-- end repeat -->
														<tr>
															<td>&#160;</td>
														</tr>
														<tr class="formTable">
															<td class="formTitle" colSpan="4">Limitations Of Use</td>
														</tr>
														<tr class="formTable">
															<td class="formTitle">Use Category</td>
															<td class="formTitle">Precondition Category</td>
															<td class="formTitle">Precondition</td>
															<td class="formTitle">Labeling Section</td>
														</tr>
														<!-- Repeat Each Limitation of Use -->
														<!-- apply all limitation of use templates for issues within this subject -->
														<!-- now apply all limitation of use templates for issues that are NOT within any indication section or subsection -->
														<!-- PCR 593 Since the limitation of use can have multiple ancestors called section, we process all children limitations of the current context.
														and then all other limitations with specified named ancestors. All possible ancestors other than indication section are used in the predicate.  
														Also made a call to a named template in a loop rather than a matched template-->
														<xsl:for-each select="./v3:substanceAdministration/v3:subjectOf/v3:issue">
															<xsl:call-template name="displayLimitationsOfUse"> </xsl:call-template>
														</xsl:for-each>
														<xsl:for-each select="//v3:excerpt/v3:highlight/v3:subject/v3:substanceAdministration/v3:subjectOf/v3:issue[v3:subject/v3:observationCriterion]">
															<xsl:if test="count(ancestor::v3:section[v3:code/@code=$indicationSectionCode]) = 0">
																<xsl:call-template name="displayLimitationsOfUse"> </xsl:call-template>
															</xsl:if>
														</xsl:for-each>
														<!-- end repeat -->
													</tbody>
												</table>
											</td>
										</tr>
									</xsl:for-each>
									<!--/xsl:for-each-->
									<!-- end repeat -->
								</tbody>
							</table>
						</td>
					</tr>
				</tbody>
			</table>
			<br/>
		</xsl:if>
	</xsl:template>
	<xsl:template mode="indication" match="v3:value[@xsi:type='IVL_PQ']">
		<xsl:choose>
			<xsl:when test="v3:low and v3:high">
				<xsl:value-of select="v3:low/@value"/><xsl:value-of select="v3:low/@unit"/>&#160;to&#160;<xsl:value-of select="v3:high/@value"/><xsl:value-of select="v3:high/@unit"/>
			</xsl:when>
			<xsl:when test="v3:low and not(v3:high)"> &#8805; <xsl:value-of select="v3:low/@value"/><xsl:value-of select="v3:low/@unit"/>
			</xsl:when>
			<xsl:when test="not(v3:low) and v3:high"> &#8804;<xsl:value-of select="v3:high/@value"/><xsl:value-of select="v3:high/@unit"/>
			</xsl:when>
		</xsl:choose>
	</xsl:template>
	<xsl:template mode="indication" match="v3:value[@xsi:type='CE']">
		<xsl:param name="currentNode" select="."/>
		<xsl:value-of select="@displayName"/>
	</xsl:template>
	<xsl:template name="displayConditionsOfUse">
		<tr>
			<xsl:attribute name="class">
				<xsl:choose>
					<xsl:when test="position() mod 2 = 0">formTableRow</xsl:when>
					<xsl:otherwise>formTableRowAlt</xsl:otherwise>
				</xsl:choose>
			</xsl:attribute>
			<xsl:choose>
				<xsl:when test="./v3:observationCriterion">
					<td class="formItem">Condition of use</td>
					<td class="formItem">
						<xsl:value-of select="./v3:observationCriterion/v3:code/@displayName"/>
					</td>
					<td class="formItem">
						<xsl:apply-templates mode="indication" select="./v3:observationCriterion/v3:value"/>
					</td>
				</xsl:when>
				<xsl:when test="./v3:substanceAdministrationCriterion">
					<td class="formItem">Condition of use</td>
					<td class="formItem">Adjunct</td>
					<td class="formItem">
						<xsl:value-of select="./v3:substanceAdministrationCriterion/v3:consumable/v3:administrableMaterial/v3:playingMaterialKind/v3:code/@displayName"/>
					</td>
				</xsl:when>
			</xsl:choose>
			<td class="formItem">
				<!--PCR 593 Instead of using the variable $indicationSection the section number is being uniquely determined. for conditionsl of use.
				-->
				<xsl:variable name="sectionNumberSequence">
					<xsl:apply-templates mode="sectionNumber" select="ancestor::v3:section[parent::v3:component[parent::v3:structuredBody]]"/>
				</xsl:variable>
				<a href="#section-{substring($sectionNumberSequence,2)}">
					<xsl:value-of select="ancestor::v3:section[parent::v3:component[parent::v3:structuredBody]]/v3:title/text()"/>
				</a>
			</td>
		</tr>
	</xsl:template>
	<!-- PCR593 Using a named template instead of a matched template for  v3:issue[v3:subject/v3:observationCriterion] See where it is
	being called from, for more details.-->
	<xsl:template name="displayLimitationsOfUse">
		<tr>
			<xsl:attribute name="class">
				<xsl:choose>
					<xsl:when test="position() mod 2 = 0">formTableRow</xsl:when>
					<xsl:otherwise>formTableRowAlt</xsl:otherwise>
				</xsl:choose>
			</xsl:attribute>
			<td class="formItem">
				<xsl:value-of select="./v3:code/@displayName"/>
			</td>
			<td class="formItem">
				<xsl:for-each select="./v3:subject">
					<xsl:value-of select="./v3:observationCriterion/v3:code/@displayName"/>
					<xsl:call-template name="printSeperator">
						<xsl:with-param name="currentPos" select="position()"/>
						<xsl:with-param name="lastPos" select="last()"/>
						<xsl:with-param name="lastDelimiter">,</xsl:with-param>
					</xsl:call-template>
				</xsl:for-each>
			</td>
			<td class="formItem">
				<xsl:for-each select="./v3:subject">
					<xsl:apply-templates mode="indication" select="./v3:observationCriterion/v3:value"/>
					<xsl:call-template name="printSeperator">
						<xsl:with-param name="currentPos" select="position()"/>
						<xsl:with-param name="lastPos" select="last()"/>
						<xsl:with-param name="lastDelimiter">&#160;and</xsl:with-param>
					</xsl:call-template>
				</xsl:for-each>
			</td>
			<td class="formItem">
				<xsl:variable name="sectionNumberSequence">
					<xsl:apply-templates mode="sectionNumber" select="ancestor::v3:section[parent::v3:component[parent::v3:structuredBody]]"/>
				</xsl:variable>
				<a href="#section-{substring($sectionNumberSequence,2)}">
					<xsl:value-of select="ancestor::v3:section[parent::v3:component[parent::v3:structuredBody]]/v3:title/text()"/>
				</a>
			</td>
		</tr>
	</xsl:template>
	<xsl:template name="PLRInteractions">
		<xsl:if test="count(//v3:issue[v3:subject[v3:substanceAdministrationCriterion]]) > 0 or count(//v3:issue[not(v3:subject) and v3:risk]) > 0">
			<table class="contentTablePetite" cellSpacing="0" cellPadding="3" width="100%">
				<tbody>
					<tr>
						<td class="contentTableTitle">Interactions and Adverse Reactions</td>
					</tr>
					<tr class="formTableRowAlt">
						<td class="formItem">
							<table class="formTablePetite" cellSpacing="0" cellPadding="3" width="100%">
								<tbody>
									<tr>
										<td class="formTitle" colSpan="4">INTERACTIONS</td>
									</tr>
									<tr>
										<td class="formTitle">Contributing Factor</td>
										<td class="formTitle">Type of Consequence</td>
										<td class="formTitle">Consequence</td>
										<td class="formTitle">Labeling Section</td>
									</tr>
									<!-- only select those issues that have the proper interactions code of 'C54708' -->
									<!-- all others will be placed in a table with a title "UN-CODED INTERACTIONS OR ADVERSE REACTIONS" -->
									<xsl:apply-templates mode="interactions" select="//v3:issue[v3:code/@code = 'C54708']"/>
								</tbody>
							</table>
						</td>
					</tr>
					<tr class="formTableRowAlt">
						<td class="formItem">
							<table class="formTablePetite" cellSpacing="0" cellPadding="3" width="100%">
								<tbody>
									<tr>
										<td class="formTitle" colSpan="4">ADVERSE REACTIONS</td>
									</tr>
									<tr>
										<td class="formTitle">Type of Consequence</td>
										<td class="formTitle">Consequence</td>
										<td class="formTitle">Labeling Section</td>
									</tr>
									<!-- only select those issues that have the proper adverse reactions code of 'C41332' -->
									<!-- all others will be placed in a table with a title "UN-CODED INTERACTIONS OR ADVERSE REACTIONS" -->
									<xsl:apply-templates mode="adverseReactions" select="//v3:issue[v3:code/@code = 'C41332']"/>
								</tbody>
							</table>
						</td>
					</tr>
					<xsl:if
						test="(//v3:issue[v3:subject[v3:substanceAdministrationCriterion] and v3:code/@code != 'C54708']) or (//v3:issue[not(./v3:subject) and v3:risk and v3:code/@code != 'C41332'])">
						<tr class="formTableRowAlt">
							<td class="formItem">
								<table class="formTablePetite" cellSpacing="0" cellPadding="3" width="100%">
									<tbody>
										<tr>
											<td class="formTitle" colSpan="4">UN-CODED INTERACTIONS OR ADVERSE REACTIONS</td>
										</tr>
										<tr>
											<td class="formTitle">Contributing Factor</td>
											<td class="formTitle">Type of Consequence</td>
											<td class="formTitle">Consequence</td>
											<td class="formTitle">Labeling Section</td>
										</tr>
										<!-- apply the interaction sections that are improperly coded -->
										<xsl:apply-templates mode="interactions" select="//v3:issue[v3:subject[v3:substanceAdministrationCriterion] and v3:code/@code != 'C54708']"/>
										<!-- apply the adverse reaction sections that are imprperly code -->
										<xsl:apply-templates mode="adverseReactions" select="//v3:issue[not(./v3:subject) and v3:risk and v3:code/@code != 'C41332']">
											<xsl:with-param name="addEmptyTd">true</xsl:with-param>
										</xsl:apply-templates>
									</tbody>
								</table>
							</td>
						</tr>
					</xsl:if>
				</tbody>
			</table>
			<br/>
		</xsl:if>
	</xsl:template>
	<!-- Interactions template -->
	<xsl:template mode="interactions" match="v3:issue[v3:subject[v3:substanceAdministrationCriterion]]">
		<tr>
			<xsl:attribute name="class">
				<xsl:choose>
					<xsl:when test="position() mod 2 = 0">formTableRow</xsl:when>
					<xsl:otherwise>formTableRowAlt</xsl:otherwise>
				</xsl:choose>
			</xsl:attribute>
			<td class="formItem">
				<xsl:for-each select="v3:subject">
					<xsl:value-of select="./v3:substanceAdministrationCriterion/v3:consumable/v3:administrableMaterial/v3:playingMaterialKind/v3:code/@displayName"/>
					<xsl:call-template name="printSeperator">
						<xsl:with-param name="currentPos" select="position()"/>
						<xsl:with-param name="lastPos" select="last()"/>
						<xsl:with-param name="lastDelimiter">&#160;and</xsl:with-param>
					</xsl:call-template>
				</xsl:for-each>
			</td>
			<td class="formItem">
				<xsl:for-each select="v3:risk">
					<xsl:value-of select="v3:consequenceObservation/v3:code/@displayName"/>
					<xsl:call-template name="printSeperator">
						<xsl:with-param name="currentPos" select="position()"/>
						<xsl:with-param name="lastPos" select="last()"/>
						<xsl:with-param name="lastDelimiter">,</xsl:with-param>
					</xsl:call-template>
				</xsl:for-each>
			</td>
			<td class="formItem">
				<xsl:for-each select="v3:risk">
					<xsl:value-of select="v3:consequenceObservation/v3:value/@displayName"/>
					<xsl:call-template name="printSeperator">
						<xsl:with-param name="currentPos" select="position()"/>
						<xsl:with-param name="lastPos" select="last()"/>
						<xsl:with-param name="lastDelimiter">&#160;and</xsl:with-param>
					</xsl:call-template>
				</xsl:for-each>
			</td>
			<td class="formItem">
				<xsl:variable name="sectionNumberSequence">
					<xsl:apply-templates mode="sectionNumber" select="ancestor::v3:section[parent::v3:component[parent::v3:structuredBody]]"/>
				</xsl:variable>
				<a href="#section-{substring($sectionNumberSequence,2)}">
					<xsl:value-of select="ancestor::v3:section[parent::v3:component[parent::v3:structuredBody]]/v3:title"/>
				</a>
			</td>
		</tr>
	</xsl:template>
	<!-- Adverse Reactions template -->
	<xsl:template mode="adverseReactions" match="v3:issue[not(./v3:subject) and v3:risk]">
		<xsl:param name="addEmptyTd">false</xsl:param>
		<tr>
			<xsl:attribute name="class">
				<xsl:choose>
					<xsl:when test="position() mod 2 = 0">formTableRow</xsl:when>
					<xsl:otherwise>formTableRowAlt</xsl:otherwise>
				</xsl:choose>
			</xsl:attribute>
			<xsl:if test="$addEmptyTd = 'true'">
				<td>&#160;</td>
			</xsl:if>
			<td class="formItem">
				<xsl:for-each select="v3:risk">
					<xsl:value-of select="./v3:consequenceObservation/v3:code/@displayName"/>
					<xsl:call-template name="printSeperator">
						<xsl:with-param name="currentPos" select="position()"/>
						<xsl:with-param name="lastPos" select="last()"/>
						<xsl:with-param name="lastDelimiter">,</xsl:with-param>
					</xsl:call-template>
				</xsl:for-each>
			</td>
			<td class="formItem">
				<xsl:for-each select="v3:risk">
					<xsl:value-of select="v3:consequenceObservation/v3:value/@displayName"/>
					<xsl:call-template name="printSeperator">
						<xsl:with-param name="currentPos" select="position()"/>
						<xsl:with-param name="lastPos" select="last()"/>
						<xsl:with-param name="lastDelimiter">&#160;and</xsl:with-param>
					</xsl:call-template>
				</xsl:for-each>
			</td>
			<td class="formItem">
				<xsl:variable name="sectionNumberSequence">
					<xsl:apply-templates mode="sectionNumber" select="ancestor::v3:section[parent::v3:component[parent::v3:structuredBody]]"/>
				</xsl:variable>
				<a href="#section-{substring($sectionNumberSequence,2)}">
					<xsl:value-of select="ancestor::v3:section[parent::v3:component[parent::v3:structuredBody]]/v3:title"/>
				</a>
			</td>
		</tr>
	</xsl:template>
	<xsl:template name="PharmacologicalClass">
		<xsl:if test="count(//v3:asSpecializedKind) > 0">
			<table class="contentTable" cellSpacing="0" cellPadding="3" width="100%">
				<tbody>
					<tr>
						<td class="contentTableTitle">Established Pharmacological Class</td>
					</tr>
					<tr class="formTableRowAlt">
						<td class="formItem">
							<table class="formTable" cellSpacing="0" cellPadding="3" width="100%">
								<tbody>
									<tr>
										<td class="formTitle" width="30%">Substance</td>
										<td class="formTitle" width="70%">Pharmacological Class</td>
									</tr>
									<xsl:for-each select="//v3:activeIngredient">
										<tr>
											<xsl:attribute name="class">
												<xsl:choose>
													<xsl:when test="position() mod 2 = 0">formTableRow</xsl:when>
													<xsl:otherwise>formTableRowAlt</xsl:otherwise>
												</xsl:choose>
											</xsl:attribute>
											<td class="formItem">
												<strong>
													<xsl:value-of select="./v3:activeIngredientSubstance/v3:name"/>
												</strong>
											</td>
											<td class="formItem">
												<xsl:for-each select="./v3:activeIngredientSubstance/v3:asSpecializedKind">
													<xsl:value-of select="./v3:generalizedPharmaceuticalClass/v3:code/@displayName"/>
													<xsl:call-template name="printSeperator">
														<xsl:with-param name="currentPos" select="position()"/>
														<xsl:with-param name="lastPos" select="last()"/>
														<xsl:with-param name="lastDelimiter">&#160;and</xsl:with-param>
													</xsl:call-template>
												</xsl:for-each>
											</td>
										</tr>
									</xsl:for-each>
								</tbody>
							</table>
						</td>
					</tr>
				</tbody>
			</table>
		</xsl:if>
	</xsl:template>
</xsl:transform>
