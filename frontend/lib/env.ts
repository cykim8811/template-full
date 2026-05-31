function requireServerEnv(name: string): string {
  const value = process.env[name];
  if (!value) throw new Error(`Missing required environment variable: ${name}`);
  return value;
}

// Lazy getters so Next.js's build-time page collection doesn't throw before
// the platform has had a chance to inject the env vars. Each value is still
// required at request time.
export const serverEnv = {
  get BACKEND_URL() {
    return requireServerEnv("BACKEND_URL");
  },
};
