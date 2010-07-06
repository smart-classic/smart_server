<xsl:stylesheet 
xmlns:xsl="http://www.w3.org/1999/XSL/Transform" 
xmlns:xs="http://www.w3.org/2001/XMLSchema"
xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
xmlns:med="http://smartplatforms.org/med#" 
xmlns:dcterms="http://purl.org/dc/terms/"
xmlns:dc="http://purl.org/dc/elements/1.1/"
xmlns:rxcui="http://link.informatics.stonybrook.edu/rxnorm/RXCUI/"
xmlns:ccr='urn:astm-org:CCR'
exclude-result-prefixes="xs"
version="1.0">
<xsl:output method="xml" indent="yes"/>

<xsl:variable name="smallcase" select="'abcdefghijklmnopqrstuvwxyz '" />
<xsl:variable name="uppercase" select="'ABCDEFGHIJKLMNOPQRSTUVWXYZ_'" />

<xsl:template match="/">
<rdf:RDF>
<xsl:apply-templates select=".//ccr:Medication"/>
</rdf:RDF>
</xsl:template>

<xsl:template match="ccr:Medication">
<rdf:Description>
  <xsl:variable name="medid" select="@id" />
<xsl:variable name="dose" select='normalize-space(.//ccr:Dose/ccr:Value)'/>
<xsl:variable name="doseu" select='translate(normalize-space(.//ccr:Dose/ccr:Units), $uppercase, $smallcase)'/>
<xsl:variable name="route" select='translate(normalize-space(.//ccr:Route/ccr:Text), $uppercase, $smallcase)'/>
<xsl:variable name="freq" select='normalize-space(.//ccr:Frequency/ccr:Value)'/>
<xsl:variable name="name" select='normalize-space(.//ccr:ProductName/ccr:Text)'/>
<xsl:variable name="strength" select='normalize-space(.//ccr:Strength/ccr:Value)'/>
<xsl:variable name="strengthu" select='translate(normalize-space(.//ccr:Strength/ccr:Units), $uppercase, $smallcase)'/>
<xsl:variable name="form" select='translate(normalize-space(.//ccr:Product/ccr:Form/ccr:Text), $uppercase, $smallcase)'/>
<xsl:variable name="cui" select="normalize-space(.//ccr:ProductName/ccr:Code/ccr:Value[../ccr:CodingSystem='RxNorm'])"/>


  <xsl:choose>
  <xsl:when test="$medid">
  <xsl:attribute name="rdf:about"><xsl:value-of select="@id"/></xsl:attribute>
  </xsl:when>
  </xsl:choose>


  <rdf:type><xsl:attribute name="rdf:resource">http://smartplatforms.org/med#medication</xsl:attribute></rdf:type>

  <xsl:choose><xsl:when test="$cui">
  	    <med:drug><xsl:attribute name="rdf:resource">http://link.informatics.stonybrook.edu/rxnorm/RXCUI/<xsl:value-of select="$cui"/></xsl:attribute></med:drug>
  </xsl:when></xsl:choose>



  <xsl:choose><xsl:when test="$dose">
  	    <med:dose><xsl:value-of select="$dose"/></med:dose>
  </xsl:when></xsl:choose>
  <xsl:choose><xsl:when test="$doseu">
  	    <med:doseUnits><xsl:attribute name="rdf:resource">http://smartplatforms.org/med#<xsl:value-of select="$doseu"/></xsl:attribute></med:doseUnits>
  </xsl:when></xsl:choose>
  <xsl:choose><xsl:when test="$route">
  	    <med:route><xsl:attribute name="rdf:resource">http://smartplatforms.org/med#<xsl:value-of select="$route"/></xsl:attribute></med:route>
  </xsl:when></xsl:choose>
  <xsl:choose><xsl:when test="$freq">
  	    <med:frequency><xsl:value-of select="$freq"/></med:frequency>
  </xsl:when></xsl:choose>

  <xsl:variable name="start_date" select=".//ccr:ExactDateTime[../ccr:Type/ccr:Text='Start date']" />
  <xsl:choose>
  <xsl:when test="$start_date">
	<med:startDate>
		<rdf:Description>
			<dc:date><xsl:value-of select="$start_date" /></dc:date>
		</rdf:Description>
	</med:startDate>
  </xsl:when>
  </xsl:choose>

  <xsl:variable name="end_date" select=".//ccr:ExactDateTime[../ccr:Type/ccr:Text='Stop date']" />
  <xsl:choose>
  <xsl:when test="$end_date">
	<med:endDate>
		<rdf:Description>
			<dc:date><xsl:value-of select="$end_date" /></dc:date>
		</rdf:Description>
	</med:endDate>
  </xsl:when>
  </xsl:choose>


  <xsl:choose><xsl:when test="$name">
  	    <dcterms:title><xsl:value-of select="$name"/></dcterms:title>
  </xsl:when></xsl:choose>
  <xsl:choose><xsl:when test="$strength">
  	    <med:strength><xsl:value-of select="$strength"/></med:strength>
  </xsl:when></xsl:choose>
  <xsl:choose><xsl:when test="$strengthu">
  	    <med:strengthUnits><xsl:attribute name="rdf:resource">http://smartplatforms.org/med#<xsl:value-of select="$strengthu"/></xsl:attribute></med:strengthUnits>
  </xsl:when></xsl:choose>
  <xsl:choose><xsl:when test="form">
  	    <med:form><xsl:attribute name="rdf:resource">http://smartplatforms.org/med#<xsl:value-of select="$form"/></xsl:attribute></med:form>
  </xsl:when></xsl:choose>

</rdf:Description>

	    
</xsl:template>

</xsl:stylesheet>

