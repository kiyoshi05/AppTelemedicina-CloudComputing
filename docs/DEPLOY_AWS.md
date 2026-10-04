# Despliegue de SaludYa en AWS (EC2 t2.micro)

Guía paso a paso para subir el proyecto a GitHub y desplegarlo en una EC2 con Docker Compose.

**Resultado final:** la app disponible en `http://TU_ELASTIC_IP`, con 5 contenedores (Nginx + 4 microservicios) en una EC2 t2.micro de N. Virginia.

**Tiempo estimado:** 45 a 60 minutos la primera vez.

**Necesitas:**
- Una cuenta de AWS con acceso a la consola.
- Una cuenta de GitHub.
- Git instalado en tu PC.
- La terminal **PowerShell** de Windows (para SSH).

---

## Parte 1 · Subir el código a GitHub

### Paso 1. Crear el repositorio en GitHub

1. Entra a https://github.com/new
2. **Repository name:** `saludya-telemedicina`
3. Visibilidad: **Public** (más simple para clonarlo en la EC2) o **Private** (ver nota del paso 9).
4. **No** marques "Add a README", ".gitignore" ni licencia: el proyecto ya los tiene.
5. Clic en **Create repository** y copia la URL HTTPS, por ejemplo `https://github.com/TU_USUARIO/saludya-telemedicina.git`.

### Paso 2. Subir los archivos desde tu PC

En PowerShell, entra a la carpeta del proyecto:

```powershell
cd "D:\#CFUKUMOTO\PROYECTOS\saludya-telemedicina"
```

Ejecuta estos comandos uno por uno:

```powershell
git init
git add .
git commit -m "SaludYa: front, gateway y 4 microservicios con SQLite"
git branch -M main
git remote add origin https://github.com/TU_USUARIO/saludya-telemedicina.git
git push -u origin main
```

La primera vez, Git abre una ventana del navegador para iniciar sesión en GitHub. Al terminar, recarga la página del repositorio y verifica que aparezcan las carpetas `frontend`, `backend`, `docs`, `postman` y `scripts`.

---

## Parte 2 · Preparar AWS

> Antes de empezar, en la esquina superior derecha de la consola de AWS selecciona la región **US East (N. Virginia) us-east-1**. Todo lo que sigue debe crearse en esa región.

### Paso 3. Crear el par de llaves (key pair)

1. Consola de AWS → **EC2** → menú izquierdo **Network & Security → Key Pairs** → **Create key pair**.
2. **Name:** `saludya-key`
3. **Key pair type:** RSA · **Private key file format:** `.pem`
4. **Create key pair**. Se descarga `saludya-key.pem`.
5. Muévelo a `C:\Users\kiyo0\.ssh\saludya-key.pem` (crea la carpeta `.ssh` si no existe).

> Guárdalo bien: AWS no permite volver a descargarlo. **Nunca lo subas a GitHub** (el `.gitignore` ya excluye los `.pem`).

### Paso 4. Crear el security group (firewall)

1. **EC2 → Network & Security → Security Groups → Create security group**.
2. **Name:** `saludya-sg` · **Description:** `SaludYa web y SSH` · **VPC:** la que viene por defecto.
3. **Inbound rules → Add rule** dos veces:

| Type | Port | Source | Para qué |
|---|---|---|---|
| SSH | 22 | **My IP** | Solo tú puedes conectarte por SSH |
| HTTP | 80 | **Anywhere-IPv4** (0.0.0.0/0) | Cualquiera puede abrir la web |

4. **Outbound rules:** déjalas como están (todo permitido).
5. **Create security group**.

> No abras los puertos 8001 a 8004: los microservicios solo se usan dentro de Docker, a través de Nginx.

### Paso 5. Lanzar la instancia EC2

**EC2 → Instances → Launch instances**:

| Campo | Valor |
|---|---|
| Name | `saludya-mvp` |
| AMI | **Amazon Linux 2023 AMI** (64-bit x86) |
| Instance type | **t2.micro** (verifica que diga *Free tier eligible* si quieres usar la capa gratuita) |
| Key pair | `saludya-key` |
| Network settings → Firewall | **Select existing security group** → `saludya-sg` |
| Configure storage | **20 GiB**, tipo **gp3** |

Clic en **Launch instance** y espera a que el **Instance state** sea *Running* y los **Status checks** digan *2/2 checks passed* (2 a 3 minutos).

### Paso 6. Asignar una Elastic IP (IP fija)

Sin Elastic IP, la IP pública cambia cada vez que detienes e inicias la instancia.

1. **EC2 → Network & Security → Elastic IPs → Allocate Elastic IP address → Allocate**.
2. Selecciona la IP creada → **Actions → Associate Elastic IP address**.
3. **Resource type:** Instance · **Instance:** `saludya-mvp` → **Associate**.
4. Anota la IP. En esta guía la llamamos `TU_ELASTIC_IP`.

---

## Parte 3 · Instalar y levantar la app en la EC2

### Paso 7. Conectarte por SSH desde Windows

En PowerShell, deja la llave con permisos solo para tu usuario (SSH rechaza llaves con permisos abiertos):

```powershell
icacls "C:\Users\kiyo0\.ssh\saludya-key.pem" /inheritance:r
```

```powershell
icacls "C:\Users\kiyo0\.ssh\saludya-key.pem" /grant:r "$($env:USERNAME):(R)"
```

Conéctate:

```powershell
ssh -i "C:\Users\kiyo0\.ssh\saludya-key.pem" ec2-user@TU_ELASTIC_IP
```

La primera vez pregunta *Are you sure you want to continue connecting?*: escribe `yes`.

> **Alternativa sin llave:** en la consola, selecciona la instancia → **Connect → EC2 Instance Connect → Connect**. Se abre una terminal en el navegador. Para esto, el security group debe permitir SSH desde las IPs de AWS; si falla, cambia temporalmente la regla de SSH a *Anywhere* y vuelve a dejarla en *My IP* al terminar.

### Paso 8. Instalar Git y clonar el repositorio

Ya dentro de la EC2 (el prompt dice `[ec2-user@ip-... ~]$`):

```bash
sudo dnf install -y git
```

```bash
git clone https://github.com/TU_USUARIO/saludya-telemedicina.git
```

```bash
cd saludya-telemedicina
```

> **Si el repositorio es privado:** GitHub pide usuario y contraseña. En la contraseña pega un **Personal Access Token** (GitHub → Settings → Developer settings → Personal access tokens → Fine-grained tokens, con permiso de lectura sobre el repositorio). Tu contraseña normal de GitHub no funciona aquí.

### Paso 9. Preparar el servidor (Docker, Compose y swap)

El script instala Docker, Docker Compose y Buildx, y crea 1 GB de swap (la t2.micro tiene solo 1 GB de RAM y la compilación de imágenes necesita más):

```bash
bash scripts/ec2-setup.sh
```

Al final muestra las versiones instaladas y la memoria. Luego **cierra la sesión** para que tu usuario quede en el grupo `docker`:

```bash
exit
```

Vuelve a conectarte con el mismo comando `ssh` del paso 7 y entra a la carpeta:

```bash
cd saludya-telemedicina
```

### Paso 10. Construir y levantar los contenedores

```bash
docker compose up -d --build
```

> En una t2.micro (1 vCPU) la primera construcción tarda entre 5 y 10 minutos. Las siguientes son más rápidas porque Docker reutiliza capas.

Verifica que los 5 contenedores estén en estado `running` (o `Up`):

```bash
docker compose ps
```

Debes ver `web-saludya`, `ms-pacientes`, `ms-medicos`, `ms-citas` y `ms-recetas`.

### Paso 11. Probar la aplicación

| Qué | URL |
|---|---|
| Aplicación web | `http://TU_ELASTIC_IP` |
| Swagger de pacientes | `http://TU_ELASTIC_IP/api/pacientes/docs` |
| Swagger de médicos | `http://TU_ELASTIC_IP/api/medicos/docs` |
| Swagger de citas | `http://TU_ELASTIC_IP/api/citas/docs` |
| Swagger de recetas | `http://TU_ELASTIC_IP/api/recetas/docs` |

1. Abre la app desde tu PC y también desde tu celular (comprueba el diseño responsive).
2. Inicia sesión con `maria.rojas@gmail.com` / `demo1234`, agenda una cita y revisa "Mis citas" y la receta.
3. En Postman: **Import** → `postman/saludya.postman_collection.json` → en la colección, pestaña **Variables**, cambia `base_url` a `http://TU_ELASTIC_IP`.

---

## Parte 4 · Operación del día a día

### Ver logs

```bash
docker compose logs -f citas
```

`Ctrl + C` para salir. Cambia `citas` por `frontend`, `pacientes`, `medicos` o `recetas`.

### Publicar cambios

En tu PC: `git add .`, `git commit -m "..."` y `git push`. Luego, en la EC2:

```bash
cd ~/saludya-telemedicina && git pull && docker compose up -d --build
```

Solo se reconstruyen los servicios que cambiaron. Los datos se conservan porque viven en volúmenes.

### Respaldar las bases SQLite

```bash
mkdir -p ~/backup
```

```bash
for s in pacientes medicos citas recetas; do docker compose cp $s:/data/$s.db ~/backup/$s-$(date +%F).db; done
```

Para bajar los respaldos a tu PC, desde PowerShell:

```powershell
scp -i "C:\Users\kiyo0\.ssh\saludya-key.pem" "ec2-user@TU_ELASTIC_IP:~/backup/*" .
```

### Reiniciar o detener la app

```bash
docker compose restart
```

```bash
docker compose down
```

`docker compose down` detiene los contenedores pero **conserva** los datos. Con `docker compose down -v` se borran también los volúmenes (todas las bases).

---

## Parte 5 · Costos y limpieza

- **t2.micro:** entra en la capa gratuita si tu cuenta es elegible; si no, cuesta alrededor de USD 0.0116 por hora en N. Virginia.
- **Disco gp3 de 20 GiB:** dentro de la capa gratuita (hasta 30 GiB) si tu cuenta es elegible.
- **IP pública / Elastic IP:** AWS cobra cada IPv4 pública (alrededor de USD 0.005 por hora), esté o no asociada.
- **Detener la instancia** (Instance state → Stop) deja de cobrar la EC2, pero no el disco ni la Elastic IP. Los datos se conservan.

**Para eliminar todo al terminar el curso:**
1. Respalda las bases (Parte 4).
2. **EC2 → Instances →** `saludya-mvp` **→ Instance state → Terminate**. Esto borra la instancia, su disco y los datos.
3. **Elastic IPs →** selecciona la IP **→ Actions → Release Elastic IP address**.
4. Opcional: borra el security group `saludya-sg` y el key pair `saludya-key`.

---

## Solución de problemas

| Síntoma | Causa probable | Solución |
|---|---|---|
| La página no carga (se queda esperando) | Puerto 80 cerrado | Revisa la regla HTTP 80 en `saludya-sg` |
| `ssh: connect ... Connection timed out` | Tu IP cambió | Edita la regla SSH del security group → **My IP** |
| `Permissions for 'saludya-key.pem' are too open` | Permisos de la llave en Windows | Repite los comandos `icacls` del paso 7 |
| `permission denied ... docker.sock` | No cerraste sesión tras el paso 9 | `exit` y vuelve a conectarte |
| `compose build requires buildx 0.17 or later` | Falta Buildx | Vuelve a ejecutar `bash scripts/ec2-setup.sh` |
| La construcción se detiene o la EC2 se cuelga | Falta memoria | Verifica la swap con `free -h` (debe mostrar *Swap: 1.0Gi*) |
| `502 Bad Gateway` al usar la app | Un microservicio está caído | `docker compose ps` y `docker compose logs <servicio>` |
| Ves la versión anterior del front | Caché del navegador | `Ctrl + F5` para recargar sin caché |
