"""
Servicio DIAN RADIAN - Firma XML y envío de eventos de cesión
"""
import base64
import hashlib
from datetime import datetime
import zeep
from lxml import etree
from signxml import XMLSigner, methods
from cryptography.hazmat.primitives.serialization import pkcs12
from cryptography.hazmat.backends import default_backend

from config import settings


class DianRadianService:
    """
    Servicio principal para interactuar con RADIAN de la DIAN.
    Maneja firma de XMLs y envío de eventos de cesión.
    """

    def __init__(self):
        self.ambiente = settings.DIAN_AMBIENTE
        self.nit_empresa = settings.NIT_EMPRESA
        self._cargar_certificado()

    def _cargar_certificado(self):
        """Carga el certificado digital .p12 para firma de XMLs"""
        try:
            with open(settings.CERT_PATH, "rb") as f:
                p12_data = f.read()
            self.private_key, self.certificate, self.chain = pkcs12.load_key_and_certificates(
                p12_data,
                settings.CERT_PASSWORD.encode(),
                backend=default_backend()
            )
        except FileNotFoundError:
            # En ambiente de desarrollo sin certificado
            self.private_key = None
            self.certificate = None
            self.chain = None
            print("AVISO: Certificado no encontrado - modo desarrollo sin firma")

    def generar_cude(self, numero_cesion: str, fecha: str, valor: float,
                     cedente_nit: str, cesionario_nit: str, cufe_factura: str) -> str:
        """
        Genera el CUDE (Código Único Documento Electrónico) para el evento de cesión.
        Fórmula DIAN: SHA-384 de la concatenación de campos
        """
        cadena = f"{numero_cesion}{fecha}{str(valor)}{cedente_nit}{cesionario_nit}{cufe_factura}{self.ambiente}{settings.CLAVE_TECNICA_DIAN}"
        cude = hashlib.sha384(cadena.encode()).hexdigest()
        return cude

    def construir_xml_cesion(
        self,
        cufe_factura: str,
        numero_cesion: str,
        cedente_nit: str,
        cedente_nombre: str,
        cesionario_nit: str,
        cesionario_nombre: str,
        deudor_nit: str,
        deudor_nombre: str,
        valor_cesion: float,
        fecha_cesion: datetime
    ) -> str:
        """
        Construye el XML del evento de cesión según especificaciones DIAN RADIAN.
        Evento 037 = Endoso en Propiedad (Cesión)
        """
        fecha_str = fecha_cesion.strftime("%Y-%m-%dT%H:%M:%S")
        fecha_solo = fecha_cesion.strftime("%Y-%m-%d")

        cude = self.generar_cude(
            numero_cesion, fecha_str, valor_cesion,
            cedente_nit, cesionario_nit, cufe_factura
        )

        xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<ApplicationResponse
    xmlns="urn:oasis:names:specification:ubl:schema:xsd:ApplicationResponse-2"
    xmlns:cac="urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2"
    xmlns:cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2"
    xmlns:ds="http://www.w3.org/2000/09/xmldsig#"
    xmlns:ext="urn:oasis:names:specification:ubl:schema:xsd:CommonExtensionComponents-2"
    xmlns:sts="dian:gov:co:facturaelectronica:Structures-2-1"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">

    <ext:UBLExtensions>
        <ext:UBLExtension>
            <ext:ExtensionContent>
                <sts:DianExtensions>
                    <sts:InvoiceControl>
                        <sts:InvoiceAuthorization>{numero_cesion}</sts:InvoiceAuthorization>
                    </sts:InvoiceControl>
                    <sts:SoftwareProvider>
                        <sts:ProviderID schemeAgencyID="195" schemeAgencyName="CO, DIAN (Dirección de Impuestos y Aduanas Nacionales)">{self.nit_empresa}</sts:ProviderID>
                        <sts:SoftwareID schemeAgencyID="195" schemeAgencyName="CO, DIAN">{settings.SOFTWARE_ID}</sts:SoftwareID>
                    </sts:SoftwareProvider>
                    <sts:SoftwareSecurityCode schemeAgencyID="195" schemeAgencyName="CO, DIAN">{cude}</sts:SoftwareSecurityCode>
                </sts:DianExtensions>
            </ext:ExtensionContent>
        </ext:UBLExtension>
        <!-- Aquí va la firma digital XMLDSig -->
        <ext:UBLExtension>
            <ext:ExtensionContent/>
        </ext:UBLExtension>
    </ext:UBLExtensions>

    <cbc:UBLVersionID>UBL 2.1</cbc:UBLVersionID>
    <cbc:CustomizationID>1</cbc:CustomizationID>
    <cbc:ProfileID>DIAN 2.1: Evento Título Valor</cbc:ProfileID>
    <cbc:ProfileExecutionID>{self.ambiente}</cbc:ProfileExecutionID>
    <cbc:ID>{numero_cesion}</cbc:ID>
    <cbc:UUID schemeID="{self.ambiente}" schemeName="CUDE-SHA384">{cude}</cbc:UUID>
    <cbc:IssueDate>{fecha_solo}</cbc:IssueDate>
    <cbc:IssueTime>{fecha_cesion.strftime("%H:%M:%S")}</cbc:IssueTime>
    <cbc:ResponseCode listID="EventStatusCode">037</cbc:ResponseCode>
    <cbc:Description>Endoso en Propiedad</cbc:Description>
    <cbc:Note>Cesión de factura electrónica como título valor</cbc:Note>

    <!-- Emisor del evento (Cedente) -->
    <cac:SenderParty>
        <cac:PartyTaxScheme>
            <cbc:RegistrationName>{cedente_nombre}</cbc:RegistrationName>
            <cbc:CompanyID schemeAgencyID="195" schemeAgencyName="CO, DIAN"
                schemeID="4" schemeName="31">{cedente_nit}</cbc:CompanyID>
            <cac:TaxScheme>
                <cbc:ID>01</cbc:ID>
                <cbc:Name>IVA</cbc:Name>
            </cac:TaxScheme>
        </cac:PartyTaxScheme>
    </cac:SenderParty>

    <!-- Receptor del evento (DIAN) -->
    <cac:ReceiverParty>
        <cac:PartyTaxScheme>
            <cbc:RegistrationName>DIAN</cbc:RegistrationName>
            <cbc:CompanyID schemeAgencyID="195" schemeAgencyName="CO, DIAN"
                schemeID="4" schemeName="31">800197268</cbc:CompanyID>
            <cac:TaxScheme>
                <cbc:ID>01</cbc:ID>
                <cbc:Name>IVA</cbc:Name>
            </cac:TaxScheme>
        </cac:PartyTaxScheme>
    </cac:ReceiverParty>

    <!-- Documento referenciado (Factura original) -->
    <cac:DocumentResponse>
        <cac:Response>
            <cbc:ResponseCode>037</cbc:ResponseCode>
            <cbc:Description>Endoso en Propiedad</cbc:Description>
        </cac:Response>
        <cac:DocumentReference>
            <cbc:ID>{cufe_factura[:10]}</cbc:ID>
            <cbc:UUID>{cufe_factura}</cbc:UUID>
            <cbc:DocumentTypeCode>01</cbc:DocumentTypeCode>
        </cac:DocumentReference>

        <!-- Deudor -->
        <cac:IssuerParty>
            <cac:PartyTaxScheme>
                <cbc:RegistrationName>{deudor_nombre}</cbc:RegistrationName>
                <cbc:CompanyID schemeAgencyID="195" schemeName="31">{deudor_nit}</cbc:CompanyID>
                <cac:TaxScheme>
                    <cbc:ID>01</cbc:ID>
                </cac:TaxScheme>
            </cac:PartyTaxScheme>
        </cac:IssuerParty>

        <!-- Cesionario (nuevo tenedor) -->
        <cac:RecipientParty>
            <cac:PartyTaxScheme>
                <cbc:RegistrationName>{cesionario_nombre}</cbc:RegistrationName>
                <cbc:CompanyID schemeAgencyID="195" schemeName="31">{cesionario_nit}</cbc:CompanyID>
                <cac:TaxScheme>
                    <cbc:ID>01</cbc:ID>
                </cac:TaxScheme>
            </cac:PartyTaxScheme>
        </cac:RecipientParty>

        <!-- Monto cedido -->
        <cac:LineResponse>
            <cac:Response>
                <cbc:ResponseCode>037</cbc:ResponseCode>
                <cbc:Description>Valor cedido: {valor_cesion}</cbc:Description>
            </cac:Response>
            <cac:LineReference>
                <cbc:LineID>1</cbc:LineID>
                <cbc:UUID>{cufe_factura}</cbc:UUID>
                <cbc:DocumentTypeCode>01</cbc:DocumentTypeCode>
                <cac:DocumentReference>
                    <cbc:ID>1</cbc:ID>
                    <cbc:Amount currencyID="COP">{valor_cesion}</cbc:Amount>
                </cac:DocumentReference>
            </cac:LineReference>
        </cac:LineResponse>
    </cac:DocumentResponse>
</ApplicationResponse>"""
        return xml, cude

    def firmar_xml(self, xml_string: str) -> str:
        """
        Firma digitalmente el XML usando el certificado .p12
        Implementa XMLDSig según requerimientos DIAN
        """
        if not self.private_key:
            print("AVISO: Sin certificado - XML sin firma (solo desarrollo)")
            return xml_string

        root = etree.fromstring(xml_string.encode())
        signer = XMLSigner(
            method=methods.enveloped,
            signature_algorithm="rsa-sha256",
            digest_algorithm="sha256",
        )
        signed_root = signer.sign(
            root,
            key=self.private_key,
            cert=self.certificate,
        )
        return etree.tostring(signed_root, pretty_print=True).decode()

    def enviar_evento_radian(self, xml_firmado: str) -> dict:
        """
        Envía el evento de cesión al webservice RADIAN de la DIAN.
        Método: SendEventUpdateStatus
        """
        try:
            # Codificar XML en base64
            xml_b64 = base64.b64encode(xml_firmado.encode()).decode()

            # Conectar al webservice SOAP de la DIAN
            client = zeep.Client(wsdl=settings.DIAN_WS_RADIAN_WSDL)

            # Llamar al método de envío
            response = client.service.SendEventUpdateStatus(
                fileName=f"evento_cesion_{datetime.now().strftime('%Y%m%d%H%M%S')}.xml",
                contentFile=xml_b64
            )

            return {
                "exitoso": True,
                "codigo_respuesta": response.get("ErrorMessageList", {}).get("CodeErrorMessage", ""),
                "descripcion": response.get("ErrorMessageList", {}).get("TechnicalDescription", "Evento procesado"),
                "respuesta_completa": response
            }

        except Exception as e:
            return {
                "exitoso": False,
                "error": str(e),
                "descripcion": "Error al conectar con DIAN RADIAN"
            }

    def consultar_estado_evento(self, cude: str) -> dict:
        """Consulta el estado de un evento en RADIAN por su CUDE"""
        try:
            client = zeep.Client(wsdl=settings.DIAN_WS_RADIAN_WSDL)
            response = client.service.GetStatusEvent(trackId=cude)
            return {
                "exitoso": True,
                "estado": response.get("StatusCode", ""),
                "descripcion": response.get("StatusDescription", ""),
                "fecha_procesamiento": response.get("ProcessingDate", "")
            }
        except Exception as e:
            return {"exitoso": False, "error": str(e)}


# Instancia global
dian_service = DianRadianService()
