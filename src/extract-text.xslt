<xsl:stylesheet version="1.0"
 xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
 <xsl:output method="text"/>
 <xsl:strip-space elements="*"/>

 <xsl:template match="artigos/artigo//text()">
  <xsl:value-of select="concat(.,'&#xA;')"/>
 </xsl:template>
 <xsl:template match="text()"/>
</xsl:stylesheet>
