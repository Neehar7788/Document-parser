/**
 * Application Configuration
 */

export const config = {
  // API Configuration
  API_BASE_URL: 'http://localhost:8000',
  
  // Polling Configuration
  // Interval in milliseconds to check for new files/updates
  // Default: 30000ms (30 seconds)
  // Set to 0 to disable auto-polling
  STATS_POLL_INTERVAL: 30000,
  
  // Chat Configuration
  DEFAULT_TOP_K: 5,
  DEFAULT_SIMILARITY_THRESHOLD: 0.3,
};

export default config;
