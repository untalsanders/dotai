---
name: deploy
description: Construye, valida y despliega la aplicación Spring Boot al entorno indicado.
argument-hint: <entorno> (local | staging | production)
---

Despliega la aplicación al entorno **$ARGUMENTS**.

Si no se indica entorno, pregunta antes de continuar. Nunca asumas el entorno destino.

## 1. Validaciones previas al deploy

### Verificar que el branch es el correcto

```bash
git branch --show-current
git status
```

- Para `staging`: debe ser `main` o una rama de release.
- Para `production`: debe ser `main` con todos los cambios ya mergeados y revisados.
- Si hay cambios sin commitear, detente y avisa — nunca deploys con estado sucio.

### Ejecutar la suite completa de tests

```bash
./mvnw verify -q
```

Si algún test falla, el deploy se cancela. Sin excepciones.

### Verificar que no hay secretos expuestos

```bash
git diff origin/main..HEAD -- src/main/resources/application*.yml | grep -E "(password|secret|key|token)" || echo "OK"
```

Si aparece algún resultado, detente y avisa antes de continuar.

---

## 2. Build del artefacto

```bash
./mvnw clean package -DskipTests -q
```

Verifica que el JAR se generó correctamente:

```bash
ls -lh target/*.jar
java -jar target/*.jar --spring.profiles.active=$ARGUMENTS --dry-run 2>/dev/null || true
```

---

## 3. Build y push de la imagen Docker

```bash
IMAGE_TAG=$(git rev-parse --short HEAD)
IMAGE_NAME="tu-registro/$ARGUMENTS/nombre-app"

docker build \
  --build-arg JAR_FILE=target/*.jar \
  --build-arg BUILD_DATE=$(date -u +%Y-%m-%dT%H:%M:%SZ) \
  --build-arg GIT_COMMIT=$IMAGE_TAG \
  --tag "$IMAGE_NAME:$IMAGE_TAG" \
  --tag "$IMAGE_NAME:latest" \
  .

docker push "$IMAGE_NAME:$IMAGE_TAG"
docker push "$IMAGE_NAME:latest"

echo "Image pushed: $IMAGE_NAME:$IMAGE_TAG"
```

---

## 4. Deploy por entorno

### Local

```bash
docker compose -f docker-compose.yml -f docker-compose.local.yml up -d --build
```

### Staging

```bash
kubectl set image deployment/nombre-app \
  nombre-app="$IMAGE_NAME:$IMAGE_TAG" \
  --namespace=staging

kubectl rollout status deployment/nombre-app --namespace=staging --timeout=120s
```

### Production

Requiere confirmación explícita antes de ejecutar:

```
¿Confirmas el deploy a PRODUCCIÓN con la imagen $IMAGE_NAME:$IMAGE_TAG?
Escribe 'sí' para continuar o cualquier otra cosa para cancelar.
```

```bash
kubectl set image deployment/nombre-app \
  nombre-app="$IMAGE_NAME:$IMAGE_TAG" \
  --namespace=production

kubectl rollout status deployment/nombre-app --namespace=production --timeout=180s
```

---

## 5. Verificación post-deploy

### Health check

```bash
BASE_URL="https://api-$ARGUMENTS.tudominio.com"

# Esperar a que la app responda (máx 60s)
for i in $(seq 1 12); do
  STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/actuator/health")
  if [ "$STATUS" = "200" ]; then
    echo "Health check OK"
    break
  fi
  echo "Esperando... ($i/12)"
  sleep 5
done

if [ "$STATUS" != "200" ]; then
  echo "FALLO: la app no responde. Iniciando rollback."
  exit 1
fi
```

### Verificar los endpoints críticos

```bash
# Comprobar que la API responde correctamente
curl -sf "$BASE_URL/api/v1/health" | jq '.data.status'

# Verificar que las métricas están expuestas
curl -sf "$BASE_URL/actuator/metrics" | jq '.names | length'

# Verificar que las migraciones Flyway se aplicaron
curl -sf "$BASE_URL/actuator/flyway" | jq '.contexts[].flywayBeans[].migrations | map(select(.state != "SUCCESS"))'
```

Si alguna migración no está en estado `SUCCESS`, ejecuta rollback inmediatamente.

---

## 6. Rollback

Si algo falla después del deploy:

### Kubernetes

```bash
kubectl rollout undo deployment/nombre-app --namespace=$ARGUMENTS
kubectl rollout status deployment/nombre-app --namespace=$ARGUMENTS --timeout=120s
```

### Docker Compose

```bash
docker compose -f docker-compose.yml -f docker-compose.$ARGUMENTS.yml down
docker compose -f docker-compose.yml -f docker-compose.$ARGUMENTS.yml up -d --no-build
```

Después del rollback, documenta el incidente:
1. Qué salió mal.
2. Qué imagen estaba en producción antes.
3. Qué imagen se intentó desplegar.
4. Cuánto tardó en detectarse y en revertirse.

---

## 7. Registro del deploy

Al finalizar exitosamente, deja constancia:

```bash
gh release create "v$(date +%Y%m%d)-$IMAGE_TAG" \
  --title "Deploy $ARGUMENTS — $(date +%Y-%m-%d)" \
  --notes "Imagen: $IMAGE_NAME:$IMAGE_TAG
Entorno: $ARGUMENTS
Commit: $(git log -1 --pretty='%h %s')
Deploy realizado por: $(git config user.name)" \
  --prerelease=$([ "$ARGUMENTS" != "production" ] && echo "true" || echo "false")
```
