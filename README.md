# Stroop Cognitivo Adaptativo v2

## Novedades

| Característica | v1 | v2 |
|---|---|---|
| Pantalla de inicio configurable | ❌ | ✅ ID, edad, nivel de inicio |
| Grupos de edad con normas | ❌ | ✅ 4 grupos clínicos |
| Tiempos adaptativos por edad | ❌ | ✅ |
| Calibración de cámara | ❌ | ✅ Captura rango de movimiento |
| Cámara al centro | Miniatura | ✅ Feed grande central |
| Mano fuera de frame | Crash | ✅ Manejo seguro |
| Comparación normativa en reporte | ❌ | ✅ |
| σ RT (variabilidad atencional) | ❌ | ✅ |

## Instalación

```bash
pip install -r requirements.txt
python main.py
```

## Flujo de sesión

1. Pantalla de inicio: ingresar ID, edad, nivel de inicio
2. [Recomendado] Calibración: mover la mano 5 segundos por pantalla
3. Test por niveles: palabra al centro, señalar color en esquina
4. Entre niveles: resultados vs norma del grupo de edad
5. Al final: PDF + CSV generados automáticamente

## Grupos de edad y normas (Golden 1978, Troyer 2006)

| Grupo | Edad | RT Congruente | RT Incongruente | Interferencia |
|---|---|---|---|---|
| Niño/a | 8–12 | ~1400ms | ~2000ms | ~600ms |
| Adulto joven | 18–35 | ~900ms | ~1250ms | ~350ms |
| Adulto medio | 36–59 | ~1050ms | ~1500ms | ~450ms |
| Adulto mayor | 60+ | ~1300ms | ~1950ms | ~650ms |

## Controles

| Tecla | Acción |
|---|---|
| TAB | Cambiar campo activo |
| ENTER | Confirmar / avanzar |
| ESC | Volver a inicio |
| Q | Salir |

## Config rápida (config.py)

```python
LANGUAGE      = "es"   # "es" o "en"
FULLSCREEN    = True
CAMERA_INDEX  = 0      # cambiar si usas cámara externa
DWELL_TIME_MS = 450    # ms para confirmar selección con el dedo
```

> ⚠️ Herramienta de apoyo. Interpretación clínica a cargo de profesional certificado.
