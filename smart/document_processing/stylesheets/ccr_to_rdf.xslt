<xsl:stylesheet 
xmlns:xsl="http://www.w3.org/1999/XSL/Transform" 
xmlns:xs="http://www.w3.org/2001/XMLSchema"
xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
xmlns:med="http://smartplatforms.org/med#" 
xmlns:dcterms="http://purl.org/dc/terms/"
xmlns:rxcui="http://link.informatics.stonybrook.edu/rxnorm/RXCUI/"
exclude-result-prefixes="xs"
version="1.0">
<xsl:output method="xml" indent="yes"/>

<xsl:variable name="smallcase" select="'abcdefghijklmnopqrstuvwxyz'" />
<xsl:variable name="uppercase" select="'ABCDEFGHIJKLMNOPQRSTUVWXYZ'" />

<xsl:template match="/">
<rdf:RDF>
<xsl:apply-templates />
</rdf:RDF>
</xsl:template>

<xsl:template match="//Medication">
<xsl:variable name="cui" select="normalize-space(.//ProductName/Code/Value[../CodingSystem='RxNorm'])"/>
<rdf:Description>
  <xsl:variable name="medid" select="@id" />
  <xsl:choose>
  <xsl:when test="$medid">
  <xsl:attribute name="rdf:about"><xsl:value-of select="@id"/></xsl:attribute>
  </xsl:when>
  </xsl:choose>
  	    <rdf:type><xsl:attribute name="rdf:resource">http://smartplatforms.org/med#medication</xsl:attribute></rdf:type>
  	    <med:drug><xsl:attribute name="rdf:resource">http://link.informatics.stonybrook.edu/rxnorm/RXCUI/<xsl:value-of select="$cui"/></xsl:attribute></med:drug>
  	    <med:dose><xsl:value-of select='normalize-space(.//Dose/Value)'/></med:dose>
  	    <med:doseUnits><xsl:attribute name="rdf:resource">http://smartplatforms.org/med#<xsl:value-of select='translate(normalize-space(.//Dose/Units), $uppercase, $smallcase)'/></xsl:attribute></med:doseUnits>
  	    <med:route><xsl:attribute name="rdf:resource">http://smartplatforms.org/med#<xsl:value-of select='translate(normalize-space(.//Route/Text), $uppercase, $smallcase)'/></xsl:attribute></med:route>
  	    <med:frequency><xsl:value-of select='normalize-space(.//Frequency/Value)'/></med:frequency>
</rdf:Description>
<rdf:Description>
<xsl:attribute name="rdf:about">http://link.informatics.stonybrook.edu/rxnorm/RXCUI/<xsl:value-of select="$cui"/></xsl:attribute>
  	    <dcterms:title><xsl:value-of select='normalize-space(.//ProductName/Text)'/></dcterms:title>
  	    <med:strength><xsl:value-of select='normalize-space(.//Strength/Value)'/></med:strength>
  	    <med:strengthUnits><xsl:attribute name="rdf:resource">http://smartplatforms.org/med#<xsl:value-of select='translate(normalize-space(.//Strength/Units), $uppercase, $smallcase)'/></xsl:attribute></med:strengthUnits>
  	    <med:form><xsl:attribute name="rdf:resource">http://smartplatforms.org/med#<xsl:value-of select='translate(normalize-space(.//Product/Form/Text), $uppercase, $smallcase)'/></xsl:attribute></med:form>
</rdf:Description>
</xsl:template>

</xsl:stylesheet>

