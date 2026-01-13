# AWS Elastic Beanstalk Deployment

This document describes the steps to deploy the TalaTrivia backend to AWS Elastic Beanstalk using the Docker platform.

## Prerequisites

- AWS CLI configured with appropriate credentials
- AWS account with permissions to create EB applications
- RDS PostgreSQL database configured (or use DATABASE_URL from another source)

## Deployment Steps

### 1. Create Application and Environment in Elastic Beanstalk

#### Option A: Using AWS Console

1. Access the AWS Elastic Beanstalk console
2. Click on "Create application"
3. Basic configuration:
   - **Application name**: `talatrivia-backend`
   - **Platform**: Docker
   - **Platform branch**: Docker running on 64bit Amazon Linux 2
   - **Platform version**: (use the most recent)
4. Click on "Create application"

5. Once the application is created, click on "Create environment"
6. Environment configuration:
   - **Environment tier**: Web server environment
   - **Application name**: `talatrivia-backend`
   - **Environment name**: `talatrivia-backend-prod` (or your preferred name)
   - **Domain**: (optional, EB will generate one automatically)
   - **Platform**: Docker (same as before)
7. In "Application code", select "Upload your code"
8. Create a ZIP file with the contents of `/backend`:
   ```bash
   cd backend
   zip -r ../talatrivia-backend.zip . -x "*.git*" -x "*__pycache__*" -x "*.pytest_cache*"
   ```
9. Upload the ZIP file in the console
10. Click on "Create environment"

#### Option B: Using EB CLI (Recommended for updates)

1. Install EB CLI:
   ```bash
   pip install awsebcli
   ```

2. In the `/backend` directory, initialize EB:
   ```bash
   cd backend
   eb init
   ```
   - Select the region
   - Select the application (or create a new one)
   - Select Docker as platform

3. Create the environment:
   ```bash
   eb create talatrivia-backend-prod
   ```

4. To update after changes:
   ```bash
   eb deploy
   ```

### 2. Configure Environment Variables

In the Elastic Beanstalk console:

1. Go to your environment
2. Click on "Configuration" → "Software"
3. In "Environment properties", add:

   **REQUIRED:**
   - `DATABASE_URL`: Full connection URL to RDS PostgreSQL
     - Format: `postgresql+asyncpg://user:password@host:port/dbname`
     - Example: `postgresql+asyncpg://admin:mypassword@talatrivia-db.xxxxx.us-east-1.rds.amazonaws.com:5432/talatrivia`
     - **This is mandatory in production** - the application will fail to start if not set

   **OPTIONAL (but recommended):**
   - `ENV`: `production` (recommended to disable development logs)
   - `CORS_ORIGINS`: Allowed origins separated by commas
     - Example: `https://your-amplify-app.amplifyapp.com,https://www.yourdomain.com`
     - Default: `http://localhost:5173,http://localhost:80` (only for local development)
   - `PORT`: Port number (default: `8000`, EB usually sets this automatically)

### 3. Run Database Migrations

**IMPORTANT**: Before the first deployment, you must run database migrations to create the schema.

1. Connect to your EB instance via SSH (EB Console → Your Environment → Configuration → Security → SSH)
2. Navigate to the application directory
3. Run migrations:
   ```bash
   alembic upgrade head
   ```

Alternatively, you can run migrations from your local machine if you have access to the RDS database:
```bash
cd backend
DATABASE_URL="postgresql+asyncpg://user:pass@rds-endpoint:5432/dbname" alembic upgrade head
```

**Note**: Migrations are NOT executed automatically on startup. You must run them manually before the first deployment.

### 4. Health Check

The health check endpoints are configured at:
- **Route**: `/health` - Basic health check (fast, no DB query)
  - **Method**: GET
  - **Response**: `{"status": "ok"}`
- **Route**: `/health/db` - Database health check (verifies DB connectivity)
  - **Method**: GET
  - **Response**: `{"status": "ok", "database": "connected"}` or `503` if DB is unavailable

Make sure the health check in EB points to `/health` (or `/health/db` if you want to verify database connectivity).

### 5. Local Dockerfile Testing

Before deploying, you can test locally:

```bash
cd backend
docker build -t talatrivia-backend .
docker run -p 8000:8000 \
  --env DATABASE_URL="postgresql+asyncpg://user:pass@host:5432/dbname" \
  --env CORS_ORIGINS="http://localhost:5173" \
  talatrivia-backend
```

Then verify:
```bash
curl http://localhost:8000/health
```

### 6. Verify Deployment

Once deployed, verify:
1. Health check should respond: `curl https://your-eb-url.elasticbeanstalk.com/health`
2. Logs in EB Console → Logs to verify there are no errors
3. The application should be accessible at the URL provided by EB

## Important Notes

- **Database**: In production, use RDS PostgreSQL. Do not use Docker containers for the DB.
- **Port**: The container exposes port 8000 (or the one defined in PORT). EB will map this automatically.
- **CORS**: Make sure to configure `CORS_ORIGINS` with the exact URLs of your frontend in Amplify.
- **Secrets**: Never upload `.env` files with real credentials to the repository.

## Troubleshooting

- If the health check fails, check the logs in EB Console
- Verify that `DATABASE_URL` is correctly configured
- Make sure the RDS Security Group allows connections from the EB Security Group
