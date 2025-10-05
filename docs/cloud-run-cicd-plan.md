# Simple Google Cloud Run CI/CD for a Hobby Project

This guide keeps the pipeline lightweight while still giving you push-button deploys. The idea: push to `main`, GitHub Actions builds the container, pushes it to Artifact Registry, and redeploys your single Cloud Run service.

## 1. One-Time Google Cloud Setup
1. **Create or pick a Google Cloud project.** Note the project ID.
2. **Enable the required APIs** (Cloud Run, Artifact Registry, Cloud Build, IAM) once via the console or `gcloud services enable run.googleapis.com artifactregistry.googleapis.com cloudbuild.googleapis.com iam.googleapis.com`.
3. **Create an Artifact Registry repo** (e.g., `gcloud artifacts repositories create hobby-app --repository-format=docker --location=us-central1`).
4. **Create a service account** for deployments (e.g., `cloud-run-deployer@<project>.iam.gserviceaccount.com`) and grant:
   - `roles/run.admin`
   - `roles/iam.serviceAccountUser`
   - `roles/artifactregistry.writer`
5. **Generate a key** for that service account and store it securely—you will paste it into GitHub later.

## 2. Prepare Your Repo
* Add a Dockerfile at the repo root that can build the app locally.
* (Optional) Create a `Makefile` target like `make docker-build` to match what the workflow will do.
* Add the following secrets to your GitHub repository settings:
  - `GCP_PROJECT_ID`
  - `GCP_REGION` (e.g., `us-central1`)
  - `GCP_SERVICE_ACCOUNT_KEY` (the JSON key you downloaded)
  - `CLOUD_RUN_SERVICE` (name you want, e.g., `coordinate-converter`)

## 3. GitHub Actions Workflow
Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy to Cloud Run

on:
  push:
    branches: ["main"]

jobs:
  deploy:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Set up gcloud
        uses: google-github-actions/setup-gcloud@v2
        with:
          service_account_key: ${{ secrets.GCP_SERVICE_ACCOUNT_KEY }}
          project_id: ${{ secrets.GCP_PROJECT_ID }}

      - name: Configure Docker auth
        run: gcloud auth configure-docker ${{ secrets.GCP_REGION }}-docker.pkg.dev --quiet

      - name: Build image
        run: |
          IMAGE="${{ secrets.GCP_REGION }}-docker.pkg.dev/${{ secrets.GCP_PROJECT_ID }}/hobby-app/${{ secrets.CLOUD_RUN_SERVICE }}:${GITHUB_SHA}"
          docker build -t "$IMAGE" .
          echo "IMAGE=$IMAGE" >> $GITHUB_ENV

      - name: Push image
        run: docker push "$IMAGE"

      - name: Deploy to Cloud Run
        run: |
          gcloud run deploy ${{ secrets.CLOUD_RUN_SERVICE }} \
            --image "$IMAGE" \
            --region ${{ secrets.GCP_REGION }} \
            --platform managed \
            --allow-unauthenticated
```

That workflow does everything: authenticate, build, push, and deploy the new revision. You can expand later with tests or staging, but this is enough for a hobby app.

## 4. First Deployment
Run locally once to ensure the service exists:
```bash
gcloud run deploy $CLOUD_RUN_SERVICE \
  --image gcr.io/cloudrun/hello \
  --region $GCP_REGION \
  --platform managed \
  --allow-unauthenticated
```
This creates the service and lets the workflow update it later.

## 5. Day-to-Day Workflow
1. Push code to a feature branch, test locally.
2. Merge to `main` when ready.
3. GitHub Actions runs automatically and redeploys Cloud Run with the new image.
4. Check the workflow logs or the Cloud Run revision history if something goes wrong.

## 6. Optional Nice-to-Haves
- Add a quick `pytest` or `npm test` job before the build step.
- Use GitHub environments for manual approvals if you want extra safety.
- Rotate the service-account key annually and update the GitHub secret.

That’s it—minimal moving parts, automated deploys, and easy to maintain.
