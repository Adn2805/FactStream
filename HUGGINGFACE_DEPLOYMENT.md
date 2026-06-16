# 🚀 Deploying FactStream to HuggingFace Spaces

Because FactStream is a robust 5-container Microservice Architecture, we have compressed it into a single monolithic container using a specialized `Dockerfile.hf` to allow it to run on HuggingFace's free tier.

## Step-by-Step Deployment Guide

1. **Create an Account:**
   Go to [HuggingFace.co](https://huggingface.co/) and create a free account.

2. **Create a New Space:**
   - Click on your profile picture in the top right and select **New Space**.
   - **Space Name:** `FactStream` (or whatever you prefer).
   - **License:** `MIT` (or your choice).
   - **Select the Space SDK:** Click **Docker**.
   - **Choose a Docker Template:** Select **Blank**.
   - **Space Hardware:** Select the free **CPU basic (16GB RAM, 2 vCPU)**.
   - Click **Create Space**.

3. **Upload Your Files:**
   Once the space is created, you need to upload your project files. You can do this in two ways:

   **Method A: Using Git (Recommended)**
   ```bash
   git remote add huggingface https://huggingface.co/spaces/YOUR_USERNAME/FactStream
   git push huggingface main
   ```

   **Method B: Manual Upload**
   - Click the **Files and versions** tab in your HuggingFace Space.
   - Click **Add file** -> **Upload files**.
   - Upload all the files from your local folder.

4. **The Most Important Step (Dockerfile config):**
   HuggingFace looks for a file named exactly `Dockerfile`. Because we named our file `Dockerfile.hf` (to prevent confusing your local Docker-Compose setup), you must rename it in HuggingFace.
   - Go to the **Files** tab in HuggingFace.
   - Find `Dockerfile.hf` and rename it to `Dockerfile`.
   
5. **Wait for the Build:**
   HuggingFace will automatically start building your Docker container. It will download all the Whisper models, HuggingFace NLU models, and install all Python libraries. **This can take up to 10-15 minutes.**
   
   *Note: Because 5 AI microservices are running on a 2-vCPU free server, the initial boot and analysis might be slower than your local laptop. This is the trade-off for 100% free hosting!*

You can view the logs in the "Logs" tab to see all 5 uvicorn servers and the Streamlit frontend booting up. Once it says "Running", your app is live to the world!
