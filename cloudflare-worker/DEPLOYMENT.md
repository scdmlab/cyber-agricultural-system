# Cloudflare Worker Deployment Guide

## Step 1: Create a Cloudflare Account

1. Go to [https://dash.cloudflare.com/sign-up](https://dash.cloudflare.com/sign-up)
2. Sign up for a free account (no credit card required)

## Step 2: Create a New Worker

### Option A: Using Cloudflare Dashboard (Easiest)

1. Log in to [Cloudflare Dashboard](https://dash.cloudflare.com/)
2. Click **Workers & Pages** in the left sidebar
3. Click **Create Application**
4. Click **Create Worker**
5. Give it a name like `nass-api-proxy`
6. Click **Deploy**
7. After deployment, click **Edit Code**
8. Delete all the default code
9. Copy and paste the entire contents of `nass-proxy-worker.js`
10. Click **Save and Deploy**

### Option B: Using Wrangler CLI (Advanced)

```bash
# Install Wrangler CLI globally
npm install -g wrangler

# Login to Cloudflare
wrangler login

# Create a new worker project
wrangler init nass-api-proxy

# Copy the worker code
# (Copy nass-proxy-worker.js content to src/index.js in the created folder)

# Deploy
wrangler deploy
```

## Step 3: Configure Environment Variables (API Key)

**IMPORTANT:** You need to add your NASS API key as a secret environment variable.

### Using Dashboard:

1. In your Worker page, click **Settings**
2. Click **Variables and Secrets**
3. Under "Environment Variables", click **Add variable**
4. Add:
   - **Variable name**: `NASS_API_KEY`
   - **Value**: Your NASS API key (from https://quickstats.nass.usda.gov/api)
   - Check **Encrypt** to make it a secret
5. Click **Save and deploy**

### Using Wrangler CLI:

```bash
wrangler secret put NASS_API_KEY
# Enter your NASS API key when prompted
```

## Step 4: Get Your Worker URL

After deployment, your worker will be available at:
```
https://nass-api-proxy.<your-subdomain>.workers.dev
```

Example:
```
https://nass-api-proxy.myusername.workers.dev
```

You can find your exact URL:
- In the dashboard after deployment
- Or by running `wrangler deploy` (it will show the URL)

## Step 5: Test Your Worker

### Test the root endpoint:
```bash
curl https://nass-api-proxy.<your-subdomain>.workers.dev/
```

Should return API documentation JSON.

### Test the NASS proxy endpoint:
```bash
curl "https://nass-api-proxy.<your-subdomain>.workers.dev/api/nass?commodity_desc=CORN&year=2023&agg_level_desc=COUNTY&statisticcat_desc=YIELD&source_desc=SURVEY&sector_desc=CROPS&group_desc=FIELD+CROPS"
```

Should return NASS data JSON.

## Step 6: Update Your Vue.js App

Update `src/components/NassDataPanel.vue`:

```javascript
const buildApiUrl = () => {
  // Replace with your Cloudflare Worker URL
  const baseUrl = 'https://nass-api-proxy.<your-subdomain>.workers.dev/api/nass'

  const params = new URLSearchParams({
    commodity_desc: selectedCrop.value,
    year: selectedYear.value,
    agg_level_desc: 'COUNTY',
    statisticcat_desc: statisticCategory.value,
    source_desc: 'SURVEY',
    sector_desc: 'CROPS',
    group_desc: 'FIELD CROPS',
    short_desc: selectedCrop.value === 'CORN'
      ? 'CORN, GRAIN - YIELD, MEASURED IN BU / ACRE'
      : 'SOYBEANS - YIELD, MEASURED IN BU / ACRE'
  })

  return `${baseUrl}?${params.toString()}`
}
```

## Monitoring and Limits

### Free Tier Limits:
- **100,000 requests per day**
- **10ms CPU time per request**
- More than enough for most applications!

### Monitor Usage:
1. Go to your Worker in the dashboard
2. Click **Metrics** to see request counts and performance

## Troubleshooting

### "Error 1101: Worker threw exception"
- Check that your NASS_API_KEY environment variable is set correctly
- Check the worker logs in the dashboard

### CORS errors still appearing
- Make sure you deployed the latest code
- Clear your browser cache
- Check browser console for the exact error

### API key not working
- Get a new API key from https://quickstats.nass.usda.gov/api
- Make sure it's set as an encrypted secret in Cloudflare

## Advantages Over Replit

✅ **More reliable** - No sleeping, 99.99% uptime
✅ **Faster** - Edge network, lower latency
✅ **More scalable** - 100k requests/day free tier
✅ **Better for production** - Professional infrastructure
✅ **Easier maintenance** - Single file, simple updates

## Need Help?

- Cloudflare Workers Docs: https://developers.cloudflare.com/workers/
- Wrangler CLI Docs: https://developers.cloudflare.com/workers/wrangler/
