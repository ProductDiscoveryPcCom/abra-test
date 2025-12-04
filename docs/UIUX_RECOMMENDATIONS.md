# 🎨 Recomendaciones UI/UX - Abra Trend Hunter

## Estado Actual

La app tiene una base sólida pero necesita mejoras en jerarquía visual y organización.

---

## 1. 🎯 Regla 60-30-10 (Colores)

### Distribución Actual
```
Dorado (#F5C518) - Acento/CTA     ✅ ~10%
Púrpura (#7C3AED) - Secundario    ⚠️ ~20% (debería ser 30%)
Blanco/Gris - Dominante           ⚠️ ~70% (debería ser 60%)
```

### Recomendación
| Proporción | Color | Uso |
|------------|-------|-----|
| **60%** | Blanco/Gris (#FAFAFA) | Fondos, espacios |
| **30%** | Púrpura (#7C3AED) | Headers, cards principales, bordes |
| **10%** | Dorado (#F5C518) | CTAs, badges, highlights |

### Cambios Sugeridos

1. **Añadir más color púrpura** en:
   - Headers de secciones (no solo texto)
   - Bordes de cards principales
   - Iconos de navegación

2. **Reservar dorado solo para**:
   - Botón "Analizar" (CTA principal)
   - Badges de "Breakout" o "Trending"
   - Indicadores de score alto (>70)

---

## 2. 📐 Jerarquía Visual

### Problemas Identificados

1. **Demasiados separadores** (`st.markdown("---")`)
   - 12 separadores horizontales = ruido visual
   - Solución: Usar espaciado y cards en lugar de líneas

2. **Expanders ocultan información importante**
   - Social Media, Market Intelligence están colapsados
   - El usuario no sabe qué hay dentro
   - Solución: Mostrar preview/resumen antes del expander

3. **Sin agrupación lógica clara**
   - Datos de tendencias mezclados con scores
   - Solución: Crear "zonas" visuales claras

### Estructura Propuesta

```
┌─────────────────────────────────────────────┐
│  🔍 BÚSQUEDA                                │ ← Zona 1: Input
├─────────────────────────────────────────────┤
│  📊 RESUMEN EJECUTIVO                       │ ← Zona 2: KPIs
│  ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐           │
│  │Score│ │Score│ │Growth│ │Index│           │
│  └─────┘ └─────┘ └─────┘ └─────┘           │
├─────────────────────────────────────────────┤
│  📈 ANÁLISIS DE TENDENCIA                   │ ← Zona 3: Gráficos
│  [Gráfico principal]                        │
│  [Estacionalidad]                           │
├─────────────────────────────────────────────┤
│  🔍 INTELIGENCIA DE MERCADO                 │ ← Zona 4: Insights
│  [Market Intelligence] [Social] [News]      │
├─────────────────────────────────────────────┤
│  📦 PRODUCTOS Y OPORTUNIDADES               │ ← Zona 5: Acción
│  [Matriz BCG] [Keywords] [Exportar]         │
└─────────────────────────────────────────────┘
```

---

## 3. 📱 Responsive Design

### Breakpoints Recomendados

```css
/* Mobile First */
@media (max-width: 768px) {
    /* Stacked layout */
    .syntax-grid { grid-template-columns: 1fr; }
    /* Reducir padding */
    .card { padding: var(--space-3); }
    /* Ocultar elementos secundarios */
    .hide-mobile { display: none; }
}

@media (min-width: 769px) and (max-width: 1024px) {
    /* Tablet */
    .syntax-grid { grid-template-columns: repeat(2, 1fr); }
}

@media (min-width: 1025px) {
    /* Desktop */
    .syntax-grid { grid-template-columns: repeat(4, 1fr); }
}
```

### Mejoras Móviles Necesarias

1. **Reducir tamaño de métricas** en mobile
2. **Colapsar gráficos** a versión simplificada
3. **Menú hamburguesa** para sidebar
4. **Touch-friendly** botones mínimo 44x44px

---

## 4. ⚖️ Equilibrio y Armonía

### Espaciado Consistente

```
Sección a sección:     32px (--space-8)
Card a card:           16px (--space-4)
Elementos internos:    8-12px (--space-2/3)
```

### Cards con Jerarquía

```
┌────────────────────────────────────────┐
│ PRIMARIO (Score Cards)                 │
│ - Borde izquierdo grueso (4px)         │
│ - Sombra lg                            │
│ - Padding 24px                         │
└────────────────────────────────────────┘

┌────────────────────────────────────────┐
│ SECUNDARIO (Queries, Topics)           │
│ - Borde sutil (1px)                    │
│ - Sombra sm                            │
│ - Padding 16px                         │
└────────────────────────────────────────┘

┌────────────────────────────────────────┐
│ TERCIARIO (Detalles, Expandibles)      │
│ - Sin borde                            │
│ - Sin sombra                           │
│ - Padding 12px                         │
└────────────────────────────────────────┘
```

---

## 5. 🚀 Mejoras Prioritarias

### Alta Prioridad (Hacer ahora)

1. **Reemplazar separadores por espaciado**
   ```python
   # Antes
   st.markdown("---")
   
   # Después
   st.markdown("<div style='margin: 2rem 0;'></div>", unsafe_allow_html=True)
   ```

2. **Añadir headers de sección con estilo**
   ```python
   def section_header(title, icon):
       st.markdown(f"""
       <div class="section-header">
           <span class="section-icon">{icon}</span>
           <h3 class="section-title">{title}</h3>
       </div>
       """, unsafe_allow_html=True)
   ```

3. **Preview antes de expanders**
   ```python
   # Mostrar resumen antes del expander
   st.info("🧠 3 insights disponibles | 5 fuentes citadas")
   with st.expander("Ver análisis completo"):
       ...
   ```

### Media Prioridad (Próxima iteración)

4. **Tabs en lugar de múltiples expanders**
   ```python
   tab1, tab2, tab3 = st.tabs(["📊 Tendencia", "🧠 Mercado", "📱 Social"])
   ```

5. **Sticky header con KPIs**
   - Mostrar scores siempre visibles mientras scroll

6. **Loading states mejorados**
   - Skeleton screens en lugar de spinners

### Baja Prioridad (Futuro)

7. **Dark mode toggle**
8. **Exportar como imagen (además de PDF)**
9. **Guardar análisis favoritos**

---

## 6. 🎨 CSS Adicional Sugerido

```css
/* Section Headers */
.section-header {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 16px 0;
    border-bottom: 2px solid var(--abra-purple-light);
    margin-bottom: 16px;
}

.section-icon {
    font-size: 1.5rem;
    background: var(--abra-purple-light);
    padding: 8px;
    border-radius: var(--radius-sm);
}

.section-title {
    font-size: 1.25rem;
    font-weight: 600;
    color: var(--abra-dark);
    margin: 0;
}

/* Zone Container */
.zone {
    background: var(--abra-white);
    border-radius: var(--radius-lg);
    padding: var(--space-6);
    margin-bottom: var(--space-6);
    box-shadow: var(--shadow-sm);
}

.zone-executive {
    background: linear-gradient(135deg, var(--abra-purple-light) 0%, var(--abra-white) 100%);
    border: 1px solid var(--abra-purple);
}

.zone-insights {
    background: linear-gradient(135deg, var(--abra-gold-light) 0%, var(--abra-white) 100%);
    border: 1px solid var(--abra-gold);
}

/* Preview Badge */
.preview-badge {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    background: var(--abra-info-light);
    color: var(--abra-info);
    padding: 6px 12px;
    border-radius: var(--radius-full);
    font-size: 0.8rem;
    font-weight: 500;
    margin-bottom: 8px;
}
```

---

## 7. 📊 Métricas de Éxito UI/UX

| Métrica | Actual | Objetivo |
|---------|--------|----------|
| Tiempo hasta primer insight | ~5s | <3s |
| Scroll necesario para KPIs | 0 | 0 ✅ |
| Expanders abiertos por sesión | ? | <2 |
| Tasa de uso móvil | ? | >30% |
| Tiempo en página | ? | >2min |

---

## Resumen Ejecutivo

**Top 3 cambios de mayor impacto:**

1. ✅ **Regla 60-30-10**: Más púrpura, menos líneas grises
2. ✅ **Zonas visuales**: Agrupar contenido relacionado
3. ✅ **Preview antes de expanders**: El usuario sabe qué hay dentro

**No cambiar:**
- Paleta de colores (gold + purple funciona bien)
- Tipografías (Space Grotesk + DM Sans)
- Sistema de cards (ya está bien implementado)
