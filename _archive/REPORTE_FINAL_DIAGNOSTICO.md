# 📊 REPORTE FINAL - Diagnóstico y Corrección del Servidor Madrid (NAB9)

> **Fecha:** 15 de Junio, 2026  
> **Ejecutado por:** Julio (remotamente desde Venezuela)  
> **Servidor:** NAB9 - 100.105.27.27 (Tailscale)

---

## 🎯 HALLAZGOS PRINCIPALES

### ✅ BUENA NOTICIA: El SSD está SANO físicamente

```
Disco: PNY 250GB SATA SSD (sda)
SMART Health: PASSED ✅
Sectores reasignados: 0 ✅
Sectores pendientes: 0 ✅
Errores SMART: 0 ✅
Horas de uso: 4.232 horas (~176 días)
Temperatura: 40°C ✅
Espacio reservado: 100% ✅
```

**El SSD NO se está muriendo.** El problema NO es el disco.

---

### 🔴 PROBLEMA #1 ENCONTRADO: ¡EL SSD ESTÁ CONECTADO POR USB!

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️  El SSD del sistema (/dev/sda) está conectado
    mediante un ADAPTADOR USB-SATA, NO por SATA interno.

    Dispositivo USB detectado:
    Other World Computing External SATA Hard Drive
    Adapter cable PA023U3

    Esto causa desconexiones momentáneas del SSD que
    CORROMPEN el filesystem. Es la causa #1 del problema.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

**ESTO EXPLICA TODO:**
- Las caídas a `busybox initramfs` son por micro-desconexiones USB
- El SSD se desconecta un instante → se corrompe el journal ext4
- En el próximo arranque, Linux detecta corrupción → cae a busybox

### 🔴 PROBLEMA #2: Disco al 95% (ahora 86%)

- **Antes:** 197GB usados de 220GB (12GB libres, 95%)
- **Después de limpieza:** 179GB usados (31GB libres, 86%)
- **Liberado:** ~18GB

### 🔴 PROBLEMA #3: No hay UPS

El servidor no tiene batería de respaldo. Si se va la luz, se corrompe.

---

## ✅ CORRECCIONES APLICADAS (15 Junio 2026)

### 1. fsck en CADA arranque
```
Maximum mount count: 1 (antes: -1 = desactivado)
```
Ahora Linux revisa el disco SIEMPRE antes de arrancar.

### 2. Auto-fsck en initramfs
Script instalado que ejecuta `fsck -y /dev/sda3` automáticamente si cae a busybox. Ya no debería necesitar intervención manual.

### 3. Limpieza de espacio (18GB liberados)
- Docker build cache: 17.5GB eliminados
- Journal logs: ~998MB → 100MB
- apt cache: 796MB limpiados
- Paquetes huérfanos eliminados

### 4. Script de monitoreo instalado
- `/usr/local/bin/disk-monitor.sh` ejecuta cada hora (cron)
- Monitorea: SMART, espacio en disco, errores ext4, errores USB

---

## 🚧 TODAVÍA HAY 75GB RECUPERABLES EN DOCKER

```
Docker images: 53.71GB (98% reclaimable - imágenes sin usar)
Build cache:   22.22GB (reclaimable)
TOTAL RECUPERABLE: ~75GB
```

Para liberar más espacio (con cuidado), ejecutar en el servidor:
```bash
# Ver qué imágenes hay
docker images

# Eliminar imágenes que no se usan (CUIDADO: revisar primero)
docker image prune -a -f

# Eliminar todo el build cache
docker builder prune -a -f
```

---

## 🎯 RECOMENDACIONES CRÍTICAS (POR PRIORIDAD)

### 🔴 PRIORIDAD MÁXIMA: Conectar el SSD por SATA interno

> **ESTO ES LO QUE HAY QUE HACER SÍ O SÍ.**

El SSD PNY de 250GB está conectado por un adaptador USB-SATA externo. Hay que:

1. **Abrir el NAB9** y conectar el SSD directamente a un puerto SATA de la placa base
2. Si no hay puerto SATA disponible, **comprar un SSD M.2** e instalar el sistema ahí
3. Un SSD M.2 de 250-500GB cuesta **20-40€**

**Mientras el SSD siga por USB, el problema VA A REPETIRSE.**

### 🟡 PRIORIDAD ALTA: Comprar UPS (SAI)

- Un UPS básico cuesta **50-100€**
- Evita corrupción por cortes de energía
- Recomendado: APC Back-UPS 600VA o similar

### 🟡 PRIORIDAD MEDIA: Limpiar más Docker

Aún hay 75GB en imágenes Docker sin usar. Ejecutar limpieza completa.

### 🟢 PRIORIDAD BAJA: Mover datos al Seagate 1.8TB

- `AI_MODELS_BACKUP` (51GB) debería ir al Seagate USB
- `Wan2GP` (39GB) podría moverse al Seagate

---

## 📋 ESTADO ACTUAL DEL SISTEMA

| Métrica | Valor | Estado |
|---------|-------|--------|
| SMART del SSD | PASSED | ✅ Sano |
| Espacio libre | 31GB (14%) | ⚠️ Mejoró del 5% |
| fsck automático | Activado | ✅ Configurado |
| Auto-fsck initramfs | Instalado | ✅ Configurado |
| Monitoreo | Cada hora | ✅ Activo |
| UPS | No tiene | ❌ Faltante |
| Conexión SSD | USB (problema) | ❌ Debe ser SATA |

---

## 🔧 ARCHIVOS CREADOS

| Archivo | Descripción |
|---------|-------------|
| `GUIA_REPARACION_DISCO.md` | Guía para reparar manualmente si cae a busybox |
| `PREVENCION_CORRUPCION.md` | Explicación de causas y soluciones |
| `diagnostico_disco.sh` | Script de diagnóstico para ejecutar en el servidor |
| `diag_remoto.py` | Ejecuta diagnóstico desde PC remoto |
| `deep_diag.py` | Diagnóstico profundo (SMART USB + espacio) |
| `aplicar_correcciones.py` | Aplica todas las correcciones preventivas |
| `RESULTADO_DIAGNOSTICO.txt` | Resultados del primer diagnóstico |
| `RESULTADO_PROFUNDO.txt` | Resultados del diagnóstico profundo |

---

**Conclusión:** El disco está sano pero conectado por USB, que es la causa raíz de la corrupción recurrente. Ya aplicamos prevención automática (fsck en cada boot + auto-fsck en initramfs), pero la solución definitiva es conectar el SSD por SATA interno.