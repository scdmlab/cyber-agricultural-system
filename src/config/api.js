/**
 * API Configuration
 *
 * Update the NASS_PROXY_URL after deploying your Cloudflare Worker
 */

// OPTION 1: Current Replit proxy (will sleep after inactivity)
// const NASS_PROXY_URL = 'https://nass-crop-proxy.replit.app/api/nass'

// OPTION 2: Your Cloudflare Worker (recommended - more reliable)
// Replace <your-subdomain> with your actual Cloudflare Workers subdomain
// Example: https://nass-api-proxy.myusername.workers.dev/api/nass
const NASS_PROXY_URL = 'https://nass-api-proxy.fangdxc.workers.dev/api/nass'
// const NASS_PROXY_URL = 'https://nass-api-proxy.<your-subdomain>.workers.dev/api/nass'

export { NASS_PROXY_URL }
