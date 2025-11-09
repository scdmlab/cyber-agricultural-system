/**
 * Cloudflare Worker - NASS API Proxy
 *
 * This worker proxies requests to the USDA NASS QuickStats API
 * and adds CORS headers to allow browser-based requests.
 */

const NASS_API_ENDPOINT = 'https://quickstats.nass.usda.gov/api/api_GET';

export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    // Handle CORS preflight requests
    if (request.method === 'OPTIONS') {
      return handleOptions();
    }

    // Root endpoint - API documentation
    if (url.pathname === '/' || url.pathname === '') {
      return new Response(JSON.stringify({
        name: 'NASS API Proxy Service',
        version: '1.0.0',
        description: 'A Cloudflare Worker proxy for the NASS (National Agricultural Statistics Service) API',
        endpoints: {
          '/api/nass': {
            method: 'GET',
            description: 'Proxy endpoint for NASS API requests',
            parameters: {
              commodity_desc: 'Commodity description (e.g., CORN)',
              year: 'Year of data (e.g., 2023)',
              agg_level_desc: 'Aggregation level (e.g., COUNTY)',
              statisticcat_desc: 'Statistic category (e.g., YIELD)',
              source_desc: 'Source description (e.g., SURVEY)',
              sector_desc: 'Sector description (e.g., CROPS)',
              group_desc: 'Group description (e.g., FIELD CROPS)',
              short_desc: 'Short description filter'
            }
          }
        }
      }, null, 2), {
        status: 200,
        headers: {
          'Content-Type': 'application/json',
          ...getCorsHeaders()
        }
      });
    }

    // NASS API proxy endpoint
    if (url.pathname === '/api/nass') {
      return handleNassRequest(request, env);
    }

    // 404 for unknown routes
    return new Response(JSON.stringify({
      error: 'Not Found',
      message: 'The requested endpoint does not exist'
    }), {
      status: 404,
      headers: {
        'Content-Type': 'application/json',
        ...getCorsHeaders()
      }
    });
  }
};

/**
 * Handle requests to the NASS API proxy endpoint
 */
async function handleNassRequest(request, env) {
  try {
    const url = new URL(request.url);

    // Get all query parameters from the incoming request
    const queryParams = new URLSearchParams(url.searchParams);

    // Add the API key from environment variables
    // The API key should be set in Cloudflare Worker settings
    if (!env.NASS_API_KEY) {
      return new Response(JSON.stringify({
        error: 'Server configuration error',
        message: 'NASS API key is not configured'
      }), {
        status: 500,
        headers: {
          'Content-Type': 'application/json',
          ...getCorsHeaders()
        }
      });
    }

    queryParams.set('key', env.NASS_API_KEY);

    // Construct the target URL
    const targetUrl = `${NASS_API_ENDPOINT}?${queryParams.toString()}`;

    // Make request to NASS API
    const nassResponse = await fetch(targetUrl, {
      method: 'GET',
      headers: {
        'User-Agent': 'NASS-API-Proxy-CloudflareWorker/1.0',
        'Accept': 'application/json'
      }
    });

    // Get the response data
    const data = await nassResponse.json();

    // Return the response with CORS headers
    return new Response(JSON.stringify(data), {
      status: nassResponse.status,
      headers: {
        'Content-Type': 'application/json',
        ...getCorsHeaders()
      }
    });

  } catch (error) {
    // Handle errors
    console.error('Error proxying NASS API request:', error);

    return new Response(JSON.stringify({
      error: 'Failed to fetch data from NASS API',
      details: error.message
    }), {
      status: 502,
      headers: {
        'Content-Type': 'application/json',
        ...getCorsHeaders()
      }
    });
  }
}

/**
 * Handle CORS preflight requests
 */
function handleOptions() {
  return new Response(null, {
    status: 204,
    headers: {
      ...getCorsHeaders(),
      'Access-Control-Max-Age': '86400', // 24 hours
    }
  });
}

/**
 * Get CORS headers
 */
function getCorsHeaders() {
  return {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type',
  };
}
