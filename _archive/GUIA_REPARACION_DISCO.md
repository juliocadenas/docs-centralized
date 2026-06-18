# 🔧 GUÍA DE REPARACIÓN - Servidor Madrid (NAB9)

> **EL SERVIDOR ESTÁ EN `busybox initramfs` PORQUE `/dev/sda3` ESTÁ CORROMPIDO**
> Esta guía es para la persona que está físicamente frente al servidor en Madrid.

---

## ✅ SOLUCIÓN RÁPIDA (Probar primero)

### Paso 1: Escribir el comando de reparación

En la pantalla negra donde dice `initramfs`, escribir EXACTAMENTE esto:

```
fsck -y /dev/sda3
```

Pulsar **Enter**.

### Paso 2: Esperar (PACIENCIA)

- El comando va a empezar a reparar errores.
- Puede tardar **5 minutos, 30 minutos, o más** dependiendo del daño.
- **NO APAGAR** el servidor ni tocar nada mientras esté trabajando.
- Verás mensajes como:
  - `Inode XXXX marked as used but... FIXED`
  - `Block XXXX... CORRECTED`
  - Muchas líneas de texto = **está funcionando bien**

### Paso 3: Reiniciar

Cuando termine (verás de nuevo `initramfs:` o `(initramfs)`), escribir:

```
reboot
```

Pulsar **Enter**.

---

## 🔄 SI `fsck` NO FUNCIONA

### Caso A: Dice "command not found" o "fsck: not found"

Probar estas alternativas una por una:

```
e2fsck -y /dev/sda3
```

Si tampoco funciona:

```
/bin/fsck -y /dev/sda3
```

Si tampoco funciona:

```
/sbin/fsck -y /dev/sda3
```

### Caso B: Dice "device not found" o "no such file"

Primero ver qué discos hay:

```
ls /dev/sd*
```

Y probar:

```
ls /dev/mapper/
```

Si aparece algo como `vgname-root` o similar, usar ese nombre:

```
fsck -y /dev/mapper/NOMBRE_QUE_APAREZCA
```

### Caso C: Dice " filesystem is mounted" o similar

Desmontar primero:

```
umount /dev/sda3
```

Y luego:

```
fsck -y /dev/sda3
```

### Caso D: Se queda colgado sin hacer nada tras escribir `exit`

Escribir:

```
exit
```

Y tomar foto de **TODOS los mensajes rojos** que aparezcan.
Esos mensajes son importantes para diagnosticar el problema real.

---

## ⚠️ SI NADA DE LO ANTERIOR FUNCIONA

### Opción Live USB (Más avanzada)

1. Necesitas un **USB con Ubuntu/Linux** (live USB)
2. Arrancar el servidor desde el USB (pulsar F12 o Esc al encender)
3. Abrir una terminal
4. Ejecutar:

```bash
sudo fsck -y /dev/sda3
```

5. Si sigue fallando, verificar el estado físico del disco:

```bash
sudo smartctl -a /dev/sda
```

Si dice `PASSED` → el disco está bien físicamente, es corrupción lógica.

Si dice `FAILED` → **el disco está muriendo físicamente** y hay que reemplazarlo.

---

## 📋 INFORMACIÓN QUE NECESITO QUE ME MANDES

Toma **FOTO** de la pantalla y mándamela por WhatsApp si:

1. ❌ Después de `fsck -y /dev/sda3` hay errores que no se reparan
2. ❌ Al hacer `reboot` vuelve a `busybox initramfs`
3. ❌ Aparecen mensajes rojos raros
4. ❌ El comando `fsck` no existe

---

## 🎯 RESUMEN PARA PERSONA QUE NO SABE LINUX

> **Lee solo esto si te pierdes:**

1. En la pantalla negra escribe: `fsck -y /dev/sda3`
2. Pulsa Enter
3. **Espera** que termine (no toques nada)
4. Escribe: `reboot`
5. Pulsa Enter
6. Si no funciona, mándame foto de lo que dice la pantalla

---

**Creado por:** Julio (desde Venezuela)  
**Para:** Persona en Madrid frente al servidor NAB9  
**Fecha:** Junio 2026