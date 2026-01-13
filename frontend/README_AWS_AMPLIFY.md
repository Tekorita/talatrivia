# AWS Amplify Deployment

This document describes the steps to deploy the TalaTrivia frontend to AWS Amplify.

## Prerequisites

- AWS account with permissions to create applications in Amplify
- Git repository (GitHub, GitLab, Bitbucket, or CodeCommit) with the frontend code
- Backend deployed on Elastic Beanstalk (to get the API URL)

## Deployment Steps

### 1. Connect Repository in Amplify

1. Access the AWS Amplify console
2. Click on "New app" → "Host web app"
3. Select your Git provider (GitHub, GitLab, Bitbucket, or CodeCommit)
4. Authorize Amplify to access your repository
5. Select the repository and branch (e.g., `main` or `development`)
6. Amplify will automatically detect the `amplify.yml` file in the repository root

### 2. Configure Environment Variables

In the Amplify build configuration:

1. Go to "App settings" → "Environment variables"
2. Add the variable:
   - **Key**: `VITE_API_URL`
   - **Value**: Full URL of your backend in Elastic Beanstalk
     - Example: `https://talatrivia-backend-prod.elasticbeanstalk.com`
     - Or if you have a custom domain: `https://api.yourdomain.com`

### 3. Configure Build

Amplify will automatically use the `amplify.yml` file in the repository root, which is configured to:
- Install dependencies from `/frontend`
- Build the project from `/frontend`
- Serve files from `/frontend/dist`

### 4. Deploy

1. Amplify will automatically start the build and deploy after connecting the repository
2. You can monitor progress in the Amplify console
3. Once completed, Amplify will provide a URL to access your application

### 5. Configure Custom Domain (Optional)

1. In the Amplify console, go to "Domain management"
2. Click on "Add domain"
3. Enter your domain
4. Follow the instructions to configure DNS records

### 6. Update CORS in Backend

**IMPORTANT**: After deploying the frontend, update `CORS_ORIGINS` in Elastic Beanstalk to include the Amplify URL:

1. Go to Elastic Beanstalk → Your environment → Configuration → Software
2. Update `CORS_ORIGINS` to include:
   - The Amplify URL (e.g., `https://main.d1234567890.amplifyapp.com`)
   - Your custom domain if configured
   - Separated by commas: `https://amplify-url.amplifyapp.com,https://www.yourdomain.com`

### 7. Verify Deployment

1. Access the URL provided by Amplify
2. Verify that the application loads correctly
3. Test functionalities that require backend communication
4. Check the browser console to ensure there are no CORS errors

## Future Updates

Every time you push to the connected branch, Amplify will:
1. Automatically detect changes
2. Start a new build
3. Deploy the new version

You can view the build history in the Amplify console.

## Important Notes

- **Environment variables**: Only variables starting with `VITE_` are available in the frontend code
- **Build**: The `amplify.yml` file is configured to build from `/frontend`
- **CORS**: Make sure the backend has `CORS_ORIGINS` configured with the Amplify URL
- **Cache**: Amplify caches `node_modules` for faster builds

## Troubleshooting

- If the build fails, check the logs in the Amplify console
- If there are CORS errors, verify that `CORS_ORIGINS` in EB includes the Amplify URL
- If the application doesn't load, verify that `VITE_API_URL` is correctly configured
