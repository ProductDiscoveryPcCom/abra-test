"""
Email Report Module
Envía informes de tendencias por email usando Mailgun

Configuración requerida en secrets.toml:
    MAILGUN_API_KEY = "key-xxxxx"
    MAILGUN_DOMAIN = "mg.tudominio.com"
    MAILGUN_FROM_EMAIL = "reports@mg.tudominio.com"
    MAILGUN_FROM_NAME = "Abra Trend Hunter"
"""

import base64
from datetime import datetime
from typing import Optional, Dict, Any, List
import requests
import streamlit as st


class EmailReportService:
    """Servicio para enviar informes por email via Mailgun"""
    
    BASE_URL = "https://api.mailgun.net/v3"
    # Para EU: "https://api.eu.mailgun.net/v3"
    
    def __init__(
        self, 
        api_key: str, 
        domain: str,
        from_email: str, 
        from_name: str = "Abra Trend Hunter",
        region: str = "US"  # "US" o "EU"
    ):
        """
        Inicializa el servicio de email.
        
        Args:
            api_key: API Key de Mailgun
            domain: Dominio configurado en Mailgun (ej: mg.tudominio.com)
            from_email: Email del remitente
            from_name: Nombre del remitente
            region: "US" o "EU" (cambia el endpoint)
        """
        self.api_key = api_key
        self.domain = domain
        self.from_email = from_email
        self.from_name = from_name
        self.base_url = "https://api.eu.mailgun.net/v3" if region == "EU" else "https://api.mailgun.net/v3"
        self._last_error = ""
    
    def test_connection(self) -> tuple[bool, str]:
        """Prueba la conexión con Mailgun"""
        try:
            # Verificar dominio
            response = requests.get(
                f"{self.base_url}/domains/{self.domain}",
                auth=("api", self.api_key),
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                state = data.get("domain", {}).get("state", "unknown")
                return True, f"Conectado (dominio: {state})"
            elif response.status_code == 401:
                return False, "API Key inválida"
            elif response.status_code == 404:
                return False, f"Dominio '{self.domain}' no encontrado"
            else:
                return False, f"Error HTTP {response.status_code}"
                
        except requests.exceptions.Timeout:
            return False, "Timeout de conexión"
        except Exception as e:
            return False, f"Error: {str(e)[:50]}"
    
    def send_report(
        self,
        to_email: str,
        keyword: str,
        pdf_bytes: bytes,
        html_summary: str = "",
        include_pdf: bool = True,
        cc_emails: List[str] = None
    ) -> Dict[str, Any]:
        """
        Envía un informe de tendencia por email.
        
        Args:
            to_email: Email del destinatario
            keyword: Keyword analizado (para el asunto)
            pdf_bytes: Bytes del PDF generado
            html_summary: Resumen HTML para el cuerpo del email
            include_pdf: Si True, adjunta el PDF
            cc_emails: Lista de emails en copia
            
        Returns:
            Dict con resultado: {"success": bool, "message": str}
        """
        try:
            # Crear el email
            subject = f"📊 Informe de Tendencia: {keyword} - {datetime.now().strftime('%d/%m/%Y')}"
            
            # HTML del email
            html_content = self._build_email_html(keyword, html_summary)
            
            # Datos del formulario
            data = {
                "from": f"{self.from_name} <{self.from_email}>",
                "to": to_email,
                "subject": subject,
                "html": html_content
            }
            
            # Añadir CC si existen
            if cc_emails:
                data["cc"] = ", ".join(cc_emails)
            
            # Preparar archivos adjuntos
            files = []
            if include_pdf and pdf_bytes:
                filename = f"trend_report_{keyword.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.pdf"
                files.append(("attachment", (filename, pdf_bytes, "application/pdf")))
            
            # Enviar
            response = requests.post(
                f"{self.base_url}/{self.domain}/messages",
                auth=("api", self.api_key),
                data=data,
                files=files if files else None,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "success": True,
                    "message": f"Email enviado correctamente a {to_email}",
                    "id": result.get("id", ""),
                    "status_code": response.status_code
                }
            elif response.status_code == 401:
                self._last_error = "API Key inválida"
                return {"success": False, "message": self._last_error}
            elif response.status_code == 400:
                error_msg = response.json().get("message", "Solicitud inválida")
                self._last_error = error_msg
                return {"success": False, "message": error_msg}
            else:
                self._last_error = f"Error HTTP {response.status_code}"
                return {"success": False, "message": self._last_error}
                
        except requests.exceptions.Timeout:
            return {"success": False, "message": "Timeout enviando email"}
        except Exception as e:
            self._last_error = str(e)
            return {"success": False, "message": f"Error: {str(e)[:100]}"}
    
    def _build_email_html(self, keyword: str, summary: str = "") -> str:
        """
        Construye el HTML del email.
        """
        date_str = datetime.now().strftime("%d de %B de %Y")
        
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
             background-color: #f5f5f5; margin: 0; padding: 20px;">
    
    <div style="max-width: 600px; margin: 0 auto; background: white; 
                border-radius: 12px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
        
        <!-- Header -->
        <div style="background: linear-gradient(135deg, #6366F1, #8B5CF6); 
                    padding: 30px; text-align: center;">
            <h1 style="color: white; margin: 0; font-size: 24px;">
                📊 Informe de Tendencia
            </h1>
            <p style="color: rgba(255,255,255,0.9); margin: 10px 0 0 0; font-size: 18px;">
                <strong>{keyword}</strong>
            </p>
        </div>
        
        <!-- Body -->
        <div style="padding: 30px;">
            <p style="color: #4B5563; font-size: 14px; margin-bottom: 20px;">
                Generado el {date_str}
            </p>
            
            {f'<div style="background: #F3F4F6; padding: 20px; border-radius: 8px; margin-bottom: 20px;">{summary}</div>' if summary else ''}
            
            <div style="background: #EEF2FF; border-left: 4px solid #6366F1; 
                        padding: 15px; border-radius: 0 8px 8px 0; margin-bottom: 20px;">
                <p style="margin: 0; color: #4338CA; font-size: 14px;">
                    📎 El informe PDF completo está adjunto a este email.
                </p>
            </div>
            
            <p style="color: #6B7280; font-size: 13px; margin-top: 30px;">
                Este informe fue generado automáticamente por 
                <strong>Abra Trend Hunter</strong> - 
                Tu herramienta de inteligencia competitiva.
            </p>
        </div>
        
        <!-- Footer -->
        <div style="background: #F9FAFB; padding: 20px; text-align: center; 
                    border-top: 1px solid #E5E7EB;">
            <p style="color: #9CA3AF; font-size: 12px; margin: 0;">
                © {datetime.now().year} Abra Trend Hunter | PCComponentes
            </p>
        </div>
        
    </div>
</body>
</html>
"""
        return html
    
    def send_alert(
        self,
        to_email: str,
        keyword: str,
        alert_type: str,
        alert_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Envía una alerta de tendencia (sin PDF adjunto).
        
        Args:
            to_email: Email del destinatario
            keyword: Keyword que disparó la alerta
            alert_type: Tipo de alerta ("spike", "drop", "new_trend", etc.)
            alert_data: Datos adicionales de la alerta
            
        Returns:
            Dict con resultado
        """
        try:
            alert_icons = {
                "spike": "🚀",
                "drop": "📉",
                "new_trend": "✨",
                "competitor": "⚠️",
                "opportunity": "💡"
            }
            icon = alert_icons.get(alert_type, "📊")
            
            subject = f"{icon} Alerta de Tendencia: {keyword}"
            html_content = self._build_alert_html(keyword, alert_type, alert_data)
            
            data = {
                "from": f"{self.from_name} <{self.from_email}>",
                "to": to_email,
                "subject": subject,
                "html": html_content
            }
            
            response = requests.post(
                f"{self.base_url}/{self.domain}/messages",
                auth=("api", self.api_key),
                data=data,
                timeout=30
            )
            
            if response.status_code == 200:
                return {"success": True, "message": "Alerta enviada"}
            else:
                return {"success": False, "message": f"Error HTTP {response.status_code}"}
                
        except Exception as e:
            return {"success": False, "message": str(e)}
    
    def _build_alert_html(
        self, 
        keyword: str, 
        alert_type: str, 
        data: Dict[str, Any]
    ) -> str:
        """Construye HTML para alertas"""
        
        alert_colors = {
            "spike": "#10B981",
            "drop": "#EF4444",
            "new_trend": "#8B5CF6",
            "competitor": "#F59E0B",
            "opportunity": "#3B82F6"
        }
        
        alert_titles = {
            "spike": "📈 Subida detectada",
            "drop": "📉 Bajada detectada",
            "new_trend": "✨ Nueva tendencia",
            "competitor": "⚠️ Movimiento de competencia",
            "opportunity": "💡 Oportunidad detectada"
        }
        
        color = alert_colors.get(alert_type, "#6366F1")
        title = alert_titles.get(alert_type, "📊 Alerta")
        
        change = data.get("change", 0)
        current = data.get("current_value", 0)
        details = data.get("details", "")
        
        return f"""
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="font-family: -apple-system, BlinkMacSystemFont, sans-serif; 
             background: #f5f5f5; padding: 20px;">
    <div style="max-width: 500px; margin: 0 auto; background: white; 
                border-radius: 12px; overflow: hidden;">
        
        <div style="background: {color}; padding: 25px; text-align: center;">
            <h1 style="color: white; margin: 0; font-size: 20px;">{title}</h1>
            <p style="color: rgba(255,255,255,0.9); margin: 8px 0 0; font-size: 16px;">
                <strong>{keyword}</strong>
            </p>
        </div>
        
        <div style="padding: 25px;">
            <div style="display: flex; justify-content: space-around; 
                        margin-bottom: 20px; text-align: center;">
                <div>
                    <p style="color: #9CA3AF; font-size: 12px; margin: 0;">Cambio</p>
                    <p style="color: {color}; font-size: 24px; font-weight: bold; margin: 5px 0;">
                        {change:+.1f}%
                    </p>
                </div>
                <div>
                    <p style="color: #9CA3AF; font-size: 12px; margin: 0;">Valor actual</p>
                    <p style="color: #1F2937; font-size: 24px; font-weight: bold; margin: 5px 0;">
                        {current}/100
                    </p>
                </div>
            </div>
            
            {f'<p style="color: #4B5563; font-size: 14px; background: #F3F4F6; padding: 15px; border-radius: 8px;">{details}</p>' if details else ''}
            
            <p style="color: #9CA3AF; font-size: 12px; margin-top: 20px; text-align: center;">
                {datetime.now().strftime("%d/%m/%Y %H:%M")} | Abra Trend Hunter
            </p>
        </div>
    </div>
</body>
</html>
"""
    
    def send_batch(
        self,
        to_emails: List[str],
        keyword: str,
        pdf_bytes: bytes,
        html_summary: str = ""
    ) -> Dict[str, Any]:
        """
        Envía el mismo informe a múltiples destinatarios.
        
        Mailgun permite hasta 1000 destinatarios por llamada.
        
        Args:
            to_emails: Lista de emails destinatarios
            keyword: Keyword analizado
            pdf_bytes: Bytes del PDF
            html_summary: Resumen HTML
            
        Returns:
            Dict con resultado
        """
        try:
            subject = f"📊 Informe de Tendencia: {keyword} - {datetime.now().strftime('%d/%m/%Y')}"
            html_content = self._build_email_html(keyword, html_summary)
            
            # Mailgun acepta múltiples "to" separados por coma
            data = {
                "from": f"{self.from_name} <{self.from_email}>",
                "to": ", ".join(to_emails),
                "subject": subject,
                "html": html_content
            }
            
            files = []
            if pdf_bytes:
                filename = f"trend_report_{keyword.replace(' ', '_')}.pdf"
                files.append(("attachment", (filename, pdf_bytes, "application/pdf")))
            
            response = requests.post(
                f"{self.base_url}/{self.domain}/messages",
                auth=("api", self.api_key),
                data=data,
                files=files if files else None,
                timeout=60
            )
            
            if response.status_code == 200:
                return {
                    "success": True,
                    "message": f"Email enviado a {len(to_emails)} destinatarios",
                    "recipients": len(to_emails)
                }
            else:
                return {"success": False, "message": f"Error HTTP {response.status_code}"}
                
        except Exception as e:
            return {"success": False, "message": str(e)}


# =============================================================================
# FUNCIONES DE AYUDA
# =============================================================================

def get_email_service() -> Optional[EmailReportService]:
    """
    Factory para obtener servicio de email configurado.
    
    Returns:
        EmailReportService si está configurado, None si no
    """
    api_key = st.secrets.get("MAILGUN_API_KEY", "")
    domain = st.secrets.get("MAILGUN_DOMAIN", "")
    from_email = st.secrets.get("MAILGUN_FROM_EMAIL", "")
    from_name = st.secrets.get("MAILGUN_FROM_NAME", "Abra Trend Hunter")
    region = st.secrets.get("MAILGUN_REGION", "US")  # "US" o "EU"
    
    if not api_key or not domain or not from_email:
        return None
    
    try:
        return EmailReportService(
            api_key=api_key,
            domain=domain,
            from_email=from_email,
            from_name=from_name,
            region=region
        )
    except Exception:
        return None


def check_email_config() -> Dict[str, Any]:
    """
    Verifica la configuración de email.
    
    Returns:
        Dict con estado de configuración
    """
    api_key = st.secrets.get("MAILGUN_API_KEY", "")
    domain = st.secrets.get("MAILGUN_DOMAIN", "")
    from_email = st.secrets.get("MAILGUN_FROM_EMAIL", "")
    
    return {
        "configured": bool(api_key and domain and from_email),
        "has_api_key": bool(api_key),
        "has_domain": bool(domain),
        "has_from_email": bool(from_email),
        "domain": domain if domain else None
    }


def render_email_form(
    keyword: str,
    pdf_bytes: bytes,
    html_summary: str = ""
) -> None:
    """
    Renderiza formulario de envío de email en Streamlit.
    
    Args:
        keyword: Keyword analizado
        pdf_bytes: Bytes del PDF
        html_summary: Resumen HTML opcional
    """
    config = check_email_config()
    
    if not config["configured"]:
        st.info("""
        📧 **Configurar envío por email (Mailgun)**
        
        Añade a tu `secrets.toml`:
        ```toml
        MAILGUN_API_KEY = "key-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
        MAILGUN_DOMAIN = "mg.tudominio.com"
        MAILGUN_FROM_EMAIL = "reports@mg.tudominio.com"
        MAILGUN_FROM_NAME = "Abra Trend Hunter"
        MAILGUN_REGION = "EU"  # o "US"
        ```
        """)
        return
    
    # Formulario de envío
    with st.form("email_form"):
        st.markdown("#### 📧 Enviar informe por email")
        
        to_email = st.text_input(
            "Email destinatario",
            placeholder="usuario@empresa.com"
        )
        
        cc_emails = st.text_input(
            "CC (opcional, separados por coma)",
            placeholder="copia1@empresa.com, copia2@empresa.com"
        )
        
        include_pdf = st.checkbox("Adjuntar PDF", value=True)
        
        submitted = st.form_submit_button("📤 Enviar informe", type="primary")
        
        if submitted:
            if not to_email:
                st.error("Introduce un email destinatario")
                return
                
            service = get_email_service()
            if not service:
                st.error("Error inicializando servicio de email")
                return
            
            cc_list = [e.strip() for e in cc_emails.split(",") if e.strip()] if cc_emails else None
            
            with st.spinner("Enviando email..."):
                result = service.send_report(
                    to_email=to_email,
                    keyword=keyword,
                    pdf_bytes=pdf_bytes,
                    html_summary=html_summary,
                    include_pdf=include_pdf,
                    cc_emails=cc_list
                )
            
            if result["success"]:
                st.success(f"✅ {result['message']}")
            else:
                st.error(f"❌ {result['message']}")

