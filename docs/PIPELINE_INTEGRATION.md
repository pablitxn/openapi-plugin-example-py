# GenEY Pipeline Integration Guide

This document describes how to integrate your Python plugin with the GenEY deployment pipeline.

## Prerequisites

- Your code must be in the GenEY repository (`ey-org/tax-gen-ai`)
- Docker support with a valid `Dockerfile` in the root directory
- Azure DevOps access to run pipelines

## Onboarding Process

### 1. Initial Service Onboarding

If your plugin is a new service that hasn't been deployed before:

1. **Contact GenEY Development Team**
   - Reach out to the GenEY development team (@Luis De La Torre Camacho and @George Mathew)
   - Provide the repository path to your Dockerfile
   - Request onboarding into the pipeline process

2. **Provide Required Information**
   - Service name
   - Repository path
   - Dockerfile location
   - Environment configurations needed

3. **Wait for Confirmation**
   - The GenEY team will configure your service in the pipeline
   - You'll receive confirmation when your service is available for deployment

### 2. Deployment Process

Once your service is onboarded:

1. **Create Pull Request**
   - Push your code to the GenEY repository
   - Create a PR to the appropriate branch (see Branching Strategy)
   - Address all review comments

2. **Access Azure Pipelines**
   - Navigate to Azure DevOps Pipelines
   - Go to the "GenEY" folder
   - Find the "GenEY-Python-Plugins" pipeline
   - Direct URL: [Pipelines - Runs for GenEY-Python-Plugins](https://dev.azure.com/your-org/your-project/_build)

3. **Run the Pipeline**
   - Click "Run pipeline"
   - Select the correct branch
   - Provide parameters:
     - **Application Name**: Select your service from the dropdown
     - **Environment**: Choose deployment environment
       - `Development` - No approval required
       - `QA/Staging/Production` - Requires approval

4. **Monitor Deployment**
   - Watch the pipeline execution
   - Check logs for any errors
   - Verify deployment success

## Pipeline Configuration

The pipeline will:

1. Build your Docker image using the provided Dockerfile
2. Push the image to Azure Container Registry (ACR)
3. Deploy to Azure Container Apps
4. Configure environment variables from Azure Key Vault

### Environment Variables

The following environment variables are automatically configured:

- `clientSecret` - Retrieved from Azure Key Vault
- `APPLICATIONINSIGHTS_CONNECTION_STRING` - For telemetry
- `AZURE_STORAGE_CONNECTION_STRING` - For blob storage
- `OPENAI_API_KEY` - For AI services

### Build Arguments

The pipeline passes the following build arguments to Docker:

```dockerfile
ARG Environment
ENV ENV=$Environment
```

## Validation

After deployment:

1. **Check Health Endpoint**
   ```bash
   curl https://your-service-url/health
   ```

2. **Verify Swagger Documentation**
   - Navigate to `https://your-service-url/docs`
   - Test your API endpoints

3. **Check Application Insights**
   - Verify telemetry is being received
   - Monitor for any errors

## Troubleshooting

### Common Issues

1. **Service Not Listed in Pipeline**
   - Contact GenEY team for onboarding
   - Verify service name matches configuration

2. **Build Failures**
   - Check Dockerfile syntax
   - Ensure all dependencies are specified
   - Verify base image is accessible

3. **Deployment Failures**
   - Check environment configuration
   - Verify required secrets are in Key Vault
   - Review container logs in Azure Portal

### Support

For pipeline-related issues:
- Contact GenEY Development Team
- Check Azure DevOps pipeline logs
- Review Azure Container Apps logs

## Best Practices

1. **Test Locally First**
   ```bash
   docker build -t your-plugin --build-arg Environment=development .
   docker run -p 8000:4260 -e clientSecret=$clientSecret your-plugin
   ```

2. **Use Proper Branching**
   - Follow the branching strategy guidelines
   - Test in development before promoting

3. **Monitor Deployments**
   - Set up alerts in Application Insights
   - Monitor container health
   - Track API performance

## Related Documentation

- [Branching Strategy](./BRANCHING_STRATEGY.md)
- [CI/CD Guidelines](./CICD_GUIDELINES.md)
- [Azure Container Apps Documentation](https://docs.microsoft.com/azure/container-apps/)