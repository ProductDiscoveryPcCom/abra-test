"""
PDF Report Generator
Genera informes PDF completos con todos los datos del análisis de tendencias

Incluye:
- Resumen ejecutivo
- Gráficos de tendencia (renderizados con Plotly + Kaleido)
- Métricas de scoring
- Análisis de productos
- Inteligencia de mercado
- Recomendaciones
"""

import io
import html
import re
from datetime import datetime
from typing import Optional, Dict, List, Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, Image, HRFlowable, ListFlowable, ListItem
)
from reportlab.graphics.shapes import Drawing, Rect, String
from reportlab.graphics.charts.lineplots import LinePlot
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.widgets.markers import makeMarker

# Plotly para gráficos mejorados
try:
    import plotly.graph_objects as go
    import plotly.express as px
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False


def plotly_to_image(fig, width: int = 700, height: int = 350) -> Optional[io.BytesIO]:
    """
    Convierte una figura Plotly a imagen PNG usando Kaleido.
    
    Args:
        fig: Figura de Plotly (go.Figure)
        width: Ancho en píxeles
        height: Alto en píxeles
        
    Returns:
        BytesIO con la imagen PNG, o None si falla
    """
    if not PLOTLY_AVAILABLE:
        return None
        
    try:
        # Configurar fondo blanco para PDF
        fig.update_layout(
            paper_bgcolor='white',
            plot_bgcolor='white',
            font=dict(size=10),
            margin=dict(l=40, r=40, t=40, b=40)
        )
        
        # Renderizar a PNG con Kaleido
        img_bytes = fig.to_image(
            format="png",
            width=width,
            height=height,
            scale=2  # 2x para mejor calidad
        )
        
        return io.BytesIO(img_bytes)
        
    except Exception as e:
        print(f"Error renderizando Plotly a imagen: {e}")
        return None


def create_trend_chart_for_pdf(
    dates: List[str],
    values: List[float],
    keyword: str
) -> Optional[io.BytesIO]:
    """
    Crea un gráfico de tendencia optimizado para PDF.
    
    Args:
        dates: Lista de fechas (strings)
        values: Lista de valores (0-100)
        keyword: Palabra clave para el título
        
    Returns:
        BytesIO con imagen PNG del gráfico
    """
    if not PLOTLY_AVAILABLE or not values:
        return None
        
    try:
        fig = go.Figure()
        
        # Añadir línea de tendencia
        fig.add_trace(go.Scatter(
            x=list(range(len(values))),
            y=values,
            mode='lines',
            line=dict(color='#6366F1', width=2),
            fill='tozeroy',
            fillcolor='rgba(99, 102, 241, 0.1)',
            name='Tendencia'
        ))
        
        # Añadir media móvil si hay suficientes datos
        if len(values) >= 4:
            window = min(4, len(values) // 4)
            ma = []
            for i in range(len(values)):
                start = max(0, i - window + 1)
                ma.append(sum(values[start:i+1]) / (i - start + 1))
            
            fig.add_trace(go.Scatter(
                x=list(range(len(values))),
                y=ma,
                mode='lines',
                line=dict(color='#F59E0B', width=1.5, dash='dash'),
                name='Media móvil'
            ))
        
        fig.update_layout(
            title=f'Tendencia: {keyword}',
            xaxis_title='Período',
            yaxis_title='Índice Google Trends',
            yaxis=dict(range=[0, 100]),
            showlegend=True,
            legend=dict(orientation='h', yanchor='bottom', y=1.02),
            height=300
        )
        
        return plotly_to_image(fig, width=700, height=300)
        
    except Exception as e:
        print(f"Error creando gráfico de tendencia: {e}")
        return None


def create_seasonality_chart_for_pdf(
    seasonality_data: Dict[str, Any]
) -> Optional[io.BytesIO]:
    """
    Crea un gráfico de estacionalidad para PDF.
    
    Args:
        seasonality_data: Datos de estacionalidad con 'monthly_avg'
        
    Returns:
        BytesIO con imagen PNG del gráfico
    """
    if not PLOTLY_AVAILABLE:
        return None
        
    monthly_avg = seasonality_data.get('monthly_avg', {})
    if not monthly_avg:
        return None
        
    try:
        months = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 
                  'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']
        values = [monthly_avg.get(str(i+1), 0) for i in range(12)]
        
        # Colores por intensidad
        colors_list = ['#10B981' if v >= 70 else '#F59E0B' if v >= 40 else '#6B7280' 
                       for v in values]
        
        fig = go.Figure(data=[
            go.Bar(x=months, y=values, marker_color=colors_list)
        ])
        
        fig.update_layout(
            title='Estacionalidad mensual',
            xaxis_title='Mes',
            yaxis_title='Índice promedio',
            yaxis=dict(range=[0, 100]),
            height=250
        )
        
        return plotly_to_image(fig, width=700, height=250)
        
    except Exception as e:
        print(f"Error creando gráfico de estacionalidad: {e}")
        return None


def _escape_xml(text: str) -> str:
    """
    Escapa texto para uso seguro en Reportlab Paragraph
    
    Reportlab usa un subset de XML para formateo, por lo que
    necesitamos escapar caracteres especiales.
    """
    if not text:
        return ""
    
    # Convertir a string
    text = str(text)
    
    # Escapar caracteres XML/HTML especiales
    text = html.escape(text, quote=False)
    
    # Reportlab tiene problemas con algunos caracteres
    # Reemplazar & que no sean entidades válidas
    text = re.sub(r'&(?!(amp|lt|gt|quot|apos|#\d+|#x[0-9a-fA-F]+);)', '&amp;', text)
    
    return text


class TrendReportPDF:
    """Generador de informes PDF para Abra Trend Hunter"""
    
    # Colores corporativos
    PRIMARY_COLOR = colors.HexColor("#6366F1")  # Indigo
    SECONDARY_COLOR = colors.HexColor("#8B5CF6")  # Violeta
    SUCCESS_COLOR = colors.HexColor("#10B981")  # Verde
    WARNING_COLOR = colors.HexColor("#F59E0B")  # Naranja
    DANGER_COLOR = colors.HexColor("#EF4444")  # Rojo
    TEXT_COLOR = colors.HexColor("#1F2937")  # Gris oscuro
    LIGHT_BG = colors.HexColor("#F3F4F6")  # Gris claro
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
        self.elements = []
        
    def _setup_custom_styles(self):
        """Configura estilos personalizados"""
        # Título principal
        self.styles.add(ParagraphStyle(
            name='MainTitle',
            parent=self.styles['Heading1'],
            fontSize=28,
            textColor=self.PRIMARY_COLOR,
            spaceAfter=30,
            alignment=TA_CENTER
        ))
        
        # Subtítulo
        self.styles.add(ParagraphStyle(
            name='Subtitle',
            parent=self.styles['Normal'],
            fontSize=14,
            textColor=colors.gray,
            spaceAfter=20,
            alignment=TA_CENTER
        ))
        
        # Sección
        self.styles.add(ParagraphStyle(
            name='SectionTitle',
            parent=self.styles['Heading2'],
            fontSize=16,
            textColor=self.PRIMARY_COLOR,
            spaceBefore=20,
            spaceAfter=10,
            borderPadding=(0, 0, 5, 0)
        ))
        
        # Subsección
        self.styles.add(ParagraphStyle(
            name='SubsectionTitle',
            parent=self.styles['Heading3'],
            fontSize=13,
            textColor=self.SECONDARY_COLOR,
            spaceBefore=15,
            spaceAfter=8
        ))
        
        # Texto normal
        self.styles.add(ParagraphStyle(
            name='BodyText',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=self.TEXT_COLOR,
            spaceAfter=8,
            alignment=TA_JUSTIFY,
            leading=14
        ))
        
        # Métricas destacadas
        self.styles.add(ParagraphStyle(
            name='MetricValue',
            parent=self.styles['Normal'],
            fontSize=24,
            textColor=self.PRIMARY_COLOR,
            alignment=TA_CENTER,
            spaceAfter=5
        ))
        
        # Label de métrica
        self.styles.add(ParagraphStyle(
            name='MetricLabel',
            parent=self.styles['Normal'],
            fontSize=9,
            textColor=colors.gray,
            alignment=TA_CENTER
        ))
        
        # Bullet points
        self.styles.add(ParagraphStyle(
            name='BulletText',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=self.TEXT_COLOR,
            leftIndent=20,
            spaceAfter=5
        ))
        
        # Nota/caption
        self.styles.add(ParagraphStyle(
            name='Caption',
            parent=self.styles['Normal'],
            fontSize=8,
            textColor=colors.gray,
            alignment=TA_CENTER,
            spaceAfter=10
        ))
    
    def _add_header(self, keyword: str, date: str):
        """Añade header del informe"""
        # Escapar inputs
        keyword = _escape_xml(keyword)
        date = _escape_xml(date)
        
        # Título
        self.elements.append(Paragraph(
            f"📊 Informe de Tendencia",
            self.styles['MainTitle']
        ))
        
        # Keyword analizado
        self.elements.append(Paragraph(
            f"<b>{html.escape(keyword)}</b>",
            self.styles['Subtitle']
        ))
        
        # Fecha
        self.elements.append(Paragraph(
            f"Generado el {date}",
            self.styles['Caption']
        ))
        
        self.elements.append(HRFlowable(
            width="100%",
            thickness=2,
            color=self.PRIMARY_COLOR,
            spaceAfter=20
        ))
    
    def _add_executive_summary(
        self,
        keyword: str,
        trend_score: int,
        potential_score: int,
        growth_rate: float,
        current_value: int,
        recommendation: str = ""
    ):
        """Añade resumen ejecutivo"""
        self.elements.append(Paragraph(
            "📋 Resumen Ejecutivo",
            self.styles['SectionTitle']
        ))
        
        # Métricas principales en tabla
        metrics_data = [
            ['Trend Score', 'Potential Score', 'Crecimiento', 'Índice Actual'],
            [
                f"{trend_score}/100",
                f"{potential_score}/100",
                f"{growth_rate:+.1f}%",
                f"{current_value}/100"
            ]
        ]
        
        metrics_table = Table(metrics_data, colWidths=[4*cm, 4*cm, 4*cm, 4*cm])
        metrics_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), self.LIGHT_BG),
            ('TEXTCOLOR', (0, 0), (-1, 0), self.TEXT_COLOR),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('FONTSIZE', (0, 1), (-1, 1), 18),
            ('TEXTCOLOR', (0, 1), (0, 1), self._get_score_color(trend_score)),
            ('TEXTCOLOR', (1, 1), (1, 1), self._get_score_color(potential_score)),
            ('TEXTCOLOR', (2, 1), (2, 1), self.SUCCESS_COLOR if growth_rate > 0 else self.DANGER_COLOR),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('TOPPADDING', (0, 1), (-1, 1), 15),
            ('BOTTOMPADDING', (0, 1), (-1, 1), 15),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ]))
        
        self.elements.append(metrics_table)
        self.elements.append(Spacer(1, 15))
        
        # Interpretación
        interpretation = self._get_interpretation(trend_score, potential_score, growth_rate)
        self.elements.append(Paragraph(interpretation, self.styles['BodyText']))
        
        if recommendation:
            self.elements.append(Spacer(1, 10))
            self.elements.append(Paragraph(
                f"<b>💡 Recomendación:</b> {_escape_xml(recommendation)}",
                self.styles['BodyText']
            ))
    
    def _get_score_color(self, score: int):
        """Retorna color según score"""
        if score >= 70:
            return self.SUCCESS_COLOR
        elif score >= 40:
            return self.WARNING_COLOR
        else:
            return self.DANGER_COLOR
    
    def _get_interpretation(
        self,
        trend_score: int,
        potential_score: int,
        growth_rate: float
    ) -> str:
        """Genera interpretación automática"""
        parts = []
        
        # Trend score
        if trend_score >= 70:
            parts.append("La tendencia muestra un <b>interés muy alto</b> en el mercado")
        elif trend_score >= 40:
            parts.append("La tendencia muestra un <b>interés moderado</b> en el mercado")
        else:
            parts.append("La tendencia muestra un <b>interés bajo</b> actualmente")
        
        # Growth
        if growth_rate > 50:
            parts.append("con un <b>crecimiento explosivo</b>")
        elif growth_rate > 20:
            parts.append("con un <b>crecimiento significativo</b>")
        elif growth_rate > 0:
            parts.append("con un <b>crecimiento ligero</b>")
        elif growth_rate > -10:
            parts.append("con una <b>tendencia estable</b>")
        else:
            parts.append("con una <b>tendencia a la baja</b>")
        
        # Potential
        if potential_score >= 70:
            parts.append("y un <b>alto potencial de oportunidad</b>.")
        elif potential_score >= 40:
            parts.append("y un <b>potencial moderado</b>.")
        else:
            parts.append("y un <b>potencial limitado</b> en este momento.")
        
        return " ".join(parts)
    
    def _add_trend_analysis(
        self,
        trend_values: List[int],
        dates: List[str],
        growth_data: Dict[str, Any],
        keyword: str = ""
    ):
        """Añade sección de análisis de tendencia con gráficos mejorados"""
        self.elements.append(Paragraph(
            "📈 Análisis de Tendencia",
            self.styles['SectionTitle']
        ))
        
        # Intentar crear gráfico con Plotly (mejor calidad)
        if trend_values and len(trend_values) > 0:
            plotly_chart = create_trend_chart_for_pdf(dates, trend_values, keyword)
            
            if plotly_chart:
                # Usar gráfico de Plotly renderizado con Kaleido
                img = Image(plotly_chart, width=16*cm, height=7*cm)
                self.elements.append(img)
            else:
                # Fallback a ReportLab básico si Plotly/Kaleido no disponible
                drawing = Drawing(450, 180)
                
                lp = LinePlot()
                lp.x = 50
                lp.y = 30
                lp.width = 380
                lp.height = 130
                
                data_points = trend_values[-52:] if len(trend_values) > 52 else trend_values
                lp.data = [[(i, v) for i, v in enumerate(data_points)]]
                
                lp.lines[0].strokeColor = self.PRIMARY_COLOR
                lp.lines[0].strokeWidth = 2
                
                lp.xValueAxis.valueMin = 0
                lp.xValueAxis.valueMax = len(data_points)
                lp.yValueAxis.valueMin = 0
                lp.yValueAxis.valueMax = 100
                
                drawing.add(lp)
                self.elements.append(drawing)
            
            self.elements.append(Paragraph(
                "Índice de Google Trends (0-100) - Últimos 12 meses",
                self.styles['Caption']
            ))
        
        # Tabla de métricas de tendencia
        self.elements.append(Spacer(1, 10))
        
        metrics = [
            ['Métrica', 'Valor'],
            ['Valor actual', f"{growth_data.get('current_value', 'N/A')}/100"],
            ['Valor promedio', f"{growth_data.get('avg_value', 'N/A')}/100"],
            ['Valor máximo', f"{growth_data.get('max_value', 'N/A')}/100"],
            ['Crecimiento 3 meses', f"{growth_data.get('growth_3m', 0):+.1f}%"],
            ['Crecimiento 12 meses', f"{growth_data.get('growth_12m', 0):+.1f}%"],
        ]
        
        table = Table(metrics, colWidths=[8*cm, 8*cm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), self.PRIMARY_COLOR),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, self.LIGHT_BG]),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ('PADDING', (0, 0), (-1, -1), 8),
        ]))
        
        self.elements.append(table)
    
    def _add_seasonality(self, seasonality_data: Dict[str, Any]):
        """Añade sección de estacionalidad con gráfico mejorado"""
        self.elements.append(Paragraph(
            "📅 Estacionalidad",
            self.styles['SectionTitle']
        ))
        
        is_seasonal = seasonality_data.get("is_seasonal", False)
        
        if is_seasonal:
            self.elements.append(Paragraph(
                "✅ <b>Se detecta patrón estacional</b>",
                self.styles['BodyText']
            ))
            
            # Intentar gráfico Plotly primero
            monthly = seasonality_data.get("monthly_pattern", {})
            if monthly:
                # Preparar datos para el gráfico
                chart_data = {"monthly_avg": {str(k): v for k, v in monthly.items()}}
                plotly_chart = create_seasonality_chart_for_pdf(chart_data)
                
                if plotly_chart:
                    img = Image(plotly_chart, width=16*cm, height=6*cm)
                    self.elements.append(img)
                else:
                    # Fallback a tabla
                    month_names = {
                        1: "Ene", 2: "Feb", 3: "Mar", 4: "Abr",
                        5: "May", 6: "Jun", 7: "Jul", 8: "Ago",
                        9: "Sep", 10: "Oct", 11: "Nov", 12: "Dic"
                    }
                    
                    if len(monthly) >= 6:
                        row1 = [month_names.get(i, str(i)) for i in range(1, 7)]
                        row2 = [f"{monthly.get(i, monthly.get(str(i), 0)):.0f}" for i in range(1, 7)]
                        row3 = [month_names.get(i, str(i)) for i in range(7, 13)]
                        row4 = [f"{monthly.get(i, monthly.get(str(i), 0)):.0f}" for i in range(7, 13)]
                        
                        table_data = [row1, row2, row3, row4]
                        table = Table(table_data, colWidths=[2.5*cm]*6)
                        table.setStyle(TableStyle([
                            ('BACKGROUND', (0, 0), (-1, 0), self.LIGHT_BG),
                            ('BACKGROUND', (0, 2), (-1, 2), self.LIGHT_BG),
                            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                            ('FONTNAME', (0, 2), (-1, 2), 'Helvetica-Bold'),
                            ('FONTSIZE', (0, 0), (-1, -1), 9),
                            ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
                            ('PADDING', (0, 0), (-1, -1), 6),
                        ]))
                        self.elements.append(table)
            
            # Explicación
            explanation = seasonality_data.get("explanation", "")
            if explanation:
                self.elements.append(Spacer(1, 10))
                self.elements.append(Paragraph(
                    f"<i>{_escape_xml(explanation)}</i>",
                    self.styles['BodyText']
                ))
        else:
            self.elements.append(Paragraph(
                "📊 No se detecta un patrón estacional claro. El interés es relativamente estable a lo largo del año.",
                self.styles['BodyText']
            ))
    
    def _add_related_queries(
        self,
        rising_queries: List[Dict],
        top_queries: List[Dict]
    ):
        """Añade sección de búsquedas relacionadas"""
        self.elements.append(Paragraph(
            "🔍 Búsquedas Relacionadas",
            self.styles['SectionTitle']
        ))
        
        # Queries en crecimiento
        if rising_queries:
            self.elements.append(Paragraph(
                "📈 En Crecimiento",
                self.styles['SubsectionTitle']
            ))
            
            data = [['Query', 'Crecimiento']]
            for q in rising_queries[:10]:
                query = q.get('query', q) if isinstance(q, dict) else str(q)
                query = _escape_xml(query[:40])  # Escapar y truncar
                growth = q.get('value', 'N/A') if isinstance(q, dict) else ''
                if growth == 'Breakout':
                    growth = '🚀 Breakout'
                elif isinstance(growth, (int, float)):
                    growth = f"+{growth}%"
                data.append([query, str(growth)])
            
            table = Table(data, colWidths=[10*cm, 5*cm])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), self.SUCCESS_COLOR),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('ALIGN', (1, 0), (1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, self.LIGHT_BG]),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
                ('PADDING', (0, 0), (-1, -1), 6),
            ]))
            self.elements.append(table)
        
        self.elements.append(Spacer(1, 10))
        
        # Top queries
        if top_queries:
            self.elements.append(Paragraph(
                "🏆 Más Populares",
                self.styles['SubsectionTitle']
            ))
            
            data = [['Query', 'Índice']]
            for q in top_queries[:10]:
                query = q.get('query', q) if isinstance(q, dict) else str(q)
                query = _escape_xml(query[:40])  # Escapar y truncar
                value = q.get('value', 'N/A') if isinstance(q, dict) else ''
                data.append([query, str(value)])
            
            table = Table(data, colWidths=[10*cm, 5*cm])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), self.PRIMARY_COLOR),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('ALIGN', (1, 0), (1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, self.LIGHT_BG]),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
                ('PADDING', (0, 0), (-1, -1), 6),
            ]))
            self.elements.append(table)
    
    def _add_products_analysis(self, products: List[Dict]):
        """Añade sección de análisis de productos"""
        self.elements.append(PageBreak())
        self.elements.append(Paragraph(
            "🛒 Análisis de Productos",
            self.styles['SectionTitle']
        ))
        
        if not products:
            self.elements.append(Paragraph(
                "No se encontraron productos relacionados.",
                self.styles['BodyText']
            ))
            return
        
        # Tabla de productos
        data = [['Producto', 'Ciclo de Vida', 'Crecimiento', 'Score']]
        
        for p in products[:15]:
            name = p.get('name', p.get('query', ''))[:35]
            lifecycle = p.get('lifecycle', 'N/A')
            growth = p.get('growth', 0)
            growth_str = f"{growth:+.0f}%" if isinstance(growth, (int, float)) else str(growth)
            score = p.get('trend_score', p.get('score', 'N/A'))
            
            data.append([name, lifecycle, growth_str, str(score)])
        
        table = Table(data, colWidths=[7*cm, 3.5*cm, 3*cm, 2.5*cm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), self.SECONDARY_COLOR),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, self.LIGHT_BG]),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ('PADDING', (0, 0), (-1, -1), 6),
        ]))
        self.elements.append(table)
    
    def _add_market_intelligence(self, market_data: Dict[str, Any]):
        """Añade sección de inteligencia de mercado (de Perplexity)"""
        self.elements.append(PageBreak())
        self.elements.append(Paragraph(
            "🧠 Inteligencia de Mercado",
            self.styles['SectionTitle']
        ))
        
        # Overview
        overview = market_data.get('brand_overview', '')
        if overview:
            self.elements.append(Paragraph(overview, self.styles['BodyText']))
            self.elements.append(Spacer(1, 10))
        
        # Posicionamiento competitivo
        positioning = market_data.get('brand_positioning', '')
        if positioning:
            self.elements.append(Paragraph(
                "🎯 Posicionamiento",
                self.styles['SubsectionTitle']
            ))
            self.elements.append(Paragraph(positioning, self.styles['BodyText']))
        
        # Competidores
        competitors = market_data.get('main_players', [])
        if competitors:
            self.elements.append(Paragraph(
                "⚔️ Competidores Principales",
                self.styles['SubsectionTitle']
            ))
            
            for comp in competitors[:5]:
                if isinstance(comp, dict):
                    name = comp.get('name', '')
                    position = comp.get('position', '')
                    self.elements.append(Paragraph(
                        f"• <b>{name}</b>: {position}",
                        self.styles['BulletText']
                    ))
                else:
                    self.elements.append(Paragraph(
                        f"• {comp}",
                        self.styles['BulletText']
                    ))
        
        # Oportunidades
        opportunities = market_data.get('market_opportunities', [])
        if opportunities:
            self.elements.append(Paragraph(
                "💡 Oportunidades Detectadas",
                self.styles['SubsectionTitle']
            ))
            for opp in opportunities[:5]:
                self.elements.append(Paragraph(
                    f"✅ {opp}",
                    self.styles['BulletText']
                ))
        
        # Amenazas
        threats = market_data.get('threats', [])
        if threats:
            self.elements.append(Paragraph(
                "⚠️ Amenazas",
                self.styles['SubsectionTitle']
            ))
            for threat in threats[:5]:
                self.elements.append(Paragraph(
                    f"🔴 {threat}",
                    self.styles['BulletText']
                ))
        
        # Recomendación estratégica
        recommendation = market_data.get('strategic_recommendation', '')
        if recommendation:
            self.elements.append(Spacer(1, 10))
            self.elements.append(Paragraph(
                "🎯 Recomendación Estratégica",
                self.styles['SubsectionTitle']
            ))
            self.elements.append(Paragraph(
                f"<b>{recommendation}</b>",
                self.styles['BodyText']
            ))
        
        # Action items
        actions = market_data.get('action_items', [])
        if actions:
            self.elements.append(Spacer(1, 5))
            for i, action in enumerate(actions[:5], 1):
                self.elements.append(Paragraph(
                    f"{i}. {action}",
                    self.styles['BulletText']
                ))
        
        # Fuentes
        sources = market_data.get('sources', [])
        if sources:
            self.elements.append(Spacer(1, 15))
            self.elements.append(Paragraph(
                f"<i>Fuentes: {', '.join(sources[:5])}</i>",
                self.styles['Caption']
            ))
    
    def _add_sentiment_analysis(self, sentiment_data: Dict[str, Any]):
        """Añade sección de análisis de sentimiento"""
        self.elements.append(Paragraph(
            "💬 Sentimiento del Mercado",
            self.styles['SectionTitle']
        ))
        
        # Indicador de sentimiento
        sentiment = sentiment_data.get('sentiment', 'Desconocido')
        sentiment_colors = {
            'Muy positivo': self.SUCCESS_COLOR,
            'Positivo': self.SUCCESS_COLOR,
            'Neutral': self.WARNING_COLOR,
            'Negativo': self.DANGER_COLOR,
            'Muy negativo': self.DANGER_COLOR
        }
        
        self.elements.append(Paragraph(
            f"<font color='{sentiment_colors.get(sentiment, self.TEXT_COLOR)}'><b>{sentiment}</b></font>",
            self.styles['MetricValue']
        ))
        
        summary = sentiment_data.get('sentiment_summary', '')
        if summary:
            self.elements.append(Paragraph(summary, self.styles['BodyText']))
        
        # Pros y contras en dos columnas
        pros = sentiment_data.get('pros', [])
        cons = sentiment_data.get('cons', [])
        
        if pros or cons:
            self.elements.append(Spacer(1, 10))
            
            pros_text = "\n".join([f"✅ {p}" for p in pros[:5]]) or "Sin datos"
            cons_text = "\n".join([f"❌ {c}" for c in cons[:5]]) or "Sin datos"
            
            data = [
                ['👍 Puntos Positivos', '👎 Puntos Negativos'],
                [pros_text, cons_text]
            ]
            
            table = Table(data, colWidths=[8*cm, 8*cm])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, 0), colors.HexColor("#D1FAE5")),
                ('BACKGROUND', (1, 0), (1, 0), colors.HexColor("#FEE2E2")),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
                ('PADDING', (0, 0), (-1, -1), 8),
            ]))
            self.elements.append(table)
    
    def _add_footer(self):
        """Añade footer del informe"""
        self.elements.append(Spacer(1, 30))
        self.elements.append(HRFlowable(
            width="100%",
            thickness=1,
            color=colors.lightgrey,
            spaceAfter=10
        ))
        self.elements.append(Paragraph(
            f"Generado por <b>Abra Trend Hunter</b> | {datetime.now().strftime('%d/%m/%Y %H:%M')}",
            self.styles['Caption']
        ))
        self.elements.append(Paragraph(
            "Los datos de tendencia provienen de Google Trends (índice 0-100, no volúmenes absolutos). "
            "La inteligencia de mercado proviene de búsquedas en tiempo real vía Perplexity AI.",
            self.styles['Caption']
        ))
    
    def generate_report(
        self,
        keyword: str,
        trend_score: int = 0,
        potential_score: int = 0,
        growth_rate: float = 0,
        current_value: int = 0,
        trend_values: List[int] = None,
        trend_dates: List[str] = None,
        growth_data: Dict[str, Any] = None,
        seasonality_data: Dict[str, Any] = None,
        rising_queries: List[Dict] = None,
        top_queries: List[Dict] = None,
        products: List[Dict] = None,
        market_intelligence: Dict[str, Any] = None,
        sentiment_data: Dict[str, Any] = None,
        ai_recommendation: str = ""
    ) -> bytes:
        """
        Genera el informe PDF completo
        
        Returns:
            bytes del PDF generado
        """
        self.elements = []
        
        # Buffer para el PDF
        buffer = io.BytesIO()
        
        # Crear documento
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm
        )
        
        # Header
        date_str = datetime.now().strftime("%d de %B de %Y")
        self._add_header(keyword, date_str)
        
        # Resumen ejecutivo
        self._add_executive_summary(
            keyword=keyword,
            trend_score=trend_score,
            potential_score=potential_score,
            growth_rate=growth_rate,
            current_value=current_value,
            recommendation=ai_recommendation
        )
        
        # Análisis de tendencia
        if trend_values:
            self._add_trend_analysis(
                trend_values=trend_values or [],
                dates=trend_dates or [],
                growth_data=growth_data or {},
                keyword=keyword
            )
        
        # Estacionalidad
        if seasonality_data:
            self._add_seasonality(seasonality_data)
        
        # Búsquedas relacionadas
        if rising_queries or top_queries:
            self._add_related_queries(
                rising_queries=rising_queries or [],
                top_queries=top_queries or []
            )
        
        # Productos
        if products:
            self._add_products_analysis(products)
        
        # Inteligencia de mercado (Perplexity)
        if market_intelligence:
            self._add_market_intelligence(market_intelligence)
        
        # Sentimiento
        if sentiment_data:
            self._add_sentiment_analysis(sentiment_data)
        
        # Footer
        self._add_footer()
        
        # Construir PDF
        doc.build(self.elements)
        
        # Retornar bytes
        buffer.seek(0)
        return buffer.getvalue()


def generate_trend_report(
    keyword: str,
    data: Dict[str, Any]
) -> bytes:
    """
    Función helper para generar informe desde los datos del análisis
    
    Args:
        keyword: Keyword analizado
        data: Dict con todos los datos del análisis
        
    Returns:
        bytes del PDF
    """
    generator = TrendReportPDF()
    
    return generator.generate_report(
        keyword=keyword,
        trend_score=data.get('trend_score', 0),
        potential_score=data.get('potential_score', 0),
        growth_rate=data.get('growth_rate', 0),
        current_value=data.get('current_value', 0),
        trend_values=data.get('trend_values', []),
        trend_dates=data.get('trend_dates', []),
        growth_data=data.get('growth_data', {}),
        seasonality_data=data.get('seasonality_data', {}),
        rising_queries=data.get('rising_queries', []),
        top_queries=data.get('top_queries', []),
        products=data.get('products', []),
        market_intelligence=data.get('market_intelligence', {}),
        sentiment_data=data.get('sentiment_data', {}),
        ai_recommendation=data.get('ai_recommendation', '')
    )
