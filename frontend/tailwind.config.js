/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'fanshawe-dark': '#161917',
        'fanshawe-red': '#b9030f',
        'fanshawe-red-dark': '#9e0004',
        'fanshawe-red-darker': '#70160e',
        'fanshawe-cream': '#e1e3db',
      }
    },
  },
  plugins: [],
}
