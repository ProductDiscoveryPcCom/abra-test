"""
Scoring Engine
Calcula scores de tendencia actual y potencial de explosión
"""

from typing import Optional, List
import numpy as np
from dataclasses import dataclass


@dataclass
class TrendMetrics:
    """Métricas calculadas de una tendencia"""
    current_value: float
    avg_value: float
    growth_rate: float
    volatility: float
    momentum: float
    seasonality_score: float
    

class ScoringEngine:
    """Motor de cálculo de scores para tendencias"""
    
    def __init__(self):
        # Pesos para el cálculo del score
        self.trend_weights = {
            "current_vs_avg": 0.25,
            "growth_rate": 0.30,
            "momentum": 0.25,
            "consistency": 0.20
        }
        
        self.potential_weights = {
            "growth_acceleration": 0.30,
            "early_stage": 0.25,
            "rising_queries": 0.25,
            "low_competition": 0.20
        }
    
    def calculate_trend_score(
        self,
        timeline_data: list,
        related_queries_count: int = 0,
        paa_count: int = 0
    ) -> dict:
        """
        Calcula el Trend Score (0-100)
        Indica qué tan "trendy" es la marca actualmente
        
        Factores:
        - Valor actual vs promedio histórico
        - Tasa de crecimiento reciente
        - Momentum (aceleración del crecimiento)
        - Consistencia de la tendencia
        """
        if not timeline_data:
            return {
                "score": 0,
                "grade": "F",
                "factors": {},
                "explanation": "No hay datos suficientes"
            }
        
        # Extraer valores
        values = self._extract_values(timeline_data)
        
        if len(values) < 4:
            return {
                "score": 0,
                "grade": "F", 
                "factors": {},
                "explanation": "No hay datos suficientes"
            }
        
        # Calcular métricas
        metrics = self._calculate_metrics(values)
        
        # Factor 1: Valor actual vs promedio (0-100)
        if metrics.avg_value > 0:
            current_vs_avg = min(100, (metrics.current_value / metrics.avg_value) * 50)
        else:
            current_vs_avg = 50
        
        # Factor 2: Growth rate (0-100)
        # Mapear growth rate a score: -50% = 0, 0% = 50, +50% = 100
        growth_score = min(100, max(0, 50 + metrics.growth_rate))
        
        # Factor 3: Momentum (0-100)
        # Momentum positivo = la tendencia se está acelerando
        momentum_score = min(100, max(0, 50 + metrics.momentum * 2))
        
        # Factor 4: Consistencia (0-100)
        # Menor volatilidad = más consistente
        consistency_score = max(0, 100 - metrics.volatility)
        
        # Calcular score final
        final_score = (
            current_vs_avg * self.trend_weights["current_vs_avg"] +
            growth_score * self.trend_weights["growth_rate"] +
            momentum_score * self.trend_weights["momentum"] +
            consistency_score * self.trend_weights["consistency"]
        )
        
        # Bonus por queries relacionadas
        if related_queries_count > 10:
            final_score = min(100, final_score + 5)
        
        final_score = round(final_score)
        
        return {
            "score": final_score,
            "grade": self._score_to_grade(final_score),
            "factors": {
                "current_vs_avg": round(current_vs_avg),
                "growth": round(growth_score),
                "momentum": round(momentum_score),
                "consistency": round(consistency_score)
            },
            "metrics": {
                "current_value": round(metrics.current_value, 1),
                "avg_value": round(metrics.avg_value, 1),
                "growth_rate": round(metrics.growth_rate, 1),
                "momentum": round(metrics.momentum, 2)
            },
            "explanation": self._generate_trend_explanation(final_score, metrics)
        }
    
    def calculate_potential_score(
        self,
        timeline_data: list,
        rising_queries: list = None,
        current_value: float = 0,
        is_seasonal: bool = False
    ) -> dict:
        """
        Calcula el Potential Score (0-100)
        Indica la probabilidad de que la marca "explote"
        
        Factores:
        - Aceleración del crecimiento (segunda derivada)
        - Etapa temprana (valores bajos pero creciendo)
        - Rising queries con alto crecimiento
        - Bajo volumen actual (espacio para crecer)
        """
        if not timeline_data:
            return {
                "score": 0,
                "grade": "F",
                "factors": {},
                "explanation": "No hay datos suficientes"
            }
        
        values = self._extract_values(timeline_data)
        
        if len(values) < 6:
            return {
                "score": 0,
                "grade": "F",
                "factors": {},
                "explanation": "No hay datos suficientes"
            }
        
        rising_queries = rising_queries or []
        
        # Factor 1: Aceleración del crecimiento (0-100)
        acceleration = self._calculate_acceleration(values)
        acceleration_score = min(100, max(0, 50 + acceleration * 5))
        
        # Factor 2: Etapa temprana (0-100)
        # Score alto si el valor actual es bajo pero creciendo
        avg_value = sum(values) / len(values)
        recent_growth = self._calculate_recent_growth(values)
        
        if avg_value < 30 and recent_growth > 10:
            early_stage_score = 90
        elif avg_value < 50 and recent_growth > 5:
            early_stage_score = 70
        elif avg_value < 70 and recent_growth > 0:
            early_stage_score = 50
        else:
            early_stage_score = 30
        
        # Factor 3: Rising queries (0-100)
        rising_score = 0
        if rising_queries:
            breakout_count = sum(1 for q in rising_queries 
                               if q.get("extracted_value") == "Breakout" or 
                               q.get("extracted_value", 0) > 1000)
            high_growth_count = sum(1 for q in rising_queries 
                                   if isinstance(q.get("extracted_value"), int) and 
                                   q.get("extracted_value", 0) > 200)
            
            rising_score = min(100, breakout_count * 30 + high_growth_count * 15)
        
        # Factor 4: Espacio para crecer (0-100)
        # Valor actual bajo = más espacio
        if current_value or (values and values[-1]):
            current = current_value or values[-1]
            growth_room_score = max(0, 100 - current)
        else:
            growth_room_score = 50
        
        # Calcular score final
        final_score = (
            acceleration_score * self.potential_weights["growth_acceleration"] +
            early_stage_score * self.potential_weights["early_stage"] +
            rising_score * self.potential_weights["rising_queries"] +
            growth_room_score * self.potential_weights["low_competition"]
        )
        
        # Penalización por estacionalidad alta
        if is_seasonal:
            final_score *= 0.85
        
        final_score = round(final_score)
        
        return {
            "score": final_score,
            "grade": self._score_to_grade(final_score),
            "factors": {
                "acceleration": round(acceleration_score),
                "early_stage": round(early_stage_score),
                "rising_queries": round(rising_score),
                "growth_room": round(growth_room_score)
            },
            "explanation": self._generate_potential_explanation(final_score, rising_queries)
        }
    
    def calculate_opportunity_level(
        self,
        trend_score: int,
        potential_score: int
    ) -> dict:
        """
        Determina el nivel de oportunidad combinando ambos scores
        """
        combined = (trend_score * 0.4) + (potential_score * 0.6)
        
        if combined >= 75:
            level = "ALTA"
            color = "#10B981"
            icon = "🔥"
            action = "Actuar ahora - oportunidad caliente"
        elif combined >= 55:
            level = "MEDIA"
            color = "#F59E0B"
            icon = "⚡"
            action = "Monitorizar de cerca"
        elif combined >= 35:
            level = "BAJA"
            color = "#6B7280"
            icon = "👀"
            action = "Observar evolución"
        else:
            level = "MUY BAJA"
            color = "#EF4444"
            icon = "❄️"
            action = "No prioritario"
        
        return {
            "level": level,
            "combined_score": round(combined),
            "color": color,
            "icon": icon,
            "action": action
        }
    
    def _extract_values(self, timeline_data: list) -> list:
        """Extrae los valores numéricos del timeline"""
        values = []
        for point in timeline_data:
            if "values" in point and len(point["values"]) > 0:
                val = point["values"][0].get("extracted_value", 0)
                values.append(float(val) if val else 0)
        return values
    
    def _calculate_metrics(self, values: list) -> TrendMetrics:
        """Calcula métricas básicas de la serie temporal"""
        if not values:
            return TrendMetrics(
                current_value=0,
                avg_value=0,
                growth_rate=0,
                volatility=0,
                momentum=0,
                seasonality_score=0
            )
        
        current_value = values[-1] if values else 0
        avg_value = sum(values) / len(values) if values else 0
        
        # Growth rate (últimos 3 meses vs anteriores)
        if len(values) >= 6:
            recent = sum(values[-3:]) / 3
            previous_values = values[-6:-3]
            if previous_values:
                previous = sum(previous_values) / len(previous_values)
                growth_rate = ((recent - previous) / previous * 100) if previous > 0 else (100 if recent > 0 else 0)
            else:
                growth_rate = 0
        else:
            growth_rate = 0
        
        # Volatilidad (desviación estándar relativa)
        if avg_value > 0 and len(values) > 1:
            try:
                std_dev = np.std(values)
                volatility = (std_dev / avg_value) * 100
            except Exception:
                volatility = 0
        else:
            volatility = 0
        
        # Momentum (cambio en el growth rate)
        if len(values) >= 9:
            recent_growth = self._calculate_growth(values[-6:])
            previous_growth = self._calculate_growth(values[-9:-3])
            momentum = recent_growth - previous_growth
        else:
            momentum = 0
        
        return TrendMetrics(
            current_value=current_value,
            avg_value=avg_value,
            growth_rate=growth_rate,
            volatility=volatility,
            momentum=momentum,
            seasonality_score=0
        )
    
    def _calculate_growth(self, values: list) -> float:
        """Calcula el crecimiento de una serie"""
        if not values or len(values) < 2:
            return 0
        first_val = values[0] if values[0] else 0.001  # Evitar división por cero
        if first_val == 0:
            return 100 if values[-1] > 0 else 0
        return ((values[-1] - first_val) / first_val) * 100
    
    def _calculate_recent_growth(self, values: list) -> float:
        """Calcula el crecimiento reciente (último tercio)"""
        if len(values) < 3:
            return 0
        third = len(values) // 3
        recent = values[-third:] if third > 0 else values[-1:]
        previous = values[:third] if third > 0 else values[:1]
        
        avg_recent = sum(recent) / len(recent)
        avg_previous = sum(previous) / len(previous)
        
        if avg_previous > 0:
            return ((avg_recent - avg_previous) / avg_previous) * 100
        return 0
    
    def _calculate_acceleration(self, values: list) -> float:
        """Calcula la aceleración (segunda derivada del crecimiento)"""
        if len(values) < 9:
            return 0
        
        # Dividir en 3 periodos
        third = len(values) // 3
        period1 = values[:third]
        period2 = values[third:2*third]
        period3 = values[2*third:]
        
        avg1 = sum(period1) / len(period1)
        avg2 = sum(period2) / len(period2)
        avg3 = sum(period3) / len(period3)
        
        # Crecimiento periodo 1->2 y 2->3
        if avg1 > 0 and avg2 > 0:
            growth1 = (avg2 - avg1) / avg1
            growth2 = (avg3 - avg2) / avg2
            acceleration = growth2 - growth1
        else:
            acceleration = 0
        
        return acceleration * 100
    
    def _score_to_grade(self, score: int) -> str:
        """Convierte score numérico a letra"""
        if score >= 90:
            return "A+"
        elif score >= 80:
            return "A"
        elif score >= 70:
            return "B+"
        elif score >= 60:
            return "B"
        elif score >= 50:
            return "C+"
        elif score >= 40:
            return "C"
        elif score >= 30:
            return "D"
        else:
            return "F"
    
    def _generate_trend_explanation(self, score: int, metrics: TrendMetrics) -> str:
        """Genera explicación del trend score"""
        if score >= 75:
            base = "Tendencia muy fuerte."
        elif score >= 50:
            base = "Tendencia moderada."
        else:
            base = "Tendencia débil."
        
        details = []
        
        if metrics.growth_rate > 20:
            details.append(f"Crecimiento alto ({metrics.growth_rate:.0f}%)")
        elif metrics.growth_rate < -10:
            details.append(f"En declive ({metrics.growth_rate:.0f}%)")
        
        if metrics.momentum > 5:
            details.append("Acelerando")
        elif metrics.momentum < -5:
            details.append("Desacelerando")
        
        return f"{base} {', '.join(details)}" if details else base
    
    def _generate_potential_explanation(self, score: int, rising_queries: list) -> str:
        """Genera explicación del potential score"""
        if score >= 75:
            base = "Alto potencial de explosión."
        elif score >= 50:
            base = "Potencial moderado."
        else:
            base = "Potencial limitado."
        
        breakouts = sum(1 for q in rising_queries 
                       if q.get("extracted_value") == "Breakout")
        
        if breakouts > 0:
            base += f" {breakouts} queries en breakout."
        
        return base
